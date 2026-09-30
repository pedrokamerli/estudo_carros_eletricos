"""Testo regras pequenas que protegem a automação das datas e do histórico de vendas."""

from pathlib import Path

import pandas as pd

from src.transformation.bronze_to_silver import get_period_from_file_name
from src.transformation.sales_history_to_silver import transform_sales_history


def test_get_period_from_official_fuel_file_name() -> None:
    """Confirmo que eu reconheço o mês e o ano diretamente do nome oficial da SENATRAN."""
    file_path = Path("D_Frota_por_UF_Municipio_COMBUSTIVEL_Setembro_2026.xlsx")

    assert get_period_from_file_name(file_path) == (2026, 9)


def test_sales_history_removes_bom_and_keeps_project_years(tmp_path: Path) -> None:
    """Confirmo que meu tratamento lê CSV com BOM e respeita o recorte de 2024 a 2026."""
    source_file_path = tmp_path / "vendas.csv"
    source_file_path.write_text(
        "\ufeffAno,Modelo,Marca,Categoria,Unidades_Emplacadas\n"
        "2023,Modelo antigo,Marca A,BEV,10\n"
        "2024,Modelo atual,Marca B,BEV,20\n",
        encoding="utf-8",
    )

    result = transform_sales_history(source_file_path)

    assert result["ano_referencia"].tolist() == [2024]
    assert result["unidades_emplacadas"].tolist() == [20]
    assert pd.isna(result.loc[0, "mes_referencia"])
