# Padrão visual travado (PopRua)

Este projeto foi preparado para **usar o topo do PopRua como padrão único** em todos os módulos (CRAS, CREAS e os próximos).

## O que está travado

- **Topo (header) único:** `frontend/src/components/SuasTopHeader.jsx`
  - Usa as **mesmas classes/CSS** do PopRua (`app-header`, `app-header-inner`, `header-user-row`, `app-tabs`).
- **PageHeader em largura total:** `frontend/src/components/CrasPageHeader.jsx`
  - Força `width: 100%` e `flex: 0 0 100%` para não encolher no `flex-wrap`.

Wrappers por módulo (somente props/textos, sem layout próprio):
- `frontend/src/components/CrasTopHeader.jsx`
- `frontend/src/components/CreasTopHeader.jsx`

## Como verificar o padrão

Rode:
```bash
./scripts/check_layout.sh
```

Se algo sair do padrão, o script interrompe com erro.

## Como restaurar o padrão (se alguém mexer)

Rode:
```bash
./scripts/restore_layout.sh
```

Isso copia os arquivos canônicos de `scripts/layout_canon/` para o local correto.

## Como criar wrappers para um novo módulo (reproduzir o padrão)

Exemplo:
```bash
./scripts/create_module_wrappers.sh equipamentos "Equipamentos" "Gestão de unidades, equipe e agenda"
```

Isso cria:
- `frontend/src/components/EquipamentosTopHeader.jsx`
- `frontend/src/components/EquipamentosPageHeader.jsx`

Depois, no App do módulo, importe e use o `...TopHeader` no topo.

## Recomendado: usar Git (checkpoint)

```bash
git init
git add -A
git commit -m "Padrão visual travado"
```

Antes de mudar qualquer coisa:
```bash
git add -A
git commit -m "checkpoint antes de mexer"
```
