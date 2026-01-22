PATCH_SUS_SANDBOX_BACK_V4_FIX1

Corrige o verificador e garante que o endpoint /sus/auditoria existe.

- Atualiza tools/verify_sus_sandbox_back_v4.sh (grep mais robusto)
- Sobrescreve sus_sandbox_backend/app/routers/sus.py com uma versão mínima que contém /auditoria
  (Use este patch apenas se o seu arquivo atual estiver sem /auditoria)

OBS: Se você já tem o router V4 completo, aplique só para atualizar o verify.
