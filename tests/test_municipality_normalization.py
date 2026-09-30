"""Testo as chaves usadas para cruzar SENATRAN e IBGE sem depender da grafia original."""

from src.transformation.ibge_bronze_to_silver import normalize_municipality_name
from src.utils.capitals import UF_ABBREVIATION_BY_NAME


def test_normalize_municipality_name_removes_accents() -> None:
    """Confirmo que nomes com acento podem ser comparados com a grafia da SENATRAN."""
    assert normalize_municipality_name("São Paulo") == "SAO PAULO"


def test_state_name_maps_to_ibge_abbreviation() -> None:
    """Confirmo que a UF por extenso da SENATRAN chega na sigla usada pelo IBGE."""
    assert UF_ABBREVIATION_BY_NAME["SAO PAULO"] == "SP"
