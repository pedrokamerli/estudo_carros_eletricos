"""Carrego no schema Gold o backtest para facilitar o uso no Power BI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.database.connection import get_connection
from src.analysis.backtest_fenabrave_forecast import HOLDOUT_MONTHS


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PORTFOLIO_PATH = PROJECT_ROOT / "data" / "portfolio"
METRICS_PATH = PORTFOLIO_PATH / "backtest_previsao_fenabrave.csv"
DETAIL_PATH = PORTFOLIO_PATH / "backtest_detalhe_previsao_fenabrave.csv"

METRIC_COLUMNS = [
    "fonte", "categoria_fenabrave", "segmento_veiculos", "metodo", "meses_treino",
    "inicio_treino", "fim_treino", "meses_teste", "inicio_teste", "fim_teste",
    "mae", "rmse", "mape_percentual",
]
DETAIL_COLUMNS = [
    "fonte", "data_referencia", "ano_referencia", "mes_referencia",
    "categoria_fenabrave", "segmento_veiculos", "metodo", "emplacamentos_reais",
    "emplacamentos_previstos", "erro_previsto_menos_real", "erro_absoluto",
    "erro_percentual_absoluto", "passo_no_teste",
]


def to_python_value(value: Any) -> Any:
    """Converto os valores Pandas para os tipos aceitos pelo driver do PostgreSQL."""
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    return value.item() if hasattr(value, "item") else value


def replace_from_csv(path: Path, table: str, columns: list[str], date_columns: list[str]) -> int:
    """Valido o arquivo e substituo a tabela derivada pelo backtest mais recente."""
    if not path.exists():
        raise FileNotFoundError(
            "CSV de backtest ausente. Execute primeiro: "
            "python -m src.analysis.backtest_fenabrave_forecast"
        )
    dataframe = pd.read_csv(path, encoding="utf-8-sig")
    if list(dataframe.columns) != columns:
        raise ValueError(f"As colunas de {path.name} não correspondem ao layout esperado.")
    for column in date_columns:
        dataframe[column] = pd.to_datetime(dataframe[column], errors="raise")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {table};")
            command = f"COPY {table} ({', '.join(columns)}) FROM STDIN"
            with cursor.copy(command) as copy:
                for row in dataframe[columns].itertuples(index=False, name=None):
                    copy.write_row(tuple(to_python_value(value) for value in row))
    return len(dataframe)


def main() -> None:
    """Crio duas tabelas Gold: métricas resumidas e previsões detalhadas do teste."""
    statements = [
        "CREATE SCHEMA IF NOT EXISTS gold;",
        """
        CREATE TABLE IF NOT EXISTS gold.backtest_previsao_fenabrave (
            fonte VARCHAR(30) NOT NULL,
            categoria_fenabrave VARCHAR(20) NOT NULL,
            segmento_veiculos VARCHAR(40) NOT NULL,
            metodo VARCHAR(40) NOT NULL,
            meses_treino SMALLINT NOT NULL CHECK (meses_treino > 0),
            inicio_treino DATE NOT NULL,
            fim_treino DATE NOT NULL,
            meses_teste SMALLINT NOT NULL CHECK (meses_teste > 0),
            inicio_teste DATE NOT NULL,
            fim_teste DATE NOT NULL,
            mae NUMERIC(14, 2) NOT NULL CHECK (mae >= 0),
            rmse NUMERIC(14, 2) NOT NULL CHECK (rmse >= 0),
            mape_percentual NUMERIC(8, 2) NOT NULL CHECK (mape_percentual >= 0),
            PRIMARY KEY (categoria_fenabrave, metodo)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS gold.backtest_detalhe_previsao_fenabrave (
            fonte VARCHAR(30) NOT NULL,
            data_referencia DATE NOT NULL,
            ano_referencia SMALLINT NOT NULL,
            mes_referencia SMALLINT NOT NULL CHECK (mes_referencia BETWEEN 1 AND 12),
            categoria_fenabrave VARCHAR(20) NOT NULL,
            segmento_veiculos VARCHAR(40) NOT NULL,
            metodo VARCHAR(40) NOT NULL,
            emplacamentos_reais BIGINT NOT NULL CHECK (emplacamentos_reais >= 0),
            emplacamentos_previstos NUMERIC(14, 2) NOT NULL,
            erro_previsto_menos_real NUMERIC(14, 2) NOT NULL,
            erro_absoluto NUMERIC(14, 2) NOT NULL CHECK (erro_absoluto >= 0),
            erro_percentual_absoluto NUMERIC(10, 2) NOT NULL CHECK (erro_percentual_absoluto >= 0),
            passo_no_teste SMALLINT NOT NULL CHECK (passo_no_teste > 0),
            PRIMARY KEY (data_referencia, categoria_fenabrave, metodo)
        );
        """,
    ]
    with get_connection() as connection:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)

    metric_count = replace_from_csv(
        METRICS_PATH,
        "gold.backtest_previsao_fenabrave",
        METRIC_COLUMNS,
        ["inicio_treino", "fim_treino", "inicio_teste", "fim_teste"],
    )
    detail_count = replace_from_csv(
        DETAIL_PATH,
        "gold.backtest_detalhe_previsao_fenabrave",
        DETAIL_COLUMNS,
        ["data_referencia"],
    )
    if metric_count == 0 or detail_count != metric_count * HOLDOUT_MONTHS:
        raise ValueError(
            "A carga do backtest recebeu quantidades inesperadas: "
            f"métricas={metric_count}, detalhe={detail_count}."
        )
    print(f"Backtest carregado no PostgreSQL: {metric_count} métricas e {detail_count} previsões de teste.")


if __name__ == "__main__":
    # Inicio a carga somente quando a etapa de backtest tiver produzido os CSVs.
    main()
