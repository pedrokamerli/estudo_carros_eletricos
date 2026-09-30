"""Carrego os dados de emplacamentos e marcas FENABRAVE na Silver do PostgreSQL."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.database.connection import get_connection


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "fenabrave"
MONTHLY_PATH = SILVER_PATH / "emplacamentos_mensais.parquet"
BRANDS_PATH = SILVER_PATH / "ranking_marcas_mensal.parquet"

MONTHLY_COLUMNS = [
    "ano_referencia", "mes_referencia", "categoria_fenabrave", "emplacamentos_mes",
    "emplacamentos_mes_anterior", "emplacamentos_acumulado_ano",
    "emplacamentos_mes_ano_anterior", "emplacamentos_acumulado_ano_anterior",
    "segmento_veiculos", "pagina_pdf", "url_fonte", "metodo_extracao",
]
BRAND_COLUMNS = [
    "ano_referencia", "mes_referencia", "categoria_fenabrave", "posicao", "marca",
    "quantidade_emplacada", "participacao_percentual", "segmento_veiculos", "pagina_pdf",
    "url_fonte", "metodo_extracao",
]


def to_python_value(value: Any) -> Any:
    """Converto os escalares do Pandas para tipos simples aceitos pelo driver."""
    if pd.isna(value):
        return None
    return value.item() if hasattr(value, "item") else value


def create_tables() -> None:
    """Crio as tabelas de fonte separadas para não confundir com ABVE ou SENATRAN."""
    statements = [
        "CREATE SCHEMA IF NOT EXISTS silver;",
        "CREATE SCHEMA IF NOT EXISTS gold;",
        """
        CREATE TABLE IF NOT EXISTS silver.fenabrave_emplacamentos_mensais (
            ano_referencia SMALLINT NOT NULL CHECK (ano_referencia BETWEEN 2024 AND 2035),
            mes_referencia SMALLINT NOT NULL CHECK (mes_referencia BETWEEN 1 AND 12),
            categoria_fenabrave VARCHAR(20) NOT NULL CHECK (categoria_fenabrave IN ('hibridos', 'eletricos')),
            emplacamentos_mes BIGINT NOT NULL CHECK (emplacamentos_mes >= 0),
            emplacamentos_mes_anterior BIGINT CHECK (emplacamentos_mes_anterior >= 0),
            emplacamentos_acumulado_ano BIGINT CHECK (emplacamentos_acumulado_ano >= 0),
            emplacamentos_mes_ano_anterior BIGINT CHECK (emplacamentos_mes_ano_anterior >= 0),
            emplacamentos_acumulado_ano_anterior BIGINT CHECK (emplacamentos_acumulado_ano_anterior >= 0),
            segmento_veiculos VARCHAR(40) NOT NULL,
            pagina_pdf SMALLINT NOT NULL,
            url_fonte TEXT NOT NULL,
            metodo_extracao VARCHAR(40) NOT NULL,
            PRIMARY KEY (ano_referencia, mes_referencia, categoria_fenabrave, segmento_veiculos)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS silver.fenabrave_marcas_mensais (
            ano_referencia SMALLINT NOT NULL CHECK (ano_referencia BETWEEN 2024 AND 2035),
            mes_referencia SMALLINT NOT NULL CHECK (mes_referencia BETWEEN 1 AND 12),
            categoria_fenabrave VARCHAR(20) NOT NULL CHECK (categoria_fenabrave IN ('hibridos', 'eletricos')),
            posicao SMALLINT NOT NULL CHECK (posicao > 0),
            marca VARCHAR(100) NOT NULL,
            quantidade_emplacada BIGINT NOT NULL CHECK (quantidade_emplacada >= 0),
            participacao_percentual NUMERIC(8, 4) NOT NULL CHECK (participacao_percentual BETWEEN 0 AND 100),
            segmento_veiculos VARCHAR(40) NOT NULL,
            pagina_pdf SMALLINT NOT NULL,
            url_fonte TEXT NOT NULL,
            metodo_extracao VARCHAR(40) NOT NULL,
            PRIMARY KEY (ano_referencia, mes_referencia, categoria_fenabrave, posicao, segmento_veiculos)
        );
        """,
        "ALTER TABLE silver.fenabrave_emplacamentos_mensais ADD COLUMN IF NOT EXISTS metodo_extracao VARCHAR(40);",
        "ALTER TABLE silver.fenabrave_marcas_mensais ADD COLUMN IF NOT EXISTS metodo_extracao VARCHAR(40);",
    ]
    with get_connection() as connection:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)


def replace_table(dataframe: pd.DataFrame, table_name: str, columns: list[str]) -> None:
    """Substituo a tabela gerenciada pela versão mais recente dos Parquets locais."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {table_name};")
            command = f"COPY {table_name} ({', '.join(columns)}) FROM STDIN"
            with cursor.copy(command) as copy:
                for row in dataframe[columns].itertuples(index=False, name=None):
                    copy.write_row(tuple(to_python_value(value) for value in row))


def main() -> None:
    """Valido e publico no banco as séries de categorias e fabricantes."""
    if not MONTHLY_PATH.exists() or not BRANDS_PATH.exists():
        raise FileNotFoundError(
            "Silver FENABRAVE ausente. Execute primeiro: "
            "python -m src.transformation.fenabrave_reports_to_silver"
        )

    monthly_dataframe = pd.read_parquet(MONTHLY_PATH)
    brands_dataframe = pd.read_parquet(BRANDS_PATH)
    if monthly_dataframe.duplicated(
        ["ano_referencia", "mes_referencia", "categoria_fenabrave", "segmento_veiculos"]
    ).any():
        raise ValueError("A Silver mensal FENABRAVE tem chaves duplicadas.")
    if (monthly_dataframe["emplacamentos_mes"] < 0).any():
        raise ValueError("A Silver mensal FENABRAVE contém contagens negativas.")

    create_tables()
    replace_table(
        monthly_dataframe,
        "silver.fenabrave_emplacamentos_mensais",
        MONTHLY_COLUMNS,
    )
    replace_table(brands_dataframe, "silver.fenabrave_marcas_mensais", BRAND_COLUMNS)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM silver.fenabrave_emplacamentos_mensais;")
            loaded_monthly = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM silver.fenabrave_marcas_mensais;")
            loaded_brands = cursor.fetchone()[0]
    if loaded_monthly != len(monthly_dataframe) or loaded_brands != len(brands_dataframe):
        raise ValueError("A contagem de linhas da carga FENABRAVE difere dos Parquets de origem.")

    print(f"FENABRAVE Silver carregada: {loaded_monthly} linhas mensais.")
    print(f"FENABRAVE Silver carregada: {loaded_brands} linhas de rankings de marca.")


if __name__ == "__main__":
    # Inicio a carga somente quando executo este módulo diretamente.
    main()
