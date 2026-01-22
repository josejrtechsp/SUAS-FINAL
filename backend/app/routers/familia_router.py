from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.pessoa import PessoaRua
from app.models.familia_beneficio import (
    FamiliaReferencia,
    FamiliaReferenciaBase,
    BeneficioPessoa,
    BeneficioPessoaBase,
)

router = APIRouter(prefix="/pessoas", tags=["familia_beneficios"])


# -------------------------------------------------
# FAMÍLIA DE REFERÊNCIA
# -------------------------------------------------


@router.get("/{pessoa_id}/familia-referencia", response_model=Optional[FamiliaReferencia])
def obter_familia_referencia(
    pessoa_id: int,
    session: Session = Depends(get_session),
):
    """
    Retorna a família de referência da pessoa (se existir).
    Se não existir, devolve null.
    """
    pessoa = session.get(PessoaRua, pessoa_id)
    if not pessoa:
        # pessoa não encontrada -> devolve None sem quebrar o front
        return None

    stmt = select(FamiliaReferencia).where(FamiliaReferencia.pessoa_id == pessoa_id)
    familia = session.exec(stmt).first()
    return familia


@router.post("/{pessoa_id}/familia-referencia", response_model=FamiliaReferencia)
def salvar_familia_referencia(
    pessoa_id: int,
    dados: FamiliaReferenciaBase,
    session: Session = Depends(get_session),
):
    """
    Cria ou atualiza a família de referência da pessoa.
    Regra simples: uma família de referência por pessoa.
    """
    pessoa = session.get(PessoaRua, pessoa_id)
    if not pessoa:
        raise HTTPException(
            status_code=404,
            detail="Pessoa em situação de rua não encontrada.",
        )

    stmt = select(FamiliaReferencia).where(FamiliaReferencia.pessoa_id == pessoa_id)
    familia = session.exec(stmt).first()

    if familia:
        # Atualiza campos
        update_data = dados.dict(exclude_unset=True)
        for campo, valor in update_data.items():
            setattr(familia, campo, valor)
    else:
        familia = FamiliaReferencia.from_orm(dados)
        familia.pessoa_id = pessoa_id
        session.add(familia)

    session.commit()
    session.refresh(familia)
    return familia


# -------------------------------------------------
# BENEFÍCIOS DA PESSOA
# -------------------------------------------------


@router.get("/{pessoa_id}/beneficios", response_model=List[BeneficioPessoa])
def listar_beneficios_pessoa(
    pessoa_id: int,
    session: Session = Depends(get_session),
):
    """
    Lista todos os benefícios associados à pessoa em situação de rua.
    """
    pessoa = session.get(PessoaRua, pessoa_id)
    if not pessoa:
        # pessoa não encontrada -> devolve lista vazia
        return []

    stmt = (
        select(BeneficioPessoa)
        .where(BeneficioPessoa.pessoa_id == pessoa_id)
        .order_by(BeneficioPessoa.data_inicio.desc().nullslast())
    )
    beneficios = session.exec(stmt).all()
    return list(beneficios)


@router.post("/{pessoa_id}/beneficios", response_model=BeneficioPessoa)
def criar_beneficio_para_pessoa(
    pessoa_id: int,
    dados: BeneficioPessoaBase,
    session: Session = Depends(get_session),
):
    """
    Registra um benefício para a pessoa (BPC, Bolsa Família, benefício eventual, etc.).
    """
    pessoa = session.get(PessoaRua, pessoa_id)
    if not pessoa:
        raise HTTPException(
            status_code=404,
            detail="Pessoa em situação de rua não encontrada.",
        )

    beneficio = BeneficioPessoa.from_orm(dados)
    beneficio.pessoa_id = pessoa_id

    session.add(beneficio)
    session.commit()
    session.refresh(beneficio)

    return beneficio