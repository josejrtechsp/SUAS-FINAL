\
#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 tools/patch_front_rma_prontuario_export_v2.py .
echo "OK: apply_front_rma_prontuario_export_v2"
