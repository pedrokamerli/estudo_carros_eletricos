"""Carrego os indicadores geográficos de recarga ABVE/Tupi em Silver."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.database.connection import get_connection


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PARQUET_PATH = PROJECT_ROOT / "data" / "silver" / "abve" / "infraestrutura_recarga.parquet"
COLUMNS = [
    "nivel_geografico", "escopo_ranking", "regiao", "municipio", "uf", "posicao",
    "pontos_ac", "pontos_dc", "pontos_total", "participacao_nacional_percentual",
    "data_referencia", "data_publicacao", "data_captura", "url_fonte", "metodo_extracao",
]


def to_python_value(value: Any) -> Any:
    """Converto valores pandas anuláveis em tipos aceitos pelo driver PostgreSQL."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    return value.isoformat() if hasattr(value, "isoformat") else value


def main() -> None:
    """Substituo a tabela Silver por completo a partir do snapshot validado."""
    if not PARQUET_PATH.exists():
        raise FileNotFoundError(
            "Silver de recarga ausente. Execute primeiro: "
            "python -m src.transformation.abve_charging_snapshot_to_silver"
        )
    dataframe = pd.read_parquet(PARQUET_PATH)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS silver;")
            cursor.execute("CREATE SCHEMA IF NOT EXISTS gold;")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS silver.abve_infraestrutura_recarga (
                    id BIGSERIAL PRIMARY KEY,
                    nivel_geografico VARCHAR(20) NOT NULL,
                    escopo_ranking VARCHAR(20) NOT NULL,
                    regiao VARCHAR(30) NOT NULL,
                    municipio VARCHAR(100),
                    uf CHAR(2),
                    posicao SMALLINT,
                    pontos_ac INTEGER CHECK (pontos_ac >= 0),
                    pontos_dc INTEGER CHECK (pontos_dc >= 0),
                    pontos_total INTEGER CHECK (pontos_total >= 0),
                    participacao_nacional_percentual NUMERIC(6, 2)
                        CHECK (participacao_nacional_percentual BETWEEN 0 AND 100),
                    data_referencia DATE NOT NULL,
                    data_publicacao DATE NOT NULL,
                    data_captura DATE NOT NULL,
                    url_fonte TEXT NOT NULL,
                    metodo_extracao VARCHAR(80) NOT NULL
                );
                """
            )
            cursor.execute("TRUNCATE TABLE silver.abve_infraestrutura_recarga;")
            command = (
                "COPY silver.abve_infraestrutura_recarga ("
                + ", ".join(COLUMNS)
                + ") FROM STDIN"
            )
            with cursor.copy(command) as copy:
                for row in dataframe[COLUMNS].itertuples(index=False, name=None):
                    copy.write_row(tuple(to_python_value(value) for value in row))
            cursor.execute("SELECT COUNT(*) FROM silver.abve_infraestrutura_recarga;")
            loaded_rows = cursor.fetchone()[0]
    if loaded_rows != len(dataframe):
        raise ValueError(f"Carreguei {loaded_rows} linhas; esperava {len(dataframe)}.")
    print(f"Silver ABVE/Tupi de recarga carregada no PostgreSQL: {loaded_rows} linhas.")


if __name__ == "__main__":
    # Inicio a carga apenas quando executo este módulo diretamente.
    main()
