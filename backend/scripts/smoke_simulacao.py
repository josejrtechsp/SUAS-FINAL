#!/usr/bin/env python3
"""Smoke test da simulação.

- Faz login com amostras de perfis e chama endpoints críticos
- Gera relatório em backend/storage/sim/reports/

Uso:
  python scripts/smoke_simulacao.py --api http://127.0.0.1:8001
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from glob import glob
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _http_json(method: str, url: str, headers: Dict[str, str] | None = None, data: Any | None = None, timeout: int = 20) -> Tuple[int, Any]:
    h = headers or {}
    body = None
    if data is not None:
        if isinstance(data, (dict, list)):
            body = json.dumps(data).encode("utf-8")
            h.setdefault("Content-Type", "application/json")
        elif isinstance(data, bytes):
            body = data
        elif isinstance(data, str):
            body = data.encode("utf-8")
        else:
            body = str(data).encode("utf-8")

    req = Request(url, method=method, data=body, headers=h)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            ct = resp.headers.get("Content-Type", "")
            if "application/json" in ct:
                return resp.status, json.loads(raw.decode("utf-8"))
            # tenta json mesmo assim
            try:
                return resp.status, json.loads(raw.decode("utf-8"))
            except Exception:
                return resp.status, raw.decode("utf-8", errors="ignore")
    except Exception as e:
        # tenta capturar http error com body
        if hasattr(e, "code"):
            status = int(getattr(e, "code"))
            try:
                raw = e.read()
                try:
                    return status, json.loads(raw.decode("utf-8"))
                except Exception:
                    return status, raw.decode("utf-8", errors="ignore")
            except Exception:
                return status, str(e)
        return 0, str(e)


def login(api: str, email: str, senha: str) -> Tuple[Optional[str], int, Any]:
    url = f"{api}/auth/login"
    form = urlencode({"username": email, "password": senha}).encode("utf-8")
    status, data = _http_json("POST", url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=form)
    if status == 200 and isinstance(data, dict) and data.get("access_token"):
        return str(data["access_token"]), status, data
    return None, status, data


@dataclass
class Check:
    name: str
    method: str
    path: str
    expect: str  # "200", "403", "404", "any"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:8001")
    ap.add_argument("--cred", default="")
    ap.add_argument("--sample", type=int, default=2, help="quantos usuários por perfil testar")
    args = ap.parse_args()

    api = args.api.rstrip("/")

    # acha credenciais mais recentes
    cred_path = args.cred
    if not cred_path:
        candidates = sorted(glob(os.path.join(os.path.dirname(__file__), "..", "storage", "sim", "muni1_*_users.json")))
        cred_path = candidates[-1] if candidates else ""

    if not cred_path or not os.path.exists(cred_path):
        print("ERRO: arquivo de credenciais não encontrado. Rode primeiro scripts/simular_300_muni1.sh")
        sys.exit(2)

    with open(cred_path, "r", encoding="utf-8") as f:
        cred = json.load(f)

    senha = cred.get("senha", "demo123")
    usuarios = cred.get("usuarios", [])

    # agrupa por perfil
    by_perfil: Dict[str, List[Dict[str, Any]]] = {}
    for u in usuarios:
        by_perfil.setdefault(u.get("perfil", ""), []).append(u)

    # checks
    checks: List[Check] = [
        Check("CRAS listar casos", "GET", "/cras/casos", "200"),
        Check("CREAS listar casos", "GET", "/creas/casos", "200"),
        Check("PopRua listar pessoas", "GET", "/pessoas", "200"),
        Check("PopRua listar casos", "GET", "/casos", "200"),
        # Gestão (deve ser 200 só para coord_municipal/secretario/gestor/admin)
        Check("Gestão resumo", "GET", "/gestao/dashboard/resumo", "role_gestao"),
        Check("Gestão SLA modulo", "GET", "/gestao/dashboard/sla?group_by=modulo", "role_gestao"),
        Check("Gestão fila", "GET", "/gestao/fila?somente_atrasos=1&limit=5", "role_gestao"),
        # IA
        Check("IA health", "GET", "/ia/health", "200"),
        # VÁCUOS esperados (Gestão SUAS)
        Check("GAP financeiro", "GET", "/gestao/financeiro", "404"),
        Check("GAP benefícios eventuais", "GET", "/gestao/beneficios-eventuais", "404"),
        Check("GAP bolsa família", "GET", "/gestao/bolsa-familia", "404"),
    ]

    # perfis que DEVEM acessar gestão
    allow_gestao = {"coord_municipal", "secretario", "gestor", "admin", "gestor_consorcio"}

    results: List[Dict[str, Any]] = []

    def run_checks(perfil: str, email: str) -> None:
        tok, st, data = login(api, email, senha)
        if not tok:
            results.append({"perfil": perfil, "email": email, "check": "login", "ok": False, "status": st, "detail": data})
            return
        headers = {"Authorization": f"Bearer {tok}"}
        # rodar checks
        for c in checks:
            url = api + c.path
            status, resp = _http_json(c.method, url, headers=headers)

            expected = c.expect
            if expected == "role_gestao":
                expected = "200" if perfil in allow_gestao else "403"

            ok = False
            if expected == "any":
                ok = status > 0
            elif expected == "200":
                ok = status == 200
            elif expected == "403":
                ok = status == 403
            elif expected == "404":
                ok = status == 404

            results.append({
                "perfil": perfil,
                "email": email,
                "check": c.name,
                "path": c.path,
                "expected": expected,
                "status": status,
                "ok": ok,
                "resp": resp if (not ok) else None,
            })

    # executa amostras
    for perfil, lst in sorted(by_perfil.items()):
        if not perfil:
            continue
        sample_n = min(args.sample, len(lst))
        for i in range(sample_n):
            run_checks(perfil, lst[i]["email"])

    # sumariza
    total = len(results)
    fails = [r for r in results if not r.get("ok")]
    fails_500 = [r for r in fails if int(r.get("status") or 0) >= 500]
    gaps_404 = [r for r in results if r.get("expected") == "404" and int(r.get("status") or 0) == 404]

    # grava report
    run_id = cred.get("run_id") or datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.path.dirname(__file__), "..", "storage", "sim", "reports")
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, f"muni1_{run_id}_smoke.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"meta": {"cred": cred_path, "api": api, "total": total, "fails": len(fails)}, "results": results}, f, ensure_ascii=False, indent=2)

    md_path = os.path.join(out_dir, f"muni1_{run_id}_smoke.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Smoke test — Simulação (Município 1)\n\n")
        f.write(f"- API: `{api}`\n")
        f.write(f"- Credenciais: `{cred_path}`\n")
        f.write(f"- Total checks: **{total}**\n")
        f.write(f"- Falhas: **{len(fails)}**\n\n")

        if fails_500:
            f.write("## 🔥 Falhas 5xx (bug)\n\n")
            for r in fails_500[:50]:
                f.write(f"- **{r['perfil']}** {r['email']} → {r['check']} `{r['path']}` → **{r['status']}**\n")
            f.write("\n")

        other_fails = [r for r in fails if r not in fails_500]
        if other_fails:
            f.write("## ⚠️ Falhas (divergência de permissão/validação)\n\n")
            for r in other_fails[:80]:
                f.write(f"- **{r['perfil']}** {r['email']} → {r['check']} `{r['path']}` esperado **{r['expected']}** → veio **{r['status']}**\n")
            f.write("\n")

        f.write("## 🕳️ Vácuos (Gestão SUAS)\n\n")
        f.write("Endpoints que retornaram 404 (ainda não implementados):\n\n")
        for r in gaps_404:
            f.write(f"- {r['check']} `{r['path']}`\n")
        f.write("\n")
        f.write("Sugestão de módulos para completar na Gestão:\n")
        f.write("- Financeiro (empenho/liquidação/pagamento + execução orçamentária)\n")
        f.write("- Benefícios eventuais (solicitação, autorização, pagamento, prestação de contas)\n")
        f.write("- Bolsa Família / CadÚnico (IGD, condicionalidades, acompanhamento, fila de pendências)\n")
        f.write("\n")

        f.write("---\n")
        f.write(f"Arquivos gerados:\n- `{json_path}`\n- `{md_path}`\n")

    print("OK")
    print("JSON:", json_path)
    print("MD:", md_path)
    print("Falhas:", len(fails), "(5xx:", len(fails_500), ")")


if __name__ == "__main__":
    main()
