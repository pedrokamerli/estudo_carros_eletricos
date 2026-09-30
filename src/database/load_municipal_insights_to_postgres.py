"""Levo ao PostgreSQL as análises municipais que cruzam SENATRAN e IBGE."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.database.connection import get_connection


# Estes arquivos são calculados pela transformação Silver para Gold local.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PENETRATION_PATH = PROJECT_ROOT / "data" / "gold" / "penetracao_municipal_ibge.parquet"
OPPORTUNITY_PATH = PROJECT_ROOT / "data" / "gold" / "oportunidade_municipal_preliminar.parquet"

PENETRATION_COLUMNS = [
    "uf", "municipio", "quantidade_veiculos", "frota_total_veiculos", "municipio_chave", "uf_ibge",
    "codigo_ibge", "populacao_censo_2022", "pib_per_capita_aproximado",
    "rendimento_domiciliar_per_capita_medio_2022_reais",
    "veiculos_eletrificados_por_100_mil_habitantes", "participacao_eletrificada_na_frota_percentual", "ano_referencia_frota",
    "mes_referencia_frota",
]
OPPORTUNITY_COLUMNS = PENETRATION_COLUMNS + ["oportunidade_preliminar"]


def to_python_value(value: Any) -> Any:
    """Converto valores do Pandas para tipos que o PostgreSQL aceita no COPY."""
    if pd.isna(value):
        return None
    return value.item() if hasattr(value, "item") else value


def create_gold_tables() -> None:
    """Crio as duas tabelas analíticas caso elas ainda não existam."""
    statements = [
        """
        CREATE TABLE IF NOT EXISTS gold.penetracao_municipal_ibge (
            uf VARCHAR(30) NOT NULL,
            municipio VARCHAR(100) NOT NULL,
            quantidade_veiculos BIGINT NOT NULL,
            frota_total_veiculos BIGINT NOT NULL,
            municipio_chave VARCHAR(120) NOT NULL,
            uf_ibge CHAR(2),
            codigo_ibge CHAR(7),
            populacao_censo_2022 INTEGER,
            pib_per_capita_aproximado NUMERIC(14, 2),
            rendimento_domiciliar_per_capita_medio_2022_reais NUMERIC(14, 2),
            veiculos_eletrificados_por_100_mil_habitantes NUMERIC(16, 4),
            participacao_eletrificada_na_frota_percentual NUMERIC(12, 6),
            ano_referencia_frota SMALLINT NOT NULL,
            mes_referencia_frota SMALLINT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS gold.oportunidade_municipal_preliminar (
            uf VARCHAR(30) NOT NULL,
            municipio VARCHAR(100) NOT NULL,
            quantidade_veiculos BIGINT NOT NULL,
            frota_total_veiculos BIGINT NOT NULL,
            municipio_chave VARCHAR(120) NOT NULL,
            uf_ibge CHAR(2),
            codigo_ibge CHAR(7),
            populacao_censo_2022 INTEGER,
            pib_per_capita_aproximado NUMERIC(14, 2),
            rendimento_domiciliar_per_capita_medio_2022_reais NUMERIC(14, 2),
            veiculos_eletrificados_por_100_mil_habitantes NUMERIC(16, 4),
            participacao_eletrificada_na_frota_percentual NUMERIC(12, 6),
            ano_referencia_frota SMALLINT NOT NULL,
            mes_referencia_frota SMALLINT NOT NULL,
            oportunidade_preliminar BOOLEAN NOT NULL
        );
        """,
    ]
    with get_connection() as connection:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
            for table_name in (
                "gold.penetracao_municipal_ibge",
                "gold.oportunidade_municipal_preliminar",
            ):
                cursor.execute(
                    f"ALTER TABLE {table_name} "
                    "ADD COLUMN IF NOT EXISTS rendimento_domiciliar_per_capita_medio_2022_reais NUMERIC(14, 2);"
                )


def replace_table(dataframe: pd.DataFrame, table_name: str, columns: list[str]) -> None:
    """Atualizo uma tabela Gold derivada, sem mexer nas tabelas Silver de origem."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {table_name};")
            command = f"COPY {table_name} ({', '.join(columns)}) FROM STDIN"
            with cursor.copy(command) as copy:
                for row in dataframe[columns].itertuples(index=False, name=None):
                    copy.write_row(tuple(to_python_value(value) for value in row))


def main() -> None:
    """Confiro os arquivos Gold locais e publico seus resultados no PostgreSQL."""
    if not PENETRATION_PATH.exists() or not OPPORTUNITY_PATH.exists():
        raise FileNotFoundError(
            "As análises municipais ainda não existem. Execute primeiro: "
            "python -m src.transformation.silver_to_gold"
        )

    penetration_dataframe = pd.read_parquet(PENETRATION_PATH)
    opportunity_dataframe = pd.read_parquet(OPPORTUNITY_PATH)
    # O SIDRA chega como float após a combinação das duas tabelas, mas população
    # é uma contagem inteira e a coluna Gold foi definida como INTEGER.
    for dataframe in (penetration_dataframe, opportunity_dataframe):
        dataframe["populacao_censo_2022"] = (
            dataframe["populacao_censo_2022"].round().astype("Int64")
        )
    create_gold_tables()
    replace_table(penetration_dataframe, "gold.penetracao_municipal_ibge", PENETRATION_COLUMNS)
    replace_table(opportunity_dataframe, "gold.oportunidade_municipal_preliminar", OPPORTUNITY_COLUMNS)

    print(f"Penetração municipal carregada: {len(penetration_dataframe):,} linhas.")
    print(f"Oportunidades preliminares carregadas: {len(opportunity_dataframe):,} linhas.")


if __name__ == "__main__":
    # Eu atualizo estas análises somente quando rodo este módulo de propósito.
    main()
