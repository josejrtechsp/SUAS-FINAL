#!/usr/bin/env bash
set -euo pipefail

API_DEFAULT="http://127.0.0.1:8001"
API="${API:-$API_DEFAULT}"
USER="${USER:-admin@poprua.local}"
PASS="${PASS:-admin123}"
OUTDIR="${OUTDIR:-$HOME/POPNEWS1/_exports}"
SIGN_CARGO="${SIGN_CARGO:-Secretário Municipal de Assistência Social}"
SIGN_NAME="${SIGN_NAME:-}"

usage() {
  cat <<'USAGE'
Uso: gestao_cli.sh <comando> [opções]

Ambiente (opcional):
  API=http://127.0.0.1:8001   Base URL do backend
  USER=admin@poprua.local     Usuário
  PASS=admin123               Senha
  OUTDIR=~/POPNEWS1/_exports  Pasta de saída
  SIGN_CARGO="Secretário Municipal de Assistência Social"  Cargo padrão na assinatura
  SIGN_NAME="Nome do Secretário"  Nome (opcional) na assinatura

Comandos:
  token                         Imprime token JWT (debug)
  resumo                        Salva gestao_resumo.json
  sla-export                    Exporta SLA (modulo/unidade/territorio/etapa/responsavel/destino)
  fila [--modulo X] [--atrasos] Lista fila e salva fila.json
  relatorio-first               Gera relatório (IA + PDF) do 1º item em atraso
  cobrar-rede-first             Gera ofício de cobrança do 1º item REDE em atraso e baixa PDF

Exemplos:
  ./tools/gestao_cli.sh sla-export
  ./tools/gestao_cli.sh fila --modulo rede --atrasos
  ./tools/gestao_cli.sh relatorio-first
  ./tools/gestao_cli.sh cobrar-rede-first
USAGE
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "ERRO: precisa de '$1' no PATH"; exit 1; }
}

get_token() {
  curl -sS -X POST \
    --data-urlencode "username=$USER" \
    --data-urlencode "password=$PASS" \
    "$API/auth/login" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
}

auth_me() {
  local token="$1"
  curl -sS "$API/auth/me" -H "Authorization: Bearer $token"
}

mkdir -p "$OUTDIR"

cmd="${1:-}"
shift || true

case "$cmd" in
  ""|-h|--help)
    usage
    exit 0
    ;;

  token)
    need_cmd python3
    tok=$(get_token)
    echo "$tok"
    ;;

  resumo)
    need_cmd python3
    tok=$(get_token)
    curl -sS "$API/gestao/dashboard/resumo" \
      -H "Authorization: Bearer $tok" \
      > "$OUTDIR/gestao_resumo.json"
    python3 -m json.tool "$OUTDIR/gestao_resumo.json" | head -n 60
    echo "OK: $OUTDIR/gestao_resumo.json"
    ;;

  sla-export)
    need_cmd python3
    tok=$(get_token)
    for GB in modulo unidade territorio etapa responsavel destino; do
      echo "== SLA $GB =="
      curl -sS -L "$API/gestao/dashboard/sla?group_by=$GB" \
        -H "Authorization: Bearer $tok" \
        > "$OUTDIR/gestao_sla_$GB.json"
      python3 -m json.tool "$OUTDIR/gestao_sla_$GB.json" >/dev/null \
        && echo "OK: $OUTDIR/gestao_sla_$GB.json" \
        || { echo "ERRO: SLA $GB não é JSON"; head -n 30 "$OUTDIR/gestao_sla_$GB.json"; exit 2; }
    done
    ;;

  fila)
    need_cmd python3
    modulo=""
    somente_atrasos=0
    while [[ ${#} -gt 0 ]]; do
      case "$1" in
        --modulo)
          modulo="$2"; shift 2;;
        --atrasos)
          somente_atrasos=1; shift;;
        *)
          echo "Opção desconhecida: $1"; usage; exit 2;;
      esac
    done
    tok=$(get_token)
    url="$API/gestao/fila?limit=50"
    [[ -n "$modulo" ]] && url+="&modulo=$modulo"
    [[ $somente_atrasos -eq 1 ]] && url+="&somente_atrasos=1"

    curl -sS "$url" -H "Authorization: Bearer $tok" > "$OUTDIR/fila.json"

    OUTDIR="$OUTDIR" python3 - <<'PY'
import os, json
from pathlib import Path
outdir = Path(os.environ["OUTDIR"])
d = json.loads((outdir/"fila.json").read_text(encoding="utf-8"))
print("total:", d.get("total"))
for it in d.get("items", [])[:30]:
    print(f"{it.get('modulo')} | {it.get('tipo')} | id={it.get('referencia_id')} | atraso={it.get('dias_em_atraso')} | {it.get('titulo')}")
PY

    echo "OK: $OUTDIR/fila.json"
    ;;

  relatorio-first)
    need_cmd python3
    tok=$(get_token)

    curl -sS "$API/gestao/fila?somente_atrasos=1&limit=1" \
      -H "Authorization: Bearer $tok" \
      > "$OUTDIR/fila1.json"

    OUTDIR="$OUTDIR" python3 - <<'PY'
