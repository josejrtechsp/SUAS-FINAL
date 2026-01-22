# Ferramentas CLI — Gestão (Secretário)

Scripts para executar tarefas do módulo **Gestão** (dashboard do secretário) 100% pelo terminal.

## Instalação

Descompacte o ZIP na raiz do projeto e dê permissão de execução:

```bash
cd ~/POPNEWS1
unzip -o gestao_cli_tools.zip -d .
chmod +x tools/gestao_cli.sh
```

## Variáveis opcionais

```bash
export API="http://127.0.0.1:8001"   # base do backend
export USER="admin@poprua.local"     # login
export PASS="admin123"               # senha
export OUTDIR="$HOME/POPNEWS1/_exports"  # pasta de saída
export SIGN_CARGO="Secretário Municipal de Assistência Social"  # cargo padrão
# export SIGN_NAME="Fulano de Tal"  # nome (opcional) na assinatura
```

## Comandos

### Exportar SLA

```bash
./tools/gestao_cli.sh sla-export
```

### Ver a fila (e salvar `fila.json`)

```bash
./tools/gestao_cli.sh fila --atrasos
./tools/gestao_cli.sh fila --modulo rede --atrasos
```

### Gerar relatório com IA a partir do 1º item em atraso

```bash
./tools/gestao_cli.sh relatorio-first
```

### Gerar ofício de cobrança/devolutiva do 1º item REDE em atraso

```bash
./tools/gestao_cli.sh cobrar-rede-first
```

## Saídas

Os arquivos ficam em `OUTDIR` (padrão: `~/POPNEWS1/_exports`):

- `gestao_resumo.json`
- `gestao_sla_*.json`
- `fila.json`, `fila1.json`, `fila_rede.json`
- `RELATORIO_<ID>.pdf`
- `OFICIO_COBRANCA_<ID>.pdf`
