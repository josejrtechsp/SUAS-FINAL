"""
Seed de SIMULAÇÃO (Município 1)

Cria:
- 300 usuários (100 CRAS, 100 CREAS, 100 PopRua) com perfis variados
- Casos complexos:
  * CRAS: 200 casos (PIA faltando, CadÚnico pendente, tarefas vencidas, validação pendente, estagnação)
  * CREAS: 200 casos (risco/prioridade variados, alguns estourados)
  * PopRua: 200 pessoas + 200 casos (alguns estourados/estagnados)
- Rede:
  * Encaminhamentos CRAS (com devolutiva faltando)
  * Encaminhamentos Intermunicipais (com etapas atrasadas)
- OSC:
  * 1 OSC + 1 parceria + prestações de contas em atraso

Uso recomendado (DB separado):
  cd backend
  source .venv/bin/activate
  POPRUA_DATABASE_URL="sqlite:///./poprua_sim.db" python -m app.seed_simulacao_muni1 --reset-db

Depois subir backend apontando pro sim.db:
  POPRUA_DATABASE_URL="sqlite:///./poprua_sim.db" uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

Observação:
- Este script evita imports do app.core.db no topo para respeitar POPRUA_DATABASE_URL.
"""

from __future__ import annotations

import argparse
import json
import os
import random
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# ⚠️ IMPORTANTE:
# Não importe app.core.db / models no topo.
# Precisamos setar POPRUA_DATABASE_URL antes para o engine pegar o DB correto.


MUNICIPIOS_BASE = [
    {"nome": "São Carlos", "uf": "SP"},
    {"nome": "Tabatinga", "uf": "SP"},
    {"nome": "Araraquara", "uf": "SP"},
    {"nome": "Ibaté", "uf": "SP"},
    {"nome": "Porto Ferreira", "uf": "SP"},
    {"nome": "Santa Rita do Passa Quatro", "uf": "SP"},
    {"nome": "Américo Brasiliense", "uf": "SP"},
]

CRAS_ETAPAS = ["TRIAGEM", "DIAGNOSTICO", "PIA", "EXECUCAO", "MONITORAMENTO"]
CRAS_SLA = {"TRIAGEM": 2, "DIAGNOSTICO": 15, "PIA": 15, "EXECUCAO": 30, "MONITORAMENTO": 30}

CREAS_ETAPAS = ["entrada", "triagem", "acolhimento", "diagnostico", "plano", "execucao"]
POPRUA_ETAPAS = ["ABORDAGEM", "TRIAGEM", "PIA", "ENCAMINHAMENTO", "ACOMPANHAMENTO"]


def _rand_digits(rng: random.Random, n: int) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(n))


def _mk_cpf(rng: random.Random) -> str:
    # Não valida dígito verificador (para simulação serve)
    return _rand_digits(rng, 11)


def _mk_nis(rng: random.Random) -> str:
    return _rand_digits(rng, 11)


def _dt_days_ago(rng: random.Random, max_days: int) -> datetime:
    return datetime.utcnow() - timedelta(days=rng.randint(0, max_days), hours=rng.randint(0, 23))


def _sla_start_for(rng: random.Random, sla_dias: int) -> Tuple[datetime, bool, bool]:
    """Retorna (data_inicio_etapa, em_risco, estourado)"""
    now = datetime.utcnow()
    p = rng.random()
    if p < 0.40:
        # estourado
        delta = sla_dias + rng.randint(1, 20)
        return now - timedelta(days=delta), False, True
    if p < 0.70:
        # em risco (>= 80% do SLA)
        delta = max(1, int(sla_dias * 0.85))
        return now - timedelta(days=delta), True, False
    # ok
    delta = rng.randint(0, max(0, sla_dias - 2))
    return now - timedelta(days=delta), False, False