import os, json
from pathlib import Path
outdir = Path(os.environ["OUTDIR"])
d = json.loads((outdir/"fila1.json").read_text(encoding="utf-8"))
it = d["items"][0]
ctx=(
  "Relatório de pendência (Gestão/Secretaria).\n"
  f"Módulo: {it.get('modulo')}.\n"
  f"Tipo: {it.get('tipo')}.\n"
  f"ID: {it.get('referencia_id')}.\n"
  f"Título: {it.get('titulo')}\n"
  f"Etapa atual: {it.get('etapa_atual')}\n"
  f"Dias em atraso: {it.get('dias_em_atraso')}\n"
  f"Motivo/Descrição: {it.get('motivo') or it.get('descricao') or ''}\n"
  "Solicitar providências e prazo de retorno.\n"
)
(outdir/"ia_req.json").write_text(json.dumps({
  "modelo":"relatorio_padrao",
  "tipo":"relatorio",
  "contexto": ctx,
  "preferencias":"curto, objetivo, formal, sem dados pessoais",
}, ensure_ascii=False), encoding="utf-8")
print("OK: ia_req.json")
PY

    curl -sS -X POST "$API/ia/rascunho/documento" \
      -H "Authorization: Bearer $tok" \
      -H "Content-Type: application/json" \
      -d @"$OUTDIR/ia_req.json" \
      > "$OUTDIR/draft.json"

    # municipio_id (para admin/global)
    ME_JSON=$(auth_me "$tok")
MUNI_ID=$(echo "$ME_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin)["municipio_id"])')
USER_NOME=$(echo "$ME_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("nome",""))')

    OUTDIR="$OUTDIR" MUNI_ID="$MUNI_ID" USER_NOME="$USER_NOME" SIGN_CARGO="$SIGN_CARGO" SIGN_NAME="$SIGN_NAME" python3 - <<'PY'
import os, json
from pathlib import Path
outdir = Path(os.environ["OUTDIR"])
muni_id = int(os.environ["MUNI_ID"])
d = json.loads((outdir/"draft.json").read_text(encoding="utf-8"))

doc={
  "municipio_id": muni_id,
  "tipo": d.get("tipo","relatorio"),
  "modelo": d.get("modelo","relatorio_padrao"),
  "assunto": d.get("assunto","Relatório"),
  "destinatario_nome": d.get("destinatario_nome") or "",
  "destinatario_cargo": d.get("destinatario_cargo") or "",
  "destinatario_orgao": d.get("destinatario_orgao") or "",
  "campos": d.get("campos") or {},
  "emissor": "gestao",
  "salvar": True,
}

# Defaults de assinatura (padroniza cargo do Secretário e evita <NOME>/<CARGO>)
campos = doc.get("campos") or {}
sign_cargo = (os.environ.get("SIGN_CARGO") or "").strip()
sign_name = (os.environ.get("SIGN_NAME") or "").strip() or (os.environ.get("USER_NOME") or "").strip()

def is_placeholder(x):
    s = ("" if x is None else str(x)).strip()
    return (not s) or (s.startswith("<") and s.endswith(">"))

if sign_cargo and is_placeholder(campos.get("assinante_cargo")):
    campos["assinante_cargo"] = sign_cargo
if sign_name and is_placeholder(campos.get("assinante_nome")):
    campos["assinante_nome"] = sign_name

doc["campos"] = campos

(outdir/"doc_req.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
print("OK: doc_req.json")

PY

    curl -sS -X POST "$API/documentos/gerar" \
      -H "Authorization: Bearer $tok" \
      -H "Content-Type: application/json" \
      -d @"$OUTDIR/doc_req.json" \
      > "$OUTDIR/doc_resp.json"

    REL_ID=$(python3 -c 'import json; print(json.load(open("'$OUTDIR'/doc_resp.json"))["id"])')

    curl -sS -L -H "Authorization: Bearer $tok" \
      "$API/documentos/$REL_ID/download" \
      -o "$OUTDIR/RELATORIO_$REL_ID.pdf"

    echo "OK: $OUTDIR/RELATORIO_$REL_ID.pdf"
    ;;

  cobrar-rede-first)
    need_cmd python3
    tok=$(get_token)

    curl -sS "$API/gestao/fila?modulo=rede&somente_atrasos=1&limit=50" \
      -H "Authorization: Bearer $tok" \
      > "$OUTDIR/fila_rede.json"

    ENC_ID=$(OUTDIR="$OUTDIR" python3 - <<'PY'
import os, json
from pathlib import Path
outdir = Path(os.environ["OUTDIR"])
d = json.loads((outdir/"fila_rede.json").read_text(encoding="utf-8"))
items = d.get("items", [])
for tipo in ("encaminhamento", "encaminhamento_intermunicipal"):
    for it in items:
        if it.get("tipo") == tipo:
            print(it.get("referencia_id"))
            raise SystemExit
print("")
PY
)

    if [[ -z "$ENC_ID" ]]; then
      echo "Nenhum item REDE encontrado em atraso."; exit 3
    fi

    curl -sS -X POST "$API/documentos/gerar/cobranca-devolutiva" \
      -H "Authorization: Bearer $tok" \
      -H "Content-Type: application/json" \
      -d "{\"encaminhamento_id\": $ENC_ID, \"emissor\": \"smas\", \"usar_ia\": true, \"salvar\": true}" \
      > "$OUTDIR/cobranca_resp.json"

    DOC_ID=$(python3 -c 'import json; print(json.load(open("'$OUTDIR'/cobranca_resp.json"))["id"])')

    curl -sS -L -H "Authorization: Bearer $tok" \
      "$API/documentos/$DOC_ID/download" \
      -o "$OUTDIR/OFICIO_COBRANCA_$DOC_ID.pdf"

    echo "OK: $OUTDIR/OFICIO_COBRANCA_$DOC_ID.pdf"
    ;;

  *)
    echo "Comando desconhecido: $cmd"; usage; exit 2
    ;;
esac
