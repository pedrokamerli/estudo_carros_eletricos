"""Carrego o snapshot ABVE validado em uma tabela Silver independente."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.database.connection import get_connection


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PARQUET_PATH = PROJECT_ROOT / "data" / "silver" / "abve" / "emplacamentos_mensais.parquet"
COLUMNS = [
    "ano_referencia", "mes_referencia", "emplacamentos_total_painel",
    "emplacamentos_bev", "emplacamentos_phev", "emplacamentos_hev",
    "emplacamentos_hev_flex", "emplacamentos_mhev", "soma_tecnologias_publicadas",
    "divergencia_total_vs_tecnologias", "regra_classificacao", "url_fonte",
    "data_captura", "metodo_extracao",
]


def to_python_value(value: Any) -> Any:
    """Converto valores Pandas nulos ou NumPy para tipos simples do driver."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    return value.isoformat() if hasattr(value, "isoformat") else value


def main() -> None:
    """Recrio a tabela Silver a partir do Parquet que passou pelas validações."""
    if not PARQUET_PATH.exists():
        raise FileNotFoundError(
            "Silver ABVE ausente. Execute primeiro: "
            "python -m src.transformation.abve_snapshot_to_silver"
        )
    dataframe = pd.read_parquet(PARQUET_PATH)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS silver;")
            cursor.execute("CREATE SCHEMA IF NOT EXISTS gold;")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS silver.abve_emplacamentos_mensais (
                    ano_referencia SMALLINT NOT NULL CHECK (ano_referencia BETWEEN 2024 AND 2035),
                    mes_referencia SMALLINT NOT NULL CHECK (mes_referencia BETWEEN 1 AND 12),
                    emplacamentos_total_painel BIGINT NOT NULL CHECK (emplacamentos_total_painel >= 0),
                    emplacamentos_bev BIGINT CHECK (emplacamentos_bev >= 0),
                    emplacamentos_phev BIGINT CHECK (emplacamentos_phev >= 0),
                    emplacamentos_hev BIGINT CHECK (emplacamentos_hev >= 0),
                    emplacamentos_hev_flex BIGINT CHECK (emplacamentos_hev_flex >= 0),
                    emplacamentos_mhev BIGINT CHECK (emplacamentos_mhev >= 0),
                    soma_tecnologias_publicadas BIGINT CHECK (soma_tecnologias_publicadas >= 0),
                    divergencia_total_vs_tecnologias BIGINT,
                    regra_classificacao VARCHAR(60) NOT NULL,
                    url_fonte TEXT NOT NULL,
                    data_captura DATE NOT NULL,
                    metodo_extracao VARCHAR(80) NOT NULL,
                    PRIMARY KEY (ano_referencia, mes_referencia)
                );
                """
            )
            cursor.execute("TRUNCATE TABLE silver.abve_emplacamentos_mensais;")
            command = (
                "COPY silver.abve_emplacamentos_mensais ("
                + ", ".join(COLUMNS)
                + ") FROM STDIN"
            )
            with cursor.copy(command) as copy:
                for row in dataframe[COLUMNS].itertuples(index=False, name=None):
                    copy.write_row(tuple(to_python_value(value) for value in row))
            cursor.execute("SELECT COUNT(*) FROM silver.abve_emplacamentos_mensais;")
            loaded_rows = cursor.fetchone()[0]
    if loaded_rows != len(dataframe):
        raise ValueError(
            f"Carreguei {loaded_rows} linhas, mas o Parquet contém {len(dataframe)}."
        )
    print(f"ABVE Silver carregada no PostgreSQL: {loaded_rows} linhas.")


if __name__ == "__main__":
    # Inicio a carga somente quando executo este módulo diretamente.
    main()
