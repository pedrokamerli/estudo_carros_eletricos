from src.utils.electrification import CATEGORY_BY_FUEL


def test_hybrid_categories_are_included() -> None:
    # Confirmo que as duas categorias híbridas entram na regra de eletrificação.
    assert CATEGORY_BY_FUEL["HIBRIDO"] == "hibrido"
    assert CATEGORY_BY_FUEL["HIBRIDO PLUG-IN"] == "hibrido_plug_in"


def test_non_electrified_fuel_is_not_included() -> None:
    # Confirmo que um combustível convencional não é classificado por engano.
    assert "DIESEL" not in CATEGORY_BY_FUEL
