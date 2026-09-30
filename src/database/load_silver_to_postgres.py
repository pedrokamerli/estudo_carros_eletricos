"""Carrego as tabelas Silver locais no PostgreSQL e confiro o resultado da carga."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.database.connection import get_connection


# Encontro os Parquets já tratados pela pipeline antes de enviá-los ao banco.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FLEET_PARQUET_PATH = PROJECT_ROOT / "data" / "silver" / "senatran" / "frota_eletrificada.parquet"
IBGE_PARQUET_PATH = PROJECT_ROOT / "data" / "silver" / "ibge" / "indicadores_municipais.parquet"

FLEET_COLUMNS = [
    "uf", "municipio", "combustivel_veiculo", "quantidade_veiculos",
    "categoria_eletrificacao", "uf_informada", "capital_da_uf",
    "tipo_localidade", "ano_referencia", "mes_referencia", "fonte",
]
IBGE_COLUMNS = [
    "codigo_ibge", "municipio", "uf", "populacao_censo_2022",
    "pib_corrente_mil_reais_2023", "pib_per_capita_aproximado", "fonte",
]


def to_python_value(value: Any) -> Any:
    """Converto valores do Pandas para tipos simples que o PostgreSQL entende."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def copy_dataframe(dataframe: pd.DataFrame, table_name: str, columns: list[str]) -> bool:
    """Copio um DataFrame em lote e reaproveito uma carga já existente sem duplicá-la."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            existing_rows = cursor.fetchone()[0]
            if existing_rows > 0:
                print(
                    f"A tabela {table_name} já possui {existing_rows:,} linhas. "
                    "Vou apenas validar a carga existente, sem duplicar registros."
                )
                return False

            column_list = ", ".join(columns)
            copy_command = f"COPY {table_name} ({column_list}) FROM STDIN"
            with cursor.copy(copy_command) as copy:
                for row in dataframe[columns].itertuples(index=False, name=None):
                    copy.write_row(tuple(to_python_value(value) for value in row))

        # Ao sair do bloco sem erro, a conexão confirma a transação automaticamente.
    return True


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
    """Leio os dois Parquets Silver, carrego cada tabela e valido o resultado final."""
    fleet_dataframe = pd.read_parquet(FLEET_PARQUET_PATH)
    ibge_dataframe = pd.read_parquet(IBGE_PARQUET_PATH).rename(
        columns={"municipio_ibge": "municipio"}
    )

    # A junção dos arquivos do IBGE cria números como 21494.0. A população,
    # porém, é uma contagem de pessoas; por isso a preparo como inteiro antes
    # de enviá-la para a coluna INTEGER do PostgreSQL.
    ibge_dataframe["populacao_censo_2022"] = (
        ibge_dataframe["populacao_censo_2022"].round().astype("Int64")
    )

    print("Carregando frota eletrificada da SENATRAN...")
    copy_dataframe(fleet_dataframe, "silver.frota_eletrificada", FLEET_COLUMNS)
    validate_fleet_load(fleet_dataframe)

    print("Carregando indicadores municipais do IBGE...")
    copy_dataframe(ibge_dataframe, "silver.indicadores_municipais_ibge", IBGE_COLUMNS)
    validate_ibge_load(ibge_dataframe)

    print("Carga Silver no PostgreSQL concluída com sucesso!")


if __name__ == "__main__":
    # Executo a carga apenas quando chamo este arquivo como módulo do projeto.
    main()
