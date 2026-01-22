ATUALIZAÇÃO — CREAS · Perfis (B) + Aprovação de Encerramento

O que esta atualização faz (SEM mexer no topo/abas/page-header imutáveis):

1) Perfis (ACL) padronizados
- gestor/coordenação: aprova encerramentos, vê tudo, vê pendências
- técnico (inclui perfil "operador"): vê "meus casos + sem responsável", registra atendimentos e rede
- recepção: cria casos, agenda, edita apenas contato/endereço na Ficha Única
- leitura/controle: somente leitura (painel/relatórios)

2) Fluxo B de encerramento
- Técnico: solicita encerramento (motivo + resumo)
- Gestor: aprova e encerra OU recusa (com motivo)
- Pendências e Painel do gestor passam a mostrar "Encerramentos para aprovar"

3) Regra de responsabilidade ao criar caso (autoexplicativo)
- Se técnico/gestor cria: caso já nasce com responsável
- Se recepção cria: caso nasce SEM responsável para um técnico ASSUMIR (1 clique)

Como aplicar (Terminal, na raiz do projeto):
  cd ~/POPNEWS1
  unzip -o ~/Downloads/SUAS_CREAS_PERFIS_B_ATUALIZACAO.zip -d .

Depois, reinicie o front:
  cd ~/POPNEWS1/frontend
  NODE_OPTIONS="" npm run dev

Como testar rapidamente:
- CREAS → Configurações → "Criar 20 casos de demonstração"
- Entre como TÉCNICO (perfil "operador") e solicite encerramento em um caso.
- Entre como GESTOR (perfil "admin"/"gestor") e aprove em Pendências ou no caso.
