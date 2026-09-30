"""Carrego as tabelas Silver locais no PostgreSQL e confiro o resultado da carga."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.database.connection import get_connection


# Encontro os Parquets já tratados pela pipeline antes de enviá-los ao banco.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FLEET_PARQUET_PATH = PROJECT_ROOT / "data" / "silver" / "senatran" / "frota_eletrificada.parquet"
TOTAL_FLEET_PARQUET_PATH = PROJECT_ROOT / "data" / "silver" / "senatran" / "frota_total_municipal.parquet"
IBGE_PARQUET_PATH = PROJECT_ROOT / "data" / "silver" / "ibge" / "indicadores_municipais.parquet"

FLEET_COLUMNS = [
    "uf", "municipio", "combustivel_veiculo", "quantidade_veiculos",
    "categoria_eletrificacao", "uf_informada", "capital_da_uf",
    "tipo_localidade", "ano_referencia", "mes_referencia", "fonte",
]
TOTAL_FLEET_COLUMNS = [
    "uf", "municipio", "quantidade_veiculos", "ano_referencia", "mes_referencia", "fonte",
]
IBGE_COLUMNS = [
    "codigo_ibge", "municipio", "uf", "populacao_censo_2022",
    "pib_corrente_mil_reais_2023", "pib_per_capita_aproximado",
    "rendimento_domiciliar_per_capita_medio_2022_reais", "fonte",
]


def to_python_value(value: Any) -> Any:
    """Converto valores do Pandas para tipos simples que o PostgreSQL entende."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def replace_dataframe(dataframe: pd.DataFrame, table_name: str, columns: list[str]) -> None:
    """Atualizo uma tabela Silver gerada pelo projeto com a versão local mais recente."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {table_name};")
            column_list = ", ".join(columns)
            copy_command = f"COPY {table_name} ({column_list}) FROM STDIN"
            with cursor.copy(copy_command) as copy:
                for row in dataframe[columns].itertuples(index=False, name=None):
                    copy.write_row(tuple(to_python_value(value) for value in row))

        # Ao sair do bloco sem erro, a conexão confirma a transação automaticamente.


def create_total_fleet_table() -> None:
    """Crio os schemas e as tabelas Silver geradas pelo projeto quando faltarem."""
    statements = [
        "CREATE SCHEMA IF NOT EXISTS silver;",
        "CREATE SCHEMA IF NOT EXISTS gold;",
        """
        CREATE TABLE IF NOT EXISTS silver.frota_eletrificada (
            uf VARCHAR(30) NOT NULL,
            municipio VARCHAR(100) NOT NULL,
            combustivel_veiculo VARCHAR(80) NOT NULL,
            quantidade_veiculos INTEGER NOT NULL CHECK (quantidade_veiculos >= 0),
            categoria_eletrificacao VARCHAR(50) NOT NULL,
            uf_informada BOOLEAN NOT NULL,
            capital_da_uf VARCHAR(100),
            tipo_localidade VARCHAR(20) NOT NULL,
            ano_referencia SMALLINT NOT NULL CHECK (ano_referencia BETWEEN 2020 AND 2035),
            mes_referencia SMALLINT NOT NULL CHECK (mes_referencia BETWEEN 1 AND 12),
            fonte VARCHAR(30) NOT NULL,
            CONSTRAINT uq_frota_eletrificada_periodo UNIQUE (
                uf, municipio, combustivel_veiculo, ano_referencia, mes_referencia
            )
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS silver.indicadores_municipais_ibge (
            codigo_ibge CHAR(7) PRIMARY KEY,
            municipio VARCHAR(100) NOT NULL,
            uf CHAR(2) NOT NULL,
            populacao_censo_2022 INTEGER NOT NULL CHECK (populacao_censo_2022 > 0),
            pib_corrente_mil_reais_2023 NUMERIC(18, 2) NOT NULL
                CHECK (pib_corrente_mil_reais_2023 >= 0),
            pib_per_capita_aproximado NUMERIC(14, 2) NOT NULL
                CHECK (pib_per_capita_aproximado >= 0),
            rendimento_domiciliar_per_capita_medio_2022_reais NUMERIC(14, 2),
            fonte VARCHAR(150) NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS silver.frota_total_municipal (
            uf VARCHAR(30) NOT NULL,
            municipio VARCHAR(100) NOT NULL,
            quantidade_veiculos BIGINT NOT NULL CHECK (quantidade_veiculos >= 0),
            ano_referencia SMALLINT NOT NULL CHECK (ano_referencia BETWEEN 2020 AND 2035),
            mes_referencia SMALLINT NOT NULL CHECK (mes_referencia BETWEEN 1 AND 12),
            fonte VARCHAR(30) NOT NULL,
            PRIMARY KEY (uf, municipio, ano_referencia, mes_referencia)
        );
        """,
    ]
    with get_connection() as connection:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
            # Atualizo também instalações anteriores, nas quais a tabela já existia.
            cursor.execute(
                "ALTER TABLE silver.indicadores_municipais_ibge "
                "ADD COLUMN IF NOT EXISTS rendimento_domiciliar_per_capita_medio_2022_reais NUMERIC(14, 2);"
            )


def validate_fleet_load(expected_dataframe: pd.DataFrame) -> None:
    """Comparo quantidade de linhas e total de veículos entre Parquet e PostgreSQL."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*), COALESCE(SUM(quantidade_veiculos), 0) "
                "FROM silver.frota_eletrificada;"
            )
            loaded_rows, loaded_total = cursor.fetchone()

    expected_rows = len(expected_dataframe)
    expected_total = int(expected_dataframe["quantidade_veiculos"].sum())
    if loaded_rows != expected_rows or loaded_total != expected_total:
        raise ValueError(
            "A validação da frota falhou: "
            f"esperado {expected_rows:,} linhas e {expected_total:,} veículos; "
            f"encontrado {loaded_rows:,} linhas e {loaded_total:,} veículos."
        )

    print(f"Frota validada: {loaded_rows:,} linhas e {loaded_total:,} veículos.")


def validate_ibge_load(expected_dataframe: pd.DataFrame) -> None:
    """Comparo a quantidade de municípios entre o Parquet e o PostgreSQL."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM silver.indicadores_municipais_ibge;")
            loaded_rows = cursor.fetchone()[0]

    expected_rows = len(expected_dataframe)
    if loaded_rows != expected_rows:
        raise ValueError(
            f"A validação do IBGE falhou: esperado {expected_rows:,}, encontrado {loaded_rows:,}."
        )

    print(f"IBGE validado: {loaded_rows:,} municípios.")


def main() -> None:
    """Leio os Parquets Silver, crio as tabelas e publico uma carga reproduzível."""
    fleet_dataframe = pd.read_parquet(FLEET_PARQUET_PATH)
    total_fleet_dataframe = pd.read_parquet(TOTAL_FLEET_PARQUET_PATH)
    ibge_dataframe = pd.read_parquet(IBGE_PARQUET_PATH).rename(
        columns={"municipio_ibge": "municipio"}
    )

    # A junção dos arquivos do IBGE cria números como 21494.0. A população,
    # porém, é uma contagem de pessoas; por isso a preparo como inteiro antes
    # de enviá-la para a coluna INTEGER do PostgreSQL.
    ibge_dataframe["populacao_censo_2022"] = (
        ibge_dataframe["populacao_censo_2022"].round().astype("Int64")
    )

    create_total_fleet_table()

    print("Carregando frota eletrificada da SENATRAN...")
    replace_dataframe(fleet_dataframe, "silver.frota_eletrificada", FLEET_COLUMNS)
    validate_fleet_load(fleet_dataframe)

    print("Carregando frota total municipal da SENATRAN...")
    replace_dataframe(total_fleet_dataframe, "silver.frota_total_municipal", TOTAL_FLEET_COLUMNS)
    print(f"Frota total validada: {len(total_fleet_dataframe):,} linhas.")

    print("Carregando indicadores municipais do IBGE...")
    replace_dataframe(ibge_dataframe, "silver.indicadores_municipais_ibge", IBGE_COLUMNS)
    validate_ibge_load(ibge_dataframe)

    print("Carga Silver no PostgreSQL concluída com sucesso!")


if __name__ == "__main__":
    # Executo a carga apenas quando chamo este arquivo como módulo do projeto.
    main()
