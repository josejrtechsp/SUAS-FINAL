PATCH #039B — Corrige gestao.py (erro de indent) e otimiza /gestao/fila com cap por fonte

- Corrige erro de import (unexpected indent) introduzido no patch anterior.
- Reintroduz cache TTL (nocache=1) e mantém comportamentos existentes.
- Otimiza /gestao/fila: limita leituras por fonte (cap_fetch_base/small) e ordena por campos de data quando disponíveis.
