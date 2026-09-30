"""Testo as regras que impedem uma Silver inválida de chegar à Gold."""

import pandas as pd

from src.quality.silver_quality import assess_senatran_silver


def make_valid_silver_dataframe() -> pd.DataFrame:
    """Monto uma Silver mínima válida para isolar as regras de qualidade nos testes."""
    return pd.DataFrame(
        {
            "uf": ["SAO PAULO"],
            "municipio": ["SAO PAULO"],
            "combustivel_veiculo": ["ELETRICO"],
            "quantidade_veiculos": [10],
            "categoria_eletrificacao": ["componente eletrico"],
            "uf_informada": [True],
            "tipo_localidade": ["capital"],
            "ano_referencia": [2025],
            "mes_referencia": [12],
            "fonte": ["SENATRAN"],
        }
    )


def test_silver_quality_approves_valid_dataframe() -> None:
    """Confirmo que uma Silver válida passa e guarda seu total processado."""
    report = assess_senatran_silver(make_valid_silver_dataframe())

    assert report["aprovado"] is True
    assert report["total_processado"] == 10


def test_silver_quality_rejects_negative_quantities() -> None:
    """Confirmo que não deixo quantidades negativas seguirem para a Gold."""
    dataframe = make_valid_silver_dataframe()
    dataframe.loc[0, "quantidade_veiculos"] = -1

    report = assess_senatran_silver(dataframe)

    assert report["aprovado"] is False
    assert report["quantidades_negativas"] == 1
