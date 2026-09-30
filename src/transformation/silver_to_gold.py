"""Crio tabelas Gold agregadas para responder às primeiras perguntas do projeto."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.quality.silver_quality import assess_senatran_silver
from src.transformation.ibge_bronze_to_silver import normalize_municipality_name
from src.utils.capitals import UF_ABBREVIATION_BY_NAME

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SENATRAN_SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "senatran" / "frota_eletrificada.parquet"
MARKET_SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "market" / "mercado_ev_fornecido.parquet"
IBGE_SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "ibge" / "indicadores_municipais.parquet"
GOLD_PATH = PROJECT_ROOT / "data" / "gold"


def save_gold_table(dataframe: pd.DataFrame, table_name: str) -> None:
    """Salvo cada resposta analítica em uma tabela Gold separada e fácil de achar."""
    output_path = GOLD_PATH / f"{table_name}.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_parquet(output_path, index=False)


def build_senatran_gold(silver_dataframe: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Crio respostas de frota por estado, município, localidade e categoria."""
    period_columns = ["ano_referencia", "mes_referencia"]
    quantity_column = "quantidade_veiculos"
    return {
        "frota_por_estado": silver_dataframe.groupby(
            period_columns + ["uf"], as_index=False
        )[quantity_column].sum(),
        "frota_por_municipio": silver_dataframe.groupby(
            period_columns + ["uf", "municipio"], as_index=False
        )[quantity_column].sum(),
        "frota_capital_vs_interior": silver_dataframe.groupby(
            period_columns + ["tipo_localidade"], as_index=False
        )[quantity_column].sum(),
        "frota_por_categoria_eletrificacao": silver_dataframe.groupby(
            period_columns + ["categoria_eletrificacao"], as_index=False
        )[quantity_column].sum(),
    }


def build_market_gold(market_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Crio o ranking mensal de marcas e modelos do dataset fornecido pelo usuário."""
    return market_dataframe.groupby(
        ["ano_referencia", "mes_referencia", "marca", "modelo", "categoria_eletrificacao"],
        as_index=False,
    )["quantidade_emplacada"].sum().sort_values(
        ["ano_referencia", "mes_referencia", "quantidade_emplacada"],
        ascending=[True, True, False],
    )


def build_municipal_penetration_gold(silver_dataframe: pd.DataFrame, ibge_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Uno a fotografia mais recente da frota aos indicadores econômicos oficiais disponíveis."""
    latest_period = silver_dataframe[["ano_referencia", "mes_referencia"]].drop_duplicates()
    latest_period = latest_period.sort_values(["ano_referencia", "mes_referencia"]).iloc[-1]
    latest_fleet = silver_dataframe.loc[
        (silver_dataframe["ano_referencia"] == latest_period["ano_referencia"])
        & (silver_dataframe["mes_referencia"] == latest_period["mes_referencia"])
    ].groupby(["uf", "municipio"], as_index=False)["quantidade_veiculos"].sum()

    latest_fleet["municipio_chave"] = latest_fleet["municipio"].map(normalize_municipality_name)
    # Converto o nome estadual da SENATRAN para a sigla usada pela dimensão oficial do IBGE.
    latest_fleet["uf_ibge"] = latest_fleet["uf"].map(UF_ABBREVIATION_BY_NAME)
    result = latest_fleet.merge(
        ibge_dataframe[
            ["codigo_ibge", "uf", "municipio_chave", "populacao_censo_2022", "pib_per_capita_aproximado"]
        ].rename(columns={"uf": "uf_ibge"}),
        on=["uf_ibge", "municipio_chave"],
        how="left",
    )
    result["veiculos_eletrificados_por_100_mil_habitantes"] = (
        result["quantidade_veiculos"] / result["populacao_censo_2022"] * 100_000
    )
    result["ano_referencia_frota"] = latest_period["ano_referencia"]
    result["mes_referencia_frota"] = latest_period["mes_referencia"]
    return result


def main() -> None:
    """Valido a Silver antes de gerar qualquer tabela Gold derivada dela."""
    senatran_dataframe = pd.read_parquet(SENATRAN_SILVER_PATH)
    quality_report = assess_senatran_silver(senatran_dataframe)
    if not quality_report["aprovado"]:
        raise ValueError(f"Silver SENATRAN inválida: {quality_report}")

    for table_name, dataframe in build_senatran_gold(senatran_dataframe).items():
        save_gold_table(dataframe, table_name)
        print(f"Gold criada: {table_name} ({len(dataframe)} linhas)")

    if MARKET_SILVER_PATH.exists():
        market_dataframe = pd.read_parquet(MARKET_SILVER_PATH)
        ranking = build_market_gold(market_dataframe)
        save_gold_table(ranking, "ranking_marcas_modelos_fornecido")
        print(f"Gold criada: ranking_marcas_modelos_fornecido ({len(ranking)} linhas)")

    if IBGE_SILVER_PATH.exists():
        ibge_dataframe = pd.read_parquet(IBGE_SILVER_PATH)
        penetration = build_municipal_penetration_gold(senatran_dataframe, ibge_dataframe)
        save_gold_table(penetration, "penetracao_municipal_ibge")
        matched = int(penetration["codigo_ibge"].notna().sum())
        print(f"Gold criada: penetracao_municipal_ibge ({len(penetration)} linhas; {matched} municípios cruzados)")


if __name__ == "__main__":
    # Eu gero a Gold somente depois que as Silver necessárias já existem.
    main()
