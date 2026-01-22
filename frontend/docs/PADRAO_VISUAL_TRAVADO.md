# Padrão visual travado (Topo PopRua)

Este projeto usa **um único topo padrão** para todos os módulos, baseado no PopRua.

## Componentes oficiais
- `frontend/src/components/SuasTopHeader.jsx`  → **Topo padrão** (classes PopRua)
- `frontend/src/components/CrasPageHeader.jsx` → **Cabeçalho de página** (100% largura)

## Regras
1. Não criar topo novo por módulo.
2. CRAS/CREAS/novos módulos devem usar wrappers mínimos que só passam props.
3. Botão **Sair** fica na **linha do Município** (padrão PopRua).
4. Linha **Unidade + Portal** (quando existir) é a segunda linha, sem Sair.

## Comandos
- Validar padrão: `./scripts/check_layout.sh`
- Restaurar padrão (se alguém bagunçar): `./scripts/restore_layout.sh`
- Criar wrappers para novo módulo:
  `./scripts/create_module_wrappers.sh equipamentos "Equipamentos" "Gestão de unidades e agenda"`

## Recomendação (Git)
Inicialize Git e faça commits frequentes. Se algo bagunçar, restaure com `restore_layout.sh` ou `git checkout`.
