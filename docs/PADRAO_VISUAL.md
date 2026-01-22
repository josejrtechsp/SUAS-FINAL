# Padrão visual travado (PopRua = referência)

Este projeto está travado para que **todos os módulos** usem o **mesmo topo** do PopRua e o mesmo bloco de página (PageHeader) em largura total.

## Fonte única do topo
- `frontend/src/components/SuasTopHeader.jsx`

## Fonte única do PageHeader
- `frontend/src/components/CrasPageHeader.jsx` (com `width: 100%` e `flex: 0 0 100%`)

## Como validar o padrão
```bash
./scripts/check_layout.sh
```

## Como restaurar o padrão (se algum update bagunçar)
```bash
./scripts/restore_layout.sh
```

## Como criar wrappers para um novo módulo
```bash
./scripts/create_module_wrappers.sh equipamentos Equipamentos "Gestão de unidades, capacidade, equipe e agenda."
```
Isso cria:
- `frontend/src/components/EquipamentosTopHeader.jsx`
- `frontend/src/components/EquipamentosPageHeader.jsx`

> Regra: **não copie** HTML/CSS do topo para cada módulo. Use sempre `SuasTopHeader`.
