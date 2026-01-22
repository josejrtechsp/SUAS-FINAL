#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
python3 - <<'PY'
import re, sys
from pathlib import Path
p = Path("frontend/src/TelaCrasCasos.jsx")
s = p.read_text(encoding="utf-8")
needle = "const [suasUI, setSuasUI] = useState({"
i = s.find(needle)
if i < 0:
    print("OK: sem bloco suasUI")
    sys.exit(0)
j = s.find("async function loadEtapas", i)
if j < 0:
    print("OK: sem loadEtapas após suasUI")
    sys.exit(0)
between = s[i:j]
if not re.search(r"\n\s*\}\);\s*\n", between):
    print("ERRO: ainda não existe fechamento '});' entre useState({ e async function loadEtapas")
    sys.exit(2)
print("OK: verify_fix_cras_casos_suasui_closure_v1")
PY