def main() -> None:
    ap = argparse.ArgumentParser(description="Seed de simulação (Município 1)")
    ap.add_argument("--municipio-id", type=int, default=1)
    ap.add_argument("--users-per-module", type=int, default=100)
    ap.add_argument("--cases-cras", type=int, default=200)
    ap.add_argument("--cases-creas", type=int, default=200)
    ap.add_argument("--cases-poprua", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--senha", type=str, default="demo123")
    ap.add_argument("--reset-db", action="store_true", help="Se DB for sqlite file, apaga o arquivo antes de criar.")
    args = ap.parse_args()

    rng = random.Random(args.seed)

    # DB URL (se não vier de fora, usa poprua_sim.db)
    db_url = os.getenv("POPRUA_DATABASE_URL", "sqlite:///./poprua_sim.db")
    os.environ["POPRUA_DATABASE_URL"] = db_url

    # Reset DB (somente sqlite arquivo)
    if args.reset_db and db_url.startswith("sqlite:///./"):
        path = db_url.replace("sqlite:///./", "")
        if os.path.exists(path):
            print(f"[SIM] reset-db: removendo {path}")
            os.remove(path)

    # Importa aqui (depois de setar env)
    from sqlmodel import Session, select  # type: ignore

    from app.core.db import engine, init_db  # type: ignore
    from app.core.security import hash_senha  # type: ignore

    from app.models.municipio import Municipio  # type: ignore
    from app.models.usuario import Usuario  # type: ignore
    from app.models.cras_unidade import CrasUnidade  # type: ignore
    from app.models.creas_unidade import CreasUnidade  # type: ignore

    from app.models.pessoa_suas import PessoaSUAS  # type: ignore
    from app.models.familia_suas import FamiliaSUAS, FamiliaMembro  # type: ignore
    from app.models.caso_cras import CasoCras, CasoCrasHistorico  # type: ignore
    from app.models.cras_pia import CrasPiaPlano, CrasPiaAcao  # type: ignore
    from app.models.cadunico_precadastro import CadunicoPreCadastro  # type: ignore
    from app.models.cras_tarefas import CrasTarefa  # type: ignore
    from app.models.cras_encaminhamento import CrasEncaminhamento  # type: ignore

    from app.models.creas_caso import CreasCaso, CreasCasoHistorico  # type: ignore

    from app.models.pessoa import PessoaRua  # type: ignore
    from app.models.caso_pop_rua import CasoPopRua, CasoPopRuaEtapaHistorico  # type: ignore

    from app.models.encaminhamentos import EncaminhamentoIntermunicipal, EncaminhamentoEvento  # type: ignore

    from app.models.osc import Osc, OscParceria, OscPrestacaoContas  # type: ignore

    init_db()

    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    print(f"[SIM] DB={db_url} run_id={run_id}")

    with Session(engine) as session:
        # -------------------
        # Municípios (garante base)
        # -------------------
        for dados in MUNICIPIOS_BASE:
            nome = dados["nome"]
            existente = session.exec(select(Municipio).where(Municipio.nome == nome)).first()
            if not existente:
                session.add(Municipio(**dados))
                session.commit()

        # municipio alvo existe?
        mid = int(args.municipio_id)
        mun = session.get(Municipio, mid)
        if not mun:
            raise SystemExit(f"Município id={mid} não existe. Rode seed_municipios primeiro.")

        # -------------------
        # Unidades
        # -------------------
        cras_units = session.exec(select(CrasUnidade).where(CrasUnidade.municipio_id == mid)).all()
        if not cras_units:
            for n in ["CRAS 1", "CRAS 2"]:
                u = CrasUnidade(municipio_id=mid, nome=n, ativo=True)
                session.add(u)
            session.commit()
            cras_units = session.exec(select(CrasUnidade).where(CrasUnidade.municipio_id == mid)).all()

        creas_units = session.exec(select(CreasUnidade).where(CreasUnidade.municipio_id == mid)).all()
        if not creas_units:
            u = CreasUnidade(municipio_id=mid, nome="CREAS 1", ativo=True)
            session.add(u)
            session.commit()
            creas_units = [u]

        cras_unit_ids = [int(u.id) for u in cras_units if u.id]
        creas_unit_ids = [int(u.id) for u in creas_units if u.id]

        # -------------------
        # Usuários (300)
        # -------------------
        senha_hash = hash_senha(args.senha)

        def create_users_for_module(mod: str, total: int) -> List[Usuario]:
            # distribuição: 70 técnico, 15 recepção, 10 leitura, 5 coord
            # No CRAS: 1 secretário (substitui 1 coord)
            users: List[Usuario] = []
            dist: List[Tuple[str, int]] = [("tecnico", 70), ("recepcao", 15), ("leitura", 10), ("coord_municipal", 5)]
            if mod == "cras":
                dist = [("tecnico", 70), ("recepcao", 15), ("leitura", 10), ("coord_municipal", 4), ("secretario", 1)]

            target = total
            for perfil, n in dist:
                for _ in range(n):
                    if len(users) >= target:
                        break
                    idx = len(users) + 1
                    email = f"sim_{mod}_{perfil}_{idx:03d}@sim.local"
                    nome = f"Sim {mod.upper()} {perfil.title()} {idx:03d}"
                    exists = session.exec(select(Usuario).where(Usuario.email == email)).first()
                    if exists:
                        users.append(exists)
                        continue
                    u = Usuario(
                        nome=nome,
                        email=email,
                        perfil=perfil,
                        municipio_id=mid,
                        senha_hash=senha_hash,
                        ativo=True,
                    )
                    session.add(u)
                    session.flush()
                    users.append(u)
            session.commit()
            return users

        users_cras = create_users_for_module("cras", args.users_per_module)
        users_creas = create_users_for_module("creas", args.users_per_module)
        users_poprua = create_users_for_module("poprua", args.users_per_module)

        # cria também 1 "financeiro" e 1 "beneficios" (gestão interna) para testar
        for perfil in ["financeiro", "beneficios"]:
            email = f"sim_gestao_{perfil}@sim.local"
            ex = session.exec(select(Usuario).where(Usuario.email == email)).first()
            if not ex:
                u = Usuario(
                    nome=f"Sim Gestão {perfil.title()}",
                    email=email,
                    perfil=perfil,
                    municipio_id=mid,
                    senha_hash=senha_hash,
                    ativo=True,
                )
                session.add(u)
                session.commit()

        # salva credenciais
        sim_dir = os.path.join(os.path.dirname(__file__), "..", "storage", "sim")
        os.makedirs(sim_dir, exist_ok=True)
        cred_path = os.path.join(sim_dir, f"muni{mid}_{run_id}_users.json")
        payload = {
            "run_id": run_id,
            "municipio_id": mid,
            "senha": args.senha,
            "usuarios": [
                {"email": u.email, "perfil": u.perfil, "nome": u.nome, "municipio_id": u.municipio_id}
                for u in (users_cras + users_creas + users_poprua)
            ]
            + [
                {"email": "sim_gestao_financeiro@sim.local", "perfil": "financeiro", "nome": "Sim Gestão Financeiro", "municipio_id": mid},
                {"email": "sim_gestao_beneficios@sim.local", "perfil": "beneficios", "nome": "Sim Gestão Beneficios", "municipio_id": mid},
            ],
        }
        with open(cred_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"[SIM] credenciais: {cred_path}")

        # helpers de seleção de técnicos
        cras_tecnicos = [u for u in users_cras if u.perfil in ("tecnico", "operador")]
        creas_tecnicos = [u for u in users_creas if u.perfil in ("tecnico", "operador")]
        poprua_tecnicos = [u for u in users_poprua if u.perfil in ("tecnico", "operador")]

        # -------------------
        # CRAS: pessoas/famílias/casos
        # -------------------
        bairros = ["Centro", "Vila Nova", "Jardim", "Parque", "Santa Clara", "São José"]
        territorios = ["Território A", "Território B", "Território C", "Território D"]

        for i in range(args.cases_cras):
            unidade_id = rng.choice(cras_unit_ids)
            terr = rng.choice(territorios)
            bairro = rng.choice(bairros)

            tipo = "familia" if rng.random() < 0.65 else "individuo"

            pessoa = PessoaSUAS(
                municipio_id=mid,
                nome=f"Pessoa CRAS {i+1:04d}",
                cpf=_mk_cpf(rng),
                nis=_mk_nis(rng),
                bairro=bairro,
                territorio=terr,
                criado_em=_dt_days_ago(rng, 120),
                atualizado_em=datetime.utcnow(),
            )
            session.add(pessoa)
            session.flush()

            familia_id: Optional[int] = None
            if tipo == "familia":
                fam = FamiliaSUAS(
                    municipio_id=mid,
                    nis_familia=_mk_nis(rng),
                    bairro=bairro,
                    territorio=terr,
                    referencia_pessoa_id=int(pessoa.id),
                )
                session.add(fam)
                session.flush()
                session.add(
                    FamiliaMembro(
                        familia_id=int(fam.id),
                        pessoa_id=int(pessoa.id),
                        parentesco="responsável",
                        responsavel_bool=True,
                    )
                )
                familia_id = int(fam.id)

            etapa = rng.choice(CRAS_ETAPAS)
            sla = int(CRAS_SLA.get(etapa, 7))
            inicio_etapa, _, _ = _sla_start_for(rng, sla)

            data_abertura = _dt_days_ago(rng, 180)
            if data_abertura > inicio_etapa:
                data_abertura = inicio_etapa - timedelta(days=rng.randint(0, 10))

            caso = CasoCras(
                municipio_id=mid,
                unidade_id=int(unidade_id),
                tipo_caso=tipo,
                pessoa_id=int(pessoa.id),
                familia_id=familia_id,
                status="em_andamento",
                etapa_atual=etapa,
                prioridade=rng.choice(["baixa", "media", "alta"]),
                tecnico_responsavel_id=int(rng.choice(cras_tecnicos).id) if cras_tecnicos else None,
                data_abertura=data_abertura,
                data_inicio_etapa_atual=inicio_etapa,
                prazo_etapa_dias=sla,
                estagnado=(rng.random() < 0.08),
                motivo_estagnacao="Aguardando retorno da família" if rng.random() < 0.08 else None,
                aguardando_validacao=(rng.random() < 0.10),
                pendente_validacao_desde=(datetime.utcnow() - timedelta(days=rng.randint(3, 10))) if rng.random() < 0.10 else None,
                atualizado_em=datetime.utcnow(),
            )
            session.add(caso)
            session.flush()

            session.add(
                CasoCrasHistorico(
                    caso_id=int(caso.id),
                    etapa=caso.etapa_atual,
                    tipo_acao="abertura",
                    usuario_id=caso.tecnico_responsavel_id,
                    usuario_nome="seed_sim",
                    observacoes="Caso simulado (Município 1).",
                    criado_em=datetime.utcnow(),
                )
            )

            # PIA: cria para ~60% dos casos
            if rng.random() < 0.60:
                plano = CrasPiaPlano(
                    municipio_id=mid,
                    unidade_id=int(unidade_id),
                    caso_id=int(caso.id),
                    resumo_diagnostico="Diagnóstico simulado.",
                    objetivos="Objetivos simulados.",
                    status="ativo",
                    data_inicio=date.today() - timedelta(days=rng.randint(0, 60)),
                )
                session.add(plano)
                session.flush()
                for j in range(rng.randint(1, 3)):
                    session.add(
                        CrasPiaAcao(
                            plano_id=int(plano.id),
                            descricao=f"Ação simulada {j+1}",
                            responsavel_usuario_id=caso.tecnico_responsavel_id,
                            prazo=date.today() + timedelta(days=rng.randint(1, 30)),
                            status=rng.choice(["pendente", "em_andamento", "concluida"]),
                        )
                    )

            # CadÚnico pendente em ~30%
            if rng.random() < 0.30:
                criado = datetime.utcnow() - timedelta(days=rng.randint(5, 60))
                session.add(
                    CadunicoPreCadastro(
                        municipio_id=mid,
                        unidade_id=int(unidade_id),
                        pessoa_id=int(pessoa.id),
                        familia_id=familia_id,
                        caso_id=int(caso.id),
                        status=rng.choice(["pendente", "agendado"]),
                        data_agendada=(datetime.utcnow() + timedelta(days=rng.randint(1, 10))) if rng.random() < 0.5 else None,
                        observacoes="Pré-cadastro simulado.",
                        criado_em=criado,
                        atualizado_em=criado,
                    )
                )

            # tarefas vencidas em ~20%
            if rng.random() < 0.20:
                venc = date.today() - timedelta(days=rng.randint(1, 30))
                session.add(
                    CrasTarefa(
                        municipio_id=mid,
                        unidade_id=int(unidade_id),
                        responsavel_id=caso.tecnico_responsavel_id,
                        responsavel_nome="seed_sim",
                        ref_tipo="caso",
                        ref_id=int(caso.id),
                        titulo="Tarefa simulada",
                        descricao="Tarefa gerada para teste de fila/SLA.",
                        prioridade=rng.choice(["baixa", "media", "alta", "critica"]),
                        status=rng.choice(["aberta", "em_andamento"]),
                        data_vencimento=venc,
                        criado_em=datetime.utcnow() - timedelta(days=rng.randint(1, 40)),
                        atualizado_em=datetime.utcnow(),
                    )
                )

            if (i + 1) % 50 == 0:
                session.commit()
                print(f"[SIM] CRAS casos: {i+1}/{args.cases_cras}")

        session.commit()
        print(f"[SIM] CRAS: {args.cases_cras} casos criados.")

        # -------------------
        # CREAS: casos
        # -------------------
        for i in range(args.cases_creas):
            unidade_id = rng.choice(creas_unit_ids)

            pessoa_id: Optional[int] = None
            if rng.random() < 0.65:
                terr = rng.choice(territorios)
                bairro = rng.choice(bairros)
                p = PessoaSUAS(
                    municipio_id=mid,
                    nome=f"Pessoa CREAS {i+1:04d}",
                    cpf=_mk_cpf(rng),
                    nis=_mk_nis(rng),
                    bairro=bairro,
                    territorio=terr,
                    criado_em=_dt_days_ago(rng, 200),
                    atualizado_em=datetime.utcnow(),
                )
                session.add(p)
                session.flush()
                pessoa_id = int(p.id)

            etapa = rng.choice(CREAS_ETAPAS)
            sla = rng.choice([2, 7, 14, 30])
            inicio, _, _ = _sla_start_for(rng, sla)

            caso = CreasCaso(
                municipio_id=mid,
                unidade_id=int(unidade_id),
                tipo_caso=rng.choice(["familia", "individuo"]),
                pessoa_id=pessoa_id,
                familia_id=None,
                status="em_andamento",
                etapa_atual=etapa,
                prioridade=rng.choice(["baixa", "media", "alta"]),
                risco=rng.choice(["baixo", "medio", "alto"]),
                tecnico_responsavel_id=int(rng.choice(creas_tecnicos).id) if creas_tecnicos else None,
                titulo=rng.choice(
                    [
                        "Violência doméstica (sim)",
                        "Negligência (sim)",
                        "Trabalho infantil (sim)",
                        "Abuso (sim)",
                        "Violação de direitos (sim)",
                    ]
                ),
                tipologia=rng.choice(["violencia", "violacao_direitos", "trabalho_infantil", "abuso"]),
                data_abertura=_dt_days_ago(rng, 240),
                data_inicio_etapa_atual=inicio,
                prazo_etapa_dias=sla,
                estagnado=(rng.random() < 0.05),
                motivo_estagnacao="Aguardando documentos" if rng.random() < 0.05 else None,
                atualizado_em=datetime.utcnow(),
            )
            session.add(caso)
            session.flush()

            session.add(
                CreasCasoHistorico(
                    caso_id=int(caso.id),
                    etapa=caso.etapa_atual,
                    tipo_acao="abertura",
                    usuario_id=caso.tecnico_responsavel_id,
                    usuario_nome="seed_sim",
                    observacoes="Caso CREAS simulado.",
                    criado_em=datetime.utcnow(),
                )
            )

            if (i + 1) % 50 == 0:
                session.commit()
                print(f"[SIM] CREAS casos: {i+1}/{args.cases_creas}")

        session.commit()
        print(f"[SIM] CREAS: {args.cases_creas} casos criados.")

        # -------------------
        # PopRua: pessoas + casos
        # -------------------
        poprua_pessoas: List[PessoaRua] = []
        for i in range(args.cases_poprua):
            p = PessoaRua(
                nome_social=f"Pessoa Rua {i+1:04d}",
                cpf=_mk_cpf(rng),
                nis=_mk_nis(rng),
                municipio_origem_id=mid,
                observacoes_gerais="Cadastro simulado PopRua.",
            )
            session.add(p)
            session.flush()
            poprua_pessoas.append(p)

            etapa = rng.choice(POPRUA_ETAPAS)
            sla = rng.choice([2, 7, 15, 30])
            inicio, _, _ = _sla_start_for(rng, sla)

            caso = CasoPopRua(
                pessoa_id=int(p.id),
                municipio_id=mid,
                status="em_andamento",
                etapa_atual=etapa,
                ativo=True,
                data_abertura=_dt_days_ago(rng, 240),
                data_ultima_atualizacao=datetime.utcnow(),
                data_inicio_etapa_atual=inicio,
                prazo_etapa_dias=sla,
                estagnado=(rng.random() < 0.06),
                motivo_estagnacao="Sem contato recente" if rng.random() < 0.06 else None,
            )
            session.add(caso)
            session.flush()

            session.add(
                CasoPopRuaEtapaHistorico(
                    caso_id=int(caso.id),
                    etapa=etapa,
                    data_acao=caso.data_inicio_etapa_atual or datetime.utcnow(),
                    usuario_responsavel=(rng.choice(poprua_tecnicos).nome if poprua_tecnicos else "seed_sim"),
                    responsavel_funcao="técnico",
                    responsavel_servico="PopRua",
                    observacoes="Etapa inicial simulada.",
                    tipo_acao="abertura",
                )
            )

            if (i + 1) % 50 == 0:
                session.commit()
                print(f"[SIM] PopRua casos: {i+1}/{args.cases_poprua}")

        session.commit()
        print(f"[SIM] PopRua: {args.cases_poprua} pessoas+casos criados.")

        # -------------------
        # Rede: Encaminhamentos CRAS (com devolutiva faltando)
        # -------------------
        for _ in range(40):
            unidade_id = rng.choice(cras_unit_ids)
            session.add(
                CrasEncaminhamento(
                    municipio_id=mid,
                    unidade_id=int(unidade_id),
                    pessoa_id=None,
                    destino_tipo=rng.choice(["osc", "creas", "saude", "educacao"]),
                    destino_nome=rng.choice(["Associação Nova Vida", "CREAS 1", "UBS Central", "Escola Municipal"]),
                    motivo="Encaminhamento simulado",
                    observacao_operacional="Teste de rede e devolutiva.",
                    status=rng.choice(["enviado", "recebido", "agendado", "atendido"]),
                    enviado_em=datetime.utcnow() - timedelta(days=rng.randint(1, 40)),
                    prazo_devolutiva_dias=rng.choice([2, 5, 7]),
                    criado_por_nome="seed_sim",
                    atualizado_por_nome="seed_sim",
                )
            )

        session.commit()
        print("[SIM] Rede: 40 encaminhamentos CRAS criados.")

        # -------------------
        # Rede intermunicipal (origem município 1)
        # -------------------
        destinos = [2, 3, 4]  # ids já existem pelo seed_municipios
        for _ in range(30):
            pessoa = rng.choice(poprua_pessoas)
            st = rng.choice(["solicitado", "solicitado", "contato", "aceito", "agendado", "passagem"])
            criado = datetime.utcnow() - timedelta(days=rng.randint(3, 50))
            enc = EncaminhamentoIntermunicipal(
                pessoa_id=int(pessoa.id),
                caso_id=None,
                municipio_origem_id=mid,
                municipio_destino_id=int(rng.choice(destinos)),
                motivo="Mudança de município (simulação)",
                observacoes="Encaminhamento intermunicipal simulado para stress test.",
                consentimento_registrado=True,
                status=st,
                contato_em=(criado + timedelta(days=1)) if st in ("contato", "aceito", "agendado", "passagem") else None,
                aceite_em=(criado + timedelta(days=3)) if st in ("aceito", "agendado", "passagem") else None,
                agendado_em=(criado + timedelta(days=7)) if st in ("agendado", "passagem") else None,
                passagem_em=(criado + timedelta(days=10)) if st in ("passagem",) else None,
                criado_em=criado,
                atualizado_em=datetime.utcnow(),
            )
            session.add(enc)
            session.flush()

            session.add(
                EncaminhamentoEvento(
                    encaminhamento_id=int(enc.id),
                    tipo=st,
                    detalhe="Evento simulado",
                    por_nome="seed_sim",
                    em=criado,
                )
            )

        session.commit()
        print("[SIM] Rede: 30 intermunicipais criados.")

        # -------------------
        # OSC + prestação de contas
        # -------------------
        osc = session.exec(
            select(Osc).where(Osc.municipio_id == mid).where(Osc.nome == "Associação Nova Vida")
        ).first()
        if not osc:
            osc = Osc(
                municipio_id=mid,
                nome="Associação Nova Vida",
                cnpj=_rand_digits(rng, 14),
                tipo="associacao",
                areas_atuacao="assistencia social",
                ativo=True,
            )
            session.add(osc)
            session.commit()
            session.refresh(osc)

        parc = session.exec(
            select(OscParceria)
            .where(OscParceria.municipio_id == mid)
            .where(OscParceria.osc_id == int(osc.id))
        ).first()
        if not parc:
            parc = OscParceria(
                municipio_id=mid,
                osc_id=int(osc.id),
                instrumento="termo_fomento",
                numero="001/2025",
                objeto="Serviço socioassistencial (sim)",
                valor_total=250000.0,
                status="ativa",
                gestor_responsavel_nome="Sim Gestão",
            )
            session.add(parc)
            session.commit()
            session.refresh(parc)

        for k in range(6):
            comp = (date.today().replace(day=1) - timedelta(days=30 * k)).strftime("%Y-%m")
            existe = session.exec(
                select(OscPrestacaoContas)
                .where(OscPrestacaoContas.parceria_id == int(parc.id))
                .where(OscPrestacaoContas.competencia == comp)
            ).first()
            if existe:
                continue
            prazo = date.today() - timedelta(days=rng.randint(5, 40))
            session.add(
                OscPrestacaoContas(
                    municipio_id=mid,
                    parceria_id=int(parc.id),
                    competencia=comp,
                    prazo_entrega=prazo,
                    status="pendente",
                    responsavel_nome="Sim Gestão",
                    observacao="Prestação de contas simulada em atraso.",
                )
            )
        session.commit()
        print("[SIM] OSC: prestações de contas criadas.")

    print("[SIM] Finalizado.")


if __name__ == "__main__":
    main()
