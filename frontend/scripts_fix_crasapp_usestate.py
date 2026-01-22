from pathlib import Path
from datetime import datetime
import re

p = Path("src/CrasApp.jsx")
txt = p.read_text(encoding="utf-8").splitlines(True)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = p.with_suffix(p.suffix + f".bak_usestatefix_{ts}")
bak.write_text("".join(txt), encoding="utf-8")

# 1) achar onde está o localStorage do municipio
idx_saved = None
for i, ln in enumerate(txt):
    if "cras_municipio_id" in ln:
        idx_saved = i
        break
if idx_saved is None:
    raise SystemExit("Não achei 'cras_municipio_id' no CrasApp.jsx")

# 2) achar o início do bloco const [x, setX] = useState(
start = idx_saved
pat_start = re.compile(r"const\s*\[\s*([^,\]]+)\s*,\s*([^\]]+)\]\s*=\s*useState\s*\(")
m = None
while start > 0:
    m = pat_start.search(txt[start])
    if m:
        break
    start -= 1
if not m:
    raise SystemExit("Não achei a linha 'const [.., ..] = useState(' acima do cras_municipio_id")

state_name = m.group(1).strip()
setter_name = m.group(2).strip()

# 3) achar o fim do bloco (fecha com '});' ou ');')
end = idx_saved
while end < len(txt) and "});" not in txt[end] and ");" not in txt[end]:
    end += 1
if end >= len(txt):
    raise SystemExit("Não achei o fechamento do useState (');' ou '});').")

# inclui a linha de fechamento
end = end + 1

new_block = f"""  const [{state_name}, {setter_name}] = useState(() => {{
    try {{
      const saved = localStorage.getItem("cras_municipio_id");
      if (saved) return saved;
    }} catch (e) {{}}
    return usuarioLogado?.municipio_id ? String(usuarioLogado.municipio_id) : "";
  }});
"""

txt[start:end] = [new_block]
p.write_text("".join(txt), encoding="utf-8")

print("OK: corrigi o useState do municipio no CrasApp.jsx")
print("Backup:", bak)
print("State:", state_name, "| Setter:", setter_name)
