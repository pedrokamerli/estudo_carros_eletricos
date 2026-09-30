import pytest

from src.quality.senatran_brand_model_quality import validate_columns


def test_brand_model_columns_are_accepted() -> None:
    # Confirmo que a estrutura oficial esperada passa pela validação.
    validate_columns(
        [
            "UF",
            "Município",
            "Marca Modelo",
            "Ano Fabricação Veículo CRV",
            "Qtd. Veículos",
        ]
    )


def test_brand_model_columns_reject_missing_field() -> None:
    # Confirmo que não seguimos se o arquivo não tiver a marca/modelo.
    with pytest.raises(ValueError, match="Marca Modelo"):
        validate_columns(["UF", "Município", "Qtd. Veículos"])
