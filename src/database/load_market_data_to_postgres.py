"""Carrego no PostgreSQL os dados de mercado fornecidos para análises de marca e modelo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.database.connection import get_connection


# Encontro os dois arquivos já tratados sem depender de caminhos do computador.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MARKET_PATH = PROJECT_ROOT / "data" / "silver" / "market" / "mercado_ev_fornecido.parquet"
HISTORY_PATH = PROJECT_ROOT / "data" / "silver" / "market" / "historico_vendas_ev_brasil.parquet"

MARKET_COLUMNS = [
    "ano_referencia", "frota_total_estimada", "marca", "mes_nome", "modelo",
    "municipio", "pib_per_capita", "populacao_estimada", "quantidade_emplacada",
    "regiao", "categoria_eletrificacao", "tipo_localidade", "uf", "mes_referencia",
    "fonte", "origem_oficial_confirmada",
]
HISTORY_COLUMNS = [
    "ano_referencia", "categoria_eletrificacao", "marca", "modelo",
    "unidades_emplacadas", "mes_referencia", "fonte",
]


def to_python_value(value: Any) -> Any:
    """Converto valores do Pandas para tipos simples aceitos pelo PostgreSQL."""
    if pd.isna(value):
        return None
    return value.item() if hasattr(value, "item") else value


def create_silver_tables() -> None:
    """Crio as tabelas Silver de mercado caso esta seja a primeira carga."""
    statements = [
        """
        CREATE TABLE IF NOT EXISTS silver.mercado_ev_fornecido (
            id BIGSERIAL PRIMARY KEY,
            ano_referencia SMALLINT NOT NULL,
            frota_total_estimada BIGINT,
            marca VARCHAR(100),
            mes_nome VARCHAR(20),
            modelo VARCHAR(150),
            municipio VARCHAR(100),
            pib_per_capita NUMERIC(14, 2),
            populacao_estimada BIGINT,
            quantidade_emplacada INTEGER NOT NULL CHECK (quantidade_emplacada >= 0),
            regiao VARCHAR(30),
            categoria_eletrificacao VARCHAR(50),
            tipo_localidade VARCHAR(30),
            uf VARCHAR(30),
            mes_referencia SMALLINT,
            fonte VARCHAR(150) NOT NULL,
            origem_oficial_confirmada BOOLEAN NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS silver.historico_vendas_ev_fornecido (
            id BIGSERIAL PRIMARY KEY,
            ano_referencia SMALLINT NOT NULL,
            categoria_eletrificacao VARCHAR(50),
            marca VARCHAR(100),
            modelo VARCHAR(150),
            unidades_emplacadas INTEGER NOT NULL CHECK (unidades_emplacadas >= 0),
            mes_referencia SMALLINT,
            fonte VARCHAR(150) NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
    ]
    with get_connection() as connection:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)


def copy_dataframe(dataframe: pd.DataFrame, table_name: str, columns: list[str]) -> None:
    """Substituo a carga anterior pela versão atual do Parquet tratado."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;")
            copy_command = f"COPY {table_name} ({', '.join(columns)}) FROM STDIN"
            with cursor.copy(copy_command) as copy:
                for row in dataframe[columns].itertuples(index=False, name=None):
                    copy.write_row(tuple(to_python_value(value) for value in row))


def main() -> None:
    """Leio os Parquets fornecidos, adequo contagens e os envio para a Silver."""
    market_dataframe = pd.read_parquet(MARKET_PATH)
    history_dataframe = pd.read_parquet(HISTORY_PATH)

    # Eu trato estas três colunas como contagens, portanto elas não podem sair
    # do Pandas como valores decimais do tipo 1000.0.
    for column in ["frota_total_estimada", "populacao_estimada", "quantidade_emplacada"]:
        market_dataframe[column] = pd.to_numeric(market_dataframe[column]).round().astype("Int64")
    history_dataframe["unidades_emplacadas"] = (
        pd.to_numeric(history_dataframe["unidades_emplacadas"]).round().astype("Int64")
    )

    create_silver_tables()
    copy_dataframe(market_dataframe, "silver.mercado_ev_fornecido", MARKET_COLUMNS)
    copy_dataframe(history_dataframe, "silver.historico_vendas_ev_fornecido", HISTORY_COLUMNS)

    print(f"Mercado carregado: {len(market_dataframe):,} linhas.")
    print(f"Histórico de vendas carregado: {len(history_dataframe):,} linhas.")
    print("Atenção: estes arquivos permanecem identificados como dados fornecidos pelo usuário.")


if __name__ == "__main__":
    # Eu executo a carga apenas quando chamo este arquivo diretamente.
    main()
