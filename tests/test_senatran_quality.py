import pandas as pd
import pytest

from src.quality.senatran_quality import assess_bronze_dataframe


def valid_dataframe() -> pd.DataFrame:
    # Crio uma amostra mínima que representa uma linha válida da fonte SENATRAN.
    return pd.DataFrame(
        {
            "UF": ["SAO PAULO"],
            "Município": ["SAO PAULO"],
            "Combustível Veículo": ["ELETRICO"],
            "Qtd. Veículos": [10],
        }
    )


def test_quality_report_approves_valid_data() -> None:
    # Confirmo que uma amostra válida é aprovada pela regra de qualidade.
    report = assess_bronze_dataframe(valid_dataframe())

    assert report["aprovado"] is True
    assert report["linhas_com_quantidade_invalida"] == 0


def test_quality_report_detects_invalid_quantity() -> None:
    # Confirmo que quantidade igual a zero é detectada como problema crítico.
    dataframe = valid_dataframe()
    dataframe.loc[0, "Qtd. Veículos"] = 0

    report = assess_bronze_dataframe(dataframe)

    assert report["aprovado"] is False
    assert report["linhas_com_quantidade_invalida"] == 1


def test_quality_report_rejects_missing_required_column() -> None:
    # Confirmo que a pipeline não segue se a fonte perder uma coluna essencial.
    dataframe = valid_dataframe().drop(columns="UF")

    with pytest.raises(ValueError, match="colunas obrigatórias"):
        assess_bronze_dataframe(dataframe)
