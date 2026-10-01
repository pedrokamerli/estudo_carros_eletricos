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


def build_fleet_evolution_gold(silver_dataframe: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Crio a evolução nacional e estadual da frota, sem confundir estoque com emplacamentos."""
    national = silver_dataframe.groupby(
        ["ano_referencia", "mes_referencia"], as_index=False
    )["quantidade_veiculos"].sum().sort_values(["ano_referencia", "mes_referencia"])
    national["crescimento_mensal_percentual"] = national["quantidade_veiculos"].pct_change() * 100

    states = silver_dataframe.groupby(
        ["ano_referencia", "mes_referencia", "uf"], as_index=False
    )["quantidade_veiculos"].sum().sort_values(["uf", "ano_referencia", "mes_referencia"])
    states["crescimento_mensal_percentual"] = states.groupby("uf")["quantidade_veiculos"].pct_change() * 100
    return national, states


def build_market_gold(market_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Crio o ranking mensal de marcas e modelos do dataset fornecido pelo usuário."""
    return market_dataframe.groupby(
        ["ano_referencia", "mes_referencia", "marca", "modelo", "categoria_eletrificacao"],
        as_index=False,
    )["quantidade_emplacada"].sum().sort_values(
        ["ano_referencia", "mes_referencia", "quantidade_emplacada"],
        ascending=[True, True, False],
    )


def build_market_evolution_gold(market_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Agrego emplacamentos do dataset fornecido, mantendo a origem explícita na tabela Gold."""
    return market_dataframe.groupby(
        ["ano_referencia", "mes_referencia", "categoria_eletrificacao"], as_index=False
    )["quantidade_emplacada"].sum().sort_values(
        ["ano_referencia", "mes_referencia", "categoria_eletrificacao"]
    )


def build_opportunity_gold(penetration_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Marco municípios com PIB e renda altos e baixa penetração como candidatos a investigar."""
    valid = penetration_dataframe.dropna(
        subset=[
            "pib_per_capita_aproximado",
            "rendimento_domiciliar_per_capita_medio_2022_reais",
            "veiculos_eletrificados_por_100_mil_habitantes",
        ]
    ).copy()
    high_income_threshold = valid["pib_per_capita_aproximado"].quantile(0.75)
    high_household_income_threshold = valid[
        "rendimento_domiciliar_per_capita_medio_2022_reais"
    ].quantile(0.75)
    low_penetration_threshold = valid["veiculos_eletrificados_por_100_mil_habitantes"].quantile(0.25)
    valid["oportunidade_preliminar"] = (
        (valid["pib_per_capita_aproximado"] >= high_income_threshold)
        & (valid["rendimento_domiciliar_per_capita_medio_2022_reais"] >= high_household_income_threshold)
        & (valid["veiculos_eletrificados_por_100_mil_habitantes"] <= low_penetration_threshold)
    )
    return valid


def build_municipal_correlation_gold(penetration_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Calculo associações municipais exploratórias, sem tratá-las como causa ou previsão."""
    socioeconomic_columns = {
        "pib_per_capita_aproximado": "PIB per capita aproximado (R$)",
        "rendimento_domiciliar_per_capita_medio_2022_reais": "Renda domiciliar per capita média (R$)",
        "populacao_censo_2022": "População do Censo 2022 (pessoas)",
    }
    adoption_columns = {
        "veiculos_eletrificados_por_100_mil_habitantes": "Eletrificados por 100 mil habitantes",
        "participacao_eletrificada_na_frota_percentual": "Participação eletrificada na frota (%)",
    }
    latest = penetration_dataframe[
        ["ano_referencia_frota", "mes_referencia_frota"]
    ].drop_duplicates().sort_values(
        ["ano_referencia_frota", "mes_referencia_frota"]
    ).iloc[-1]
    rows: list[dict[str, object]] = []

    for socioeconomic_column, socioeconomic_label in socioeconomic_columns.items():
        for adoption_column, adoption_label in adoption_columns.items():
            pair = penetration_dataframe[[socioeconomic_column, adoption_column]].apply(
                pd.to_numeric, errors="coerce"
            ).replace([float("inf"), float("-inf")], float("nan")).dropna()
            for method in ("pearson", "spearman"):
                if method == "spearman":
                    # Spearman equivale à correlação de Pearson calculada sobre os postos.
                    first_rank = pair[socioeconomic_column].rank(method="average")
                    second_rank = pair[adoption_column].rank(method="average")
                    coefficient = first_rank.corr(second_rank, method="pearson")
                else:
                    coefficient = pair[socioeconomic_column].corr(
                        pair[adoption_column], method="pearson"
                    )
                rows.append(
                    {
                        "variavel_socioeconomica": socioeconomic_label,
                        "indicador_adocao": adoption_label,
                        "metodo": method,
                        "coeficiente_correlacao": coefficient,
                        "municipios_analisados": len(pair),
                        "ano_referencia_frota": int(latest["ano_referencia_frota"]),
                        "mes_referencia_frota": int(latest["mes_referencia_frota"]),
                    }
                )
    return pd.DataFrame(rows)


def build_municipal_penetration_gold(
    silver_dataframe: pd.DataFrame,
    total_fleet_dataframe: pd.DataFrame,
    ibge_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Uno frota elétrica, frota total e indicadores do IBGE no mês mais recente."""
    latest_period = silver_dataframe[["ano_referencia", "mes_referencia"]].drop_duplicates()
    latest_period = latest_period.sort_values(["ano_referencia", "mes_referencia"]).iloc[-1]
    latest_electric = silver_dataframe.loc[
        (silver_dataframe["ano_referencia"] == latest_period["ano_referencia"])
        & (silver_dataframe["mes_referencia"] == latest_period["mes_referencia"])
    ].groupby(["uf", "municipio"], as_index=False)["quantidade_veiculos"].sum()
    latest_total = total_fleet_dataframe.loc[
        (total_fleet_dataframe["ano_referencia"] == latest_period["ano_referencia"])
        & (total_fleet_dataframe["mes_referencia"] == latest_period["mes_referencia"])
    ][["uf", "municipio", "quantidade_veiculos"]].rename(
        columns={"quantidade_veiculos": "frota_total_veiculos"}
    )
    # Começo pela frota total para incluir localidades sem registros eletrificados.
    # Só atribuo zero quando o município existe no arquivo completo da mesma competência.
    orphan = latest_electric.merge(latest_total, on=["uf", "municipio"], how="left", indicator=True)
    if orphan["_merge"].eq("left_only").any():
        raise ValueError("Município eletrificado sem frota total na mesma competência.")
    latest_fleet = latest_total.merge(latest_electric, on=["uf", "municipio"],
                                      how="left", validate="one_to_one")
    latest_fleet["quantidade_veiculos"] = latest_fleet["quantidade_veiculos"].fillna(0).astype("int64")
    if (latest_fleet["frota_total_veiculos"] <= 0).any():
        raise ValueError("A frota total municipal precisa ser positiva para calcular participação.")
    latest_fleet["municipio_chave"] = latest_fleet["municipio"].map(normalize_municipality_name)
    # Converto o nome estadual da SENATRAN para a sigla usada pela dimensão oficial do IBGE.
    latest_fleet["uf_ibge"] = latest_fleet["uf"].map(UF_ABBREVIATION_BY_NAME)
    result = latest_fleet.merge(
        ibge_dataframe[
            [
                "codigo_ibge", "uf", "municipio_chave", "populacao_censo_2022",
                "pib_per_capita_aproximado", "rendimento_domiciliar_per_capita_medio_2022_reais",
            ]
        ].rename(columns={"uf": "uf_ibge"}),
        on=["uf_ibge", "municipio_chave"],
        how="left",
        validate="many_to_one",
    )
    result["veiculos_eletrificados_por_100_mil_habitantes"] = (
        result["quantidade_veiculos"] / result["populacao_censo_2022"] * 100_000
    )
    result["participacao_eletrificada_na_frota_percentual"] = (
        result["quantidade_veiculos"] / result["frota_total_veiculos"] * 100
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

    national_evolution, state_evolution = build_fleet_evolution_gold(senatran_dataframe)
    save_gold_table(national_evolution, "evolucao_frota_nacional")
    save_gold_table(state_evolution, "evolucao_frota_por_estado")
    print(f"Gold criada: evolucao_frota_nacional ({len(national_evolution)} linhas)")
    print(f"Gold criada: evolucao_frota_por_estado ({len(state_evolution)} linhas)")

    if MARKET_SILVER_PATH.exists():
        market_dataframe = pd.read_parquet(MARKET_SILVER_PATH)
        ranking = build_market_gold(market_dataframe)
        save_gold_table(ranking, "ranking_marcas_modelos_fornecido")
        print(f"Gold criada: ranking_marcas_modelos_fornecido ({len(ranking)} linhas)")
        market_evolution = build_market_evolution_gold(market_dataframe)
        save_gold_table(market_evolution, "emplacamentos_mensais_fornecidos")
        print(f"Gold criada: emplacamentos_mensais_fornecidos ({len(market_evolution)} linhas)")

    if IBGE_SILVER_PATH.exists():
        ibge_dataframe = pd.read_parquet(IBGE_SILVER_PATH)
        total_fleet_path = PROJECT_ROOT / "data" / "silver" / "senatran" / "frota_total_municipal.parquet"
        total_fleet_dataframe = pd.read_parquet(total_fleet_path)
        penetration = build_municipal_penetration_gold(
            senatran_dataframe, total_fleet_dataframe, ibge_dataframe
        )
        save_gold_table(penetration, "penetracao_municipal_ibge")
        matched = int(penetration["codigo_ibge"].notna().sum())
        print(f"Gold criada: penetracao_municipal_ibge ({len(penetration)} linhas; {matched} municípios cruzados)")
        opportunities = build_opportunity_gold(penetration)
        save_gold_table(opportunities, "oportunidade_municipal_preliminar")
        print(f"Gold criada: oportunidade_municipal_preliminar ({len(opportunities)} linhas)")
        correlations = build_municipal_correlation_gold(penetration)
        save_gold_table(correlations, "correlacao_municipal_socioeconomia_adocao")
        print(f"Gold criada: correlacao_municipal_socioeconomia_adocao ({len(correlations)} linhas)")


if __name__ == "__main__":
    # Eu gero a Gold somente depois que as Silver necessárias já existem.
    main()
