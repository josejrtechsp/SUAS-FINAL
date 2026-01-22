#!/usr/bin/env python3
"""Smoke test de ponta-a-ponta do módulo PopRua (pré-comissão) + PERF.

- Não depende do servidor rodando.
- Usa um DB isolado (sqlite) para não sujar o poprua.db.
- Cria municípios e usuários de teste (idempotente).
- Mede latências das rotas principais e gera um relatório "Top lentas".

Como rodar (na raiz do projeto):
  ~/POPNEWS1/backend/.venv/bin/python backend/scripts/smoke_comissao.py

Saída:
- imprime um resumo PASS/FAIL + TOP lentas
- salva um relatório JSON em backend/storage/smoke/smoke_comissao_report.json

Obs:
- Rotas opcionais (de patches) inexistentes viram SKIP.
- As metas de latência são "guardrails" (WARN) e não derrubam o smoke.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------
# Config / paths
# ---------------------------
THIS = Path(__file__).resolve()
BACKEND_DIR = THIS.parents[1]  # backend/
ROOT_DIR = THIS.parents[3] if len(THIS.parents) >= 4 else THIS.parents[2]

# Garante que o pacote "app" (backend/app) seja importável mesmo rodando este script fora da pasta backend
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

SMOKE_DIR = BACKEND_DIR / "storage" / "smoke"
SMOKE_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = SMOKE_DIR / "smoke_comissao_report.json"
DB_PATH = SMOKE_DIR / "smoke_comissao.db"

# Usa DB isolado (absoluto) para não sujar poprua.db
os.environ.setdefault("POPRUA_DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

# Evita seed automático do app (se existir) poluir o teste
os.environ.setdefault("GESTAO_AUTOMACOES_SEED", "false")


# Parâmetros de stress (dataset)
STRESS_MUNICIPIOS = int(os.getenv("SMOKE_STRESS_MUNICIPIOS", "2"))
STRESS_DISTRIB = os.getenv("SMOKE_STRESS_DISTRIB", "spread").strip().lower()  # spread|mun1|skew
STRESS_INTER_MODE = os.getenv("SMOKE_STRESS_INTERMUN_MODE", "mun1to2").strip().lower()  # mun1to2|ring


# ---------------------------
# Perf budgets (guardrails)
# ---------------------------
# Valores em ms. Ajuste conforme seu hardware. Em DEV (TestClient) normalmente fica bem abaixo.
BUDGETS_MS: Dict[str, int] = {
    "POST /auth/login": 800,
    "POST /pessoas/": 1200,
    "POST /casos/": 1500,
    "GET /casos/": 1200,
    "GET /casos/{id}": 1200,
    "POST /encaminhamentos/": 1500,
    "GET /encaminhamentos/": 1200,
    "POST /encaminhamentos/{id}/status": 1200,
    "POST /encaminhamentos/{id}/passagem": 1500,
    "GET /encaminhamentos/{id}": 1200,
    "GET /gestao/dashboard/resumo": 1500,
    "GET /gestao/fila": 2000,
    "POST /documentos/gerar": 4000,
    "GET /encaminhamentos/intermunicipal/inbox": 1200,
    "GET /encaminhamentos/intermunicipal/{id}/dossie": 1500,
}

TOP_N_SLOW = 10
REPEAT_P95 = int(os.getenv("SMOKE_P95_REPEAT", "5"))  # repetições para medir p95 (rotas críticas)


# ---------------------------
# Helpers
# ---------------------------
@dataclass
class StepResult:
    name: str
    ok: bool
    detail: str
    data: Optional[Dict[str, Any]] = None
    skipped: bool = False
    ms: Optional[float] = None


@dataclass
class PerfSample:
    key: str  # ex: "GET /gestao/fila"
    method: str
    path: str
    status_code: int
    ms: float
    budget_ms: Optional[int] = None


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _safe_json(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


def _has_route(app, path: str, method: str) -> bool:
    m = method.upper()
    for r in getattr(app, "routes", []):
        try:
            methods = getattr(r, "methods", None) or set()
            if m in methods and getattr(r, "path", None) == path:
                return True
        except Exception:
            continue
    return False


def _auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _p95(values: List[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = max(0, min(len(s) - 1, int(math.ceil(0.95 * len(s))) - 1))
    return float(s[idx])


def main() -> int:
    results: List[StepResult] = []
    perf: List[PerfSample] = []

    # 1) Importa app
    try:
        from fastapi.testclient import TestClient
        from sqlmodel import Session, select

        from app.core.db import engine, init_db
        from app.core.security import hash_senha
        from app.models.municipio import Municipio
        from app.models.usuario import Usuario

        # Importa app só depois do env de DB
        from app.main import app

    except Exception as e:
        results.append(
            StepResult(
                name="Importar app.main",
                ok=False,
                detail=f"Falha ao importar backend: {e}",
            )
        )
        _write_report(results, perf)
        _print_summary(results, perf)
        return 1

    client = TestClient(app)

    def req(method: str, url: str, *, key: Optional[str] = None, **kwargs):
        """Wrapper HTTP para medir latência e coletar top lentas."""
        m = method.upper()
        path = url.split("?")[0]
        k = key or f"{m} {path}"
        budget = BUDGETS_MS.get(k)
        t0 = time.perf_counter()
        resp = client.request(m, url, **kwargs)
        ms = (time.perf_counter() - t0) * 1000.0
        perf.append(PerfSample(key=k, method=m, path=path, status_code=resp.status_code, ms=ms, budget_ms=budget))
        return resp

    # 2) Inicializa DB (create_all)
    try:
        t0 = time.perf_counter()
        if DB_PATH.exists():
            DB_PATH.unlink()
        init_db()
        results.append(StepResult("Init DB (create_all)", True, "OK", ms=(time.perf_counter() - t0) * 1000.0))
    except Exception as e:
        results.append(StepResult("Init DB (create_all)", False, f"Falha no init_db(): {e}"))
        _write_report(results, perf)
        _print_summary(results, perf)
        return 1

    # 3) Seed mínimo: 2 municípios + usuários (operador A/B, coord, consórcio)
    try:
        t0 = time.perf_counter()
        with Session(engine) as s:
            # Municípios
            m = max(2, int(STRESS_MUNICIPIOS))
            for mid in range(1, m + 1):
                mun = s.exec(select(Municipio).where(Municipio.id == mid)).first()
                if not mun:
                    nm = ("Município A" if mid == 1 else ("Município B" if mid == 2 else f"Município {mid}"))
                    mun = Municipio(id=mid, nome=f"{nm} (SMOKE)", uf="SP", ativo=True)
                    s.add(mun)

            def upsert_user(email: str, nome: str, perfil: str, municipio_id: Optional[int], senha: str) -> None:
                email = (email or "").strip().lower()
                u = s.exec(select(Usuario).where(Usuario.email == email)).first()
                if not u:
                    u = Usuario(
                        nome=nome,
                        email=email,
                        perfil=perfil,
                        municipio_id=municipio_id,
                        senha_hash=hash_senha(senha),
                        ativo=True,
                    )
                    s.add(u)
                else:
                    u.nome = nome
                    u.perfil = perfil
                    u.municipio_id = municipio_id
                    u.senha_hash = hash_senha(senha)
                    u.ativo = True
                    s.add(u)

            upsert_user("smoke.opa@local", "Operador A (SMOKE)", "operador", 1, "smoke123")
            upsert_user("smoke.opb@local", "Operador B (SMOKE)", "operador", 2, "smoke123")
            upsert_user("smoke.coord@local", "Coordenação (SMOKE)", "coord_municipal", 1, "smoke123")
            upsert_user("smoke.consorcio@local", "Consórcio (SMOKE)", "gestor_consorcio", None, "smoke123")

            s.commit()

        results.append(
            StepResult(
                "Seed municípios + usuários",
                True,
                f"Criados/atualizados: Municipios(1..{max(2,int(STRESS_MUNICIPIOS))}) e usuários smoke.* (senha: smoke123)",
                ms=(time.perf_counter() - t0) * 1000.0,
            )
        )
    except Exception as e:
        results.append(StepResult("Seed municípios + usuários", False, f"Falha ao seed: {e}"))
        _write_report(results, perf)
        _print_summary(results, perf)
        return 1

    # Helpers HTTP
    def login(email: str, senha: str) -> Tuple[Optional[str], str]:
        email = (email or "").strip().lower()
        # medimos o login (POST /auth/login)
        r = req(
            "POST",
            "/auth/login",
            key="POST /auth/login",
            data={"username": email, "password": senha},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}: {r.text}"
        try:
            return r.json().get("access_token"), "OK"
        except Exception:
            return None, f"Resposta inválida: {r.text}"

    def must(resp, name: str) -> Dict[str, Any]:
        if resp.status_code >= 400:
            raise RuntimeError(f"{name}: HTTP {resp.status_code} {resp.text}")
        try:
            return resp.json()
        except Exception:
            return {"raw": resp.text}

    # 4) Login (4 perfis)
    t0 = time.perf_counter()
    tokA, msgA = login("smoke.opa@local", "smoke123")
    tokB, msgB = login("smoke.opb@local", "smoke123")
    tokCoord, msgC = login("smoke.coord@local", "smoke123")
    tokCons, msgCons = login("smoke.consorcio@local", "smoke123")

    if not tokA or not tokB or not tokCoord or not tokCons:
        results.append(
            StepResult(
                "Login (4 perfis)",
                False,
                f"opA={msgA} | opB={msgB} | coord={msgC} | consorcio={msgCons}",
                ms=(time.perf_counter() - t0) * 1000.0,
            )
        )
        _write_report(results, perf)
        _print_summary(results, perf)
        return 1
    results.append(StepResult("Login (4 perfis)", True, "OK", ms=(time.perf_counter() - t0) * 1000.0))

    # 4.5) (Opcional) Seed STRESS (volume) para medir performance com dados realistas
    if (os.getenv("SMOKE_STRESS", "").strip().lower() in ("1", "true", "yes")):
        try:
            t0s = time.perf_counter()
            n_casos = int(os.getenv("SMOKE_STRESS_CASOS", "2000"))
            n_inter = int(os.getenv("SMOKE_STRESS_INTERMUN", "300"))
            # Importa models diretamente (mais rápido do que chamar endpoints em loop)
            from app.models.pessoa import PessoaRua
            from app.models.caso_pop_rua import CasoPopRua
            from app.models.encaminhamentos import EncaminhamentoIntermunicipal, EncaminhamentoEvento

            # Gera pessoas + casos (metade Mun A, metade Mun B)
            with Session(engine) as s:
                # acha o último id (se existir)
                last_pessoa = s.exec(select(PessoaRua.id).order_by(PessoaRua.id.desc())).first() or 0
                last_caso = s.exec(select(CasoPopRua.id).order_by(CasoPopRua.id.desc())).first() or 0
                base_pid = int(last_pessoa) + 1
                base_cid = int(last_caso) + 1

                pessoas = []
                casos = []
                for i in range(n_casos):
                    # distribui municípios conforme configuração
                    if STRESS_DISTRIB == "mun1":
                        mun = 1
                    elif STRESS_DISTRIB == "skew":
                        mun = 1 if (i % 10) < 7 else ((i % max(2, STRESS_MUNICIPIOS)) + 1)
                    else:  # spread
                        mun = (i % max(2, STRESS_MUNICIPIOS)) + 1
                    p = PessoaRua(
                        nome_civil=f"STRESS Pessoa {base_pid + i}",
                        municipio_origem_id=mun,
                    )
                    pessoas.append(p)

                s.add_all(pessoas)
                s.commit()

                # Recarrega ids (SQLite)
                # (pega os últimos n_casos ids)
                ids = list(
                    s.exec(select(PessoaRua.id).order_by(PessoaRua.id.desc()).limit(n_casos)).all()
                )
                ids = list(reversed([int(x) for x in ids if x is not None]))

                agora = datetime.now(timezone.utc)
                for i, pid in enumerate(ids):
                    # distribui municípios conforme configuração
                    if STRESS_DISTRIB == "mun1":
                        mun = 1
                    elif STRESS_DISTRIB == "skew":
                        mun = 1 if (i % 10) < 7 else ((i % max(2, STRESS_MUNICIPIOS)) + 1)
                    else:  # spread
                        mun = (i % max(2, STRESS_MUNICIPIOS)) + 1
                    # espalha atualizações para gerar "atraso" e diversidade
                    delta_days = (i % 21)
                    c = CasoPopRua(
                        pessoa_id=int(pid),
                        municipio_id=mun,
                        status="em_andamento",
                        etapa_atual="ABORDAGEM",
                        ativo=True,
                        data_abertura=agora - timedelta(days=delta_days + 5),
                        data_ultima_atualizacao=agora - timedelta(days=delta_days),
                        data_inicio_etapa_atual=agora - timedelta(days=delta_days),
                        prazo_etapa_dias=7,
                        estagnado=(i % 17 == 0),
                        motivo_estagnacao=("Sem contato" if (i % 17 == 0) else None),
                        data_prevista_proxima_acao=agora + timedelta(days=1),
                    )
                    casos.append(c)

                s.add_all(casos)
                s.commit()

                # Intermunicipais (Mun A -> Mun B)
                inters = []
                eventos = []
                for j in range(min(n_inter, len(ids))):
                    pid = int(ids[j])
                    enc = EncaminhamentoIntermunicipal(
                        pessoa_id=pid,
                        caso_id=None,
                        municipio_origem_id=(1 if STRESS_INTER_MODE == "mun1to2" else ((j % max(2, STRESS_MUNICIPIOS)) + 1)),
                        municipio_destino_id=(2 if STRESS_INTER_MODE == "mun1to2" else (((j % max(2, STRESS_MUNICIPIOS)) + 1) % max(2, STRESS_MUNICIPIOS)) + 1),
                        motivo="STRESS: teste de trânsito intermunicipal",
                        observacoes=None,
                        consentimento_registrado=(j % 3 == 0),
                        status=("solicitado" if j % 4 == 0 else ("aceito" if j % 4 == 1 else ("agendado" if j % 4 == 2 else "passagem"))),
                        criado_em=agora - timedelta(days=(j % 10)),
                        atualizado_em=agora - timedelta(days=(j % 6)),
                    )
                    inters.append(enc)

                s.add_all(inters)
                s.commit()

                # eventos mínimos
                enc_ids = list(s.exec(select(EncaminhamentoIntermunicipal.id).order_by(EncaminhamentoIntermunicipal.id.desc()).limit(len(inters))).all())
                enc_ids = list(reversed([int(x) for x in enc_ids if x is not None]))
                for k, eid in enumerate(enc_ids):
                    ev = EncaminhamentoEvento(
                        encaminhamento_id=int(eid),
                        tipo="solicitado",
                        detalhe="STRESS seed",
                        por_nome="SMOKE",
                        em=agora - timedelta(days=(k % 10)),
                    )
                    eventos.append(ev)
                s.add_all(eventos)
                s.commit()

            results.append(StepResult("Seed STRESS (volume)", True, f"OK casos={n_casos} inter={n_inter}", ms=(time.perf_counter() - t0s) * 1000.0))
        except Exception as e:
            results.append(StepResult("Seed STRESS (volume)", False, f"Falha: {e}"))

    # 5) Criar pessoa (Mun A)
    try:
        t0 = time.perf_counter()
        payload_pessoa = {
            "nome_social": f"Pessoa SMOKE {int(time.time())}",
            "genero": "N/I",
        }
        r = req("POST", "/pessoas/", key="POST /pessoas/", json=payload_pessoa, headers=_auth_headers(tokA))
        pessoa = must(r, "Criar pessoa")
        pessoa_id = int(pessoa.get("id"))
        results.append(StepResult("Criar pessoa (Mun A)", True, f"pessoa_id={pessoa_id}", {"pessoa": pessoa}, ms=(time.perf_counter() - t0) * 1000.0))
    except Exception as e:
        results.append(StepResult("Criar pessoa (Mun A)", False, str(e)))
        _write_report(results, perf)
        _print_summary(results, perf)
        return 1

    # 6) Criar caso PopRua (Mun A) + obter caso
    try:
        t0 = time.perf_counter()
        r = req(
            "POST",
            "/casos/",
            key="POST /casos/",
            json={"pessoa_id": pessoa_id, "observacoes_iniciais": "SMOKE - abertura"},
            headers=_auth_headers(tokA),
        )
        caso = must(r, "Criar caso")
        caso_id = int(caso.get("id"))

        r2 = req("GET", f"/casos/{caso_id}", key="GET /casos/{id}", headers=_auth_headers(tokA))
        _ = must(r2, "Obter caso")
        results.append(StepResult("Criar/obter caso PopRua (Mun A)", True, f"caso_id={caso_id}", {"caso": caso}, ms=(time.perf_counter() - t0) * 1000.0))
    except Exception as e:
        results.append(StepResult("Criar/obter caso PopRua (Mun A)", False, str(e)))
        _write_report(results, perf)
        _print_summary(results, perf)
        return 1

    # 7) Intermunicipal: criar + fluxo completo (A->B)
    enc_id: Optional[int] = None
    try:
        t0 = time.perf_counter()
        r = req(
            "POST",
            "/encaminhamentos/",
            key="POST /encaminhamentos/",
            json={
                "pessoa_id": pessoa_id,
                "caso_id": caso_id,
                "municipio_destino_id": 2,
                "motivo": "SMOKE - retorno intermunicipal",
                "observacoes": "SMOKE",
                "consentimento_registrado": True,
            },
            headers=_auth_headers(tokA),
        )
        enc = must(r, "Criar intermunicipal")
        enc_id = int(enc.get("id"))

        # destino lista e vê
        rL = req("GET", "/encaminhamentos/", key="GET /encaminhamentos/", headers=_auth_headers(tokB))
        lst = must(rL, "Listar intermunicipal (destino)")
        if not any(int(x.get("id")) == enc_id for x in (lst or [])):
            raise RuntimeError("Destino não enxergou o encaminhamento na listagem")

        # contato (origem)
        must(req("POST", f"/encaminhamentos/{enc_id}/status", key="POST /encaminhamentos/{id}/status", json={"status": "contato", "detalhe": "Contato realizado"}, headers=_auth_headers(tokA)), "Status contato")
        # aceito (destino)
        must(req("POST", f"/encaminhamentos/{enc_id}/status", key="POST /encaminhamentos/{id}/status", json={"status": "aceito", "detalhe": "Aceito"}, headers=_auth_headers(tokB)), "Status aceito")
        # agendado (destino)
        must(req("POST", f"/encaminhamentos/{enc_id}/status", key="POST /encaminhamentos/{id}/status", json={"status": "agendado", "detalhe": "Agendado"}, headers=_auth_headers(tokB)), "Status agendado")
        # passagem (origem)
        dt = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        must(
            req(
                "POST",
                f"/encaminhamentos/{enc_id}/passagem",
                key="POST /encaminhamentos/{id}/passagem",
                json={"passagem_numero": "SMK-001", "passagem_empresa": "Teste", "passagem_data_viagem": dt, "kit_lanche": True},
                headers=_auth_headers(tokA),
            ),
            "Registrar passagem",
        )
        # contrarreferencia (destino)
        must(req("POST", f"/encaminhamentos/{enc_id}/status", key="POST /encaminhamentos/{id}/status", json={"status": "contrarreferencia", "detalhe": "Atendido no destino"}, headers=_auth_headers(tokB)), "Status contrarreferencia")
        # concluido (origem)
        must(req("POST", f"/encaminhamentos/{enc_id}/status", key="POST /encaminhamentos/{id}/status", json={"status": "concluido", "detalhe": "Encerrado"}, headers=_auth_headers(tokA)), "Status concluido")

        # obter e validar status final
        out = must(req("GET", f"/encaminhamentos/{enc_id}", key="GET /encaminhamentos/{id}", headers=_auth_headers(tokA)), "Obter intermunicipal final")
        if str(out.get("status")) != "concluido":
            raise RuntimeError(f"Status final não é concluido: {out.get('status')}")

        results.append(StepResult("Intermunicipal ponta-a-ponta (A→B)", True, f"enc_id={enc_id}", {"enc": out}, ms=(time.perf_counter() - t0) * 1000.0))
    except Exception as e:
        results.append(StepResult("Intermunicipal ponta-a-ponta (A→B)", False, str(e), {"enc_id": enc_id} if enc_id else None))
        _write_report(results, perf)
        _print_summary(results, perf)
        return 1

    # 8) Gestão: dashboard + fila (coord) + medir p95 da fila (repeat)
    try:
        t0 = time.perf_counter()
        _ = must(req("GET", "/gestao/dashboard/resumo", key="GET /gestao/dashboard/resumo", headers=_auth_headers(tokCoord)), "Gestão dashboard")

        # mede p95 da fila (limit=10 e limit=50) e listas principais
        times_fila10: List[float] = []
        times_fila50: List[float] = []
        fila_last: Dict[str, Any] = {}

        for _i in range(REPEAT_P95):
            t1 = time.perf_counter()
            r2 = req("GET", "/gestao/fila?limit=10&offset=0", key="GET /gestao/fila", headers=_auth_headers(tokCoord))
            times_fila10.append((time.perf_counter() - t1) * 1000.0)
            fila_last = must(r2, "Gestão fila")

        for _i in range(REPEAT_P95):
            t1 = time.perf_counter()
            r2 = req("GET", "/gestao/fila?limit=50&offset=0", key="GET /gestao/fila", headers=_auth_headers(tokCoord))
            times_fila50.append((time.perf_counter() - t1) * 1000.0)
            fila_last = must(r2, "Gestão fila")

        p95_fila10 = _p95(times_fila10)
        p95_fila50 = _p95(times_fila50)

        # Lista de casos (se existir)
        p95_casos50: Optional[float] = None
        if _has_route(app, "/casos/", "GET"):
            times_casos: List[float] = []
            for _i in range(REPEAT_P95):
                t1 = time.perf_counter()
                rC = req("GET", "/casos/?limit=50&offset=0", key="GET /casos/", headers=_auth_headers(tokA))
                times_casos.append((time.perf_counter() - t1) * 1000.0)
                _ = must(rC, "Listar casos")
            p95_casos50 = _p95(times_casos)

        # Lista de encaminhamentos (se existir)
        p95_enc50: Optional[float] = None
        if _has_route(app, "/encaminhamentos/", "GET"):
            times_enc: List[float] = []
            for _i in range(REPEAT_P95):
                t1 = time.perf_counter()
                rE = req("GET", "/encaminhamentos/?limit=50&offset=0", key="GET /encaminhamentos/", headers=_auth_headers(tokA))
                times_enc.append((time.perf_counter() - t1) * 1000.0)
                _ = must(rE, "Listar encaminhamentos")
            p95_enc50 = _p95(times_enc)

        detail = f"items={len((fila_last or {}).get('items') or [])} | fila_p95_10={p95_fila10:.0f}ms | fila_p95_50={p95_fila50:.0f}ms"
        if p95_casos50 is not None:
            detail += f" | casos_p95_50={p95_casos50:.0f}ms"
        if p95_enc50 is not None:
            detail += f" | enc_p95_50={p95_enc50:.0f}ms"

        results.append(

            StepResult(
                "Gestão (dashboard + fila)",
                True,
                detail,
                ms=(time.perf_counter() - t0) * 1000.0,
            )
        )
    except Exception as e:
        results.append(StepResult("Gestão (dashboard + fila)", False, str(e)))
        _write_report(results, perf)
        _print_summary(results, perf)
        return 1

    # 9) Documentos: gerar ofício + relatório (coord)
    try:
        t0 = time.perf_counter()
        doc1 = must(
            req(
                "POST",
                "/documentos/gerar",
                key="POST /documentos/gerar",
                json={
                    "municipio_id": 1,
                    "tipo": "oficio",
                    "modelo": None,
                    "assunto": "SMOKE - Ofício",
                    "campos": {"texto": "Documento de teste (SMOKE)", "assinante_nome": "Coordenação", "assinante_cargo": "Coordenação"},
                    "emissor": "smas",
                    "salvar": True,
                    "retornar_pdf": False,
                },
                headers=_auth_headers(tokCoord),
            ),
            "Gerar ofício",
        )
        doc2 = must(
            req(
                "POST",
                "/documentos/gerar",
                key="POST /documentos/gerar",
                json={
                    "municipio_id": 1,
                    "tipo": "relatorio",
                    "modelo": None,
                    "assunto": "SMOKE - Relatório",
                    "campos": {"contexto": "SMOKE", "descricao": "Relatório de teste"},
                    "emissor": "smas",
                    "salvar": True,
                    "retornar_pdf": False,
                },
                headers=_auth_headers(tokCoord),
            ),
            "Gerar relatório",
        )
        results.append(StepResult("Documentos (ofício + relatório)", True, "OK", {"oficio": doc1, "relatorio": doc2}, ms=(time.perf_counter() - t0) * 1000.0))
    except Exception as e:
        results.append(StepResult("Documentos (ofício + relatório)", False, str(e)))
        _write_report(results, perf)
        _print_summary(results, perf)
        return 1

    # 10) Consórcio: consegue ver gestão (mínimo)
    try:
        t0 = time.perf_counter()
        _ = must(req("GET", "/gestao/dashboard/resumo?municipio_id=1", key="GET /gestao/dashboard/resumo", headers=_auth_headers(tokCons)), "Consórcio dashboard")
        _ = must(req("GET", "/gestao/fila?municipio_id=1&limit=5&offset=0", key="GET /gestao/fila", headers=_auth_headers(tokCons)), "Consórcio fila")
        results.append(StepResult("Consórcio (visão via gestao)", True, "OK", ms=(time.perf_counter() - t0) * 1000.0))
    except Exception as e:
        results.append(StepResult("Consórcio (visão via gestao)", False, str(e)))
        _write_report(results, perf)
        _print_summary(results, perf)
        return 1

    # 11) Rotas opcionais (se existirem): inbox/dossie/assumir/contrarreferencia estruturada
    try:
        optional_checks: List[Tuple[str, str, Callable[[], None]]] = []

        if _has_route(app, "/encaminhamentos/intermunicipal/inbox", "GET"):
            def _chk_inbox():
                must(req("GET", "/encaminhamentos/intermunicipal/inbox", key="GET /encaminhamentos/intermunicipal/inbox", headers=_auth_headers(tokB)), "Inbox intermunicipal")
            optional_checks.append(("Inbox intermunicipal", "GET /encaminhamentos/intermunicipal/inbox", _chk_inbox))

        if enc_id and _has_route(app, f"/encaminhamentos/intermunicipal/{enc_id}/dossie", "GET"):
            def _chk_dossie():
                must(req("GET", f"/encaminhamentos/intermunicipal/{enc_id}/dossie", key="GET /encaminhamentos/intermunicipal/{id}/dossie", headers=_auth_headers(tokA)), "Dossiê intermunicipal")
            optional_checks.append(("Dossiê intermunicipal", f"GET /encaminhamentos/intermunicipal/{enc_id}/dossie", _chk_dossie))

        if not optional_checks:
            results.append(StepResult("Rotas opcionais (inbox/dossiê/etc)", True, "Não detectadas na versão atual (OK)", skipped=True))
        else:
            for n, desc, fn in optional_checks:
                try:
                    t0 = time.perf_counter()
                    fn()
                    results.append(StepResult(f"Opcional: {n}", True, desc, ms=(time.perf_counter() - t0) * 1000.0))
                except Exception as e:
                    results.append(StepResult(f"Opcional: {n}", False, f"Falhou: {e}"))

    except Exception as e:
        results.append(StepResult("Rotas opcionais (inbox/dossiê/etc)", True, f"SKIP por erro não crítico: {e}", skipped=True))

    _write_report(results, perf)
    _print_summary(results, perf)

    hard_fail = any((not r.ok) and (not r.skipped) for r in results)
    return 1 if hard_fail else 0


def _perf_summary(perf: List[PerfSample]) -> Dict[str, Any]:
    by_key: Dict[str, List[PerfSample]] = {}
    for s in perf:
        by_key.setdefault(s.key, []).append(s)

    summary: Dict[str, Any] = {}
    for k, samples in by_key.items():
        times = [x.ms for x in samples]
        summary[k] = {
            "count": len(times),
            "avg_ms": round(sum(times) / len(times), 2),
            "max_ms": round(max(times), 2),
            "p95_ms": round(_p95(times), 2),
            "budget_ms": samples[0].budget_ms,
            "over_budget": (samples[0].budget_ms is not None) and (_p95(times) > float(samples[0].budget_ms)),
        }
    return summary


def _write_report(results: List[StepResult], perf: List[PerfSample]) -> None:
    perf_summary = _perf_summary(perf)
    top_slow = sorted(perf, key=lambda x: x.ms, reverse=True)[:TOP_N_SLOW]
    report = {
        "generated_at": _now(),
        "db": os.environ.get("POPRUA_DATABASE_URL"),
        "stress": {"enabled": os.getenv("SMOKE_STRESS"), "municipios": STRESS_MUNICIPIOS, "distrib": STRESS_DISTRIB, "inter_mode": STRESS_INTER_MODE},
        "results": [
            {"name": r.name, "ok": r.ok, "skipped": r.skipped, "detail": r.detail, "ms": r.ms, "data": r.data}
            for r in results
        ],
        "perf": {
            "budgets_ms": BUDGETS_MS,
            "summary": perf_summary,
            "top_slow": [
                {
                    "key": s.key,
                    "status": s.status_code,
                    "ms": round(s.ms, 2),
                    "budget_ms": s.budget_ms,
                }
                for s in top_slow
            ],
            "samples": [
                {
                    "key": s.key,
                    "method": s.method,
                    "path": s.path,
                    "status": s.status_code,
                    "ms": round(s.ms, 2),
                    "budget_ms": s.budget_ms,
                }
                for s in perf
            ],
        },
    }
    REPORT_PATH.write_text(_safe_json(report), encoding="utf-8")


def _print_summary(results: List[StepResult], perf: List[PerfSample]) -> None:
    ok = sum(1 for r in results if r.ok and not r.skipped)
    skip = sum(1 for r in results if r.skipped)
    fail = sum(1 for r in results if (not r.ok) and (not r.skipped))

    print("\n=== SMOKE COMISSAO (PopRua) ===")
    print(f"DB: {os.environ.get('POPRUA_DATABASE_URL')}")
    print(f"Report: {REPORT_PATH}")
    print(f"PASS={ok}  FAIL={fail}  SKIP={skip}")

    for r in results:
        tag = "PASS" if r.ok else ("SKIP" if r.skipped else "FAIL")
        ms = f" ({r.ms:.0f}ms)" if r.ms is not None else ""
        print(f"[{tag}] {r.name}{ms} :: {r.detail}")

    # Perf summary
    ps = _perf_summary(perf)
    over = [k for k, v in ps.items() if v.get("over_budget")]
    if over:
        print("\n--- PERF WARN (p95 acima do budget) ---")
        for k in over:
            v = ps[k]
            print(f"[WARN] {k}: p95={v['p95_ms']}ms budget={v['budget_ms']}ms (max={v['max_ms']}ms, n={v['count']})")

    top = sorted(perf, key=lambda x: x.ms, reverse=True)[:TOP_N_SLOW]
    print("\n--- TOP rotas mais lentas (amostras) ---")
    for s in top:
        b = f" budget={s.budget_ms}ms" if s.budget_ms is not None else ""
        print(f"{s.ms:7.0f}ms  {s.key}  status={s.status_code}{b}")


if __name__ == "__main__":
    sys.exit(main())
