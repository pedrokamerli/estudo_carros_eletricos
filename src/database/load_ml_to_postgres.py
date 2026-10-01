"""Publico as saídas de ML na Gold para consulta SQL e conexão do Power BI."""

import pandas as pd
from psycopg import sql

from src.analysis.forecast_ml import OUTPUT
from src.database.connection import get_connection


TABLES = {
    "ml_backtest_detalhe": ["categoria_fenabrave", "etapa", "metodo", "horizonte_meses", "fim_treino"],
    "ml_backtest_metricas": ["categoria_fenabrave", "etapa", "metodo", "horizonte_meses"],
    "ml_selecao_modelos": ["categoria_fenabrave"],
    "ml_projecoes_experimentais": ["categoria_fenabrave", "data_referencia"],
}


def main():
    """Valido todos os arquivos antes de substituir as quatro tabelas na mesma transação."""
    frames = {name: pd.read_csv(OUTPUT / f"{name}.csv") for name in TABLES}
    for name, frame in frames.items():
        if frame.empty or frame.isna().any().any() or frame.duplicated(TABLES[name]).any():
            raise ValueError(f"Saída inválida ou duplicada: {name}")
        for column in ("fim_treino", "data_referencia"):
            if column in frame:
                frame[column] = pd.to_datetime(frame[column], errors="raise").dt.date
        if "fim_treino" in frame and (frame["fim_treino"] >= frame["data_referencia"]).any():
            raise ValueError("Encontrei um alvo dentro do período de treino.")
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS gold")
            for name, frame in frames.items():
                table = sql.Identifier("gold", name)
                definitions = []
                for column in frame:
                    dtype = frame[column].dtype
                    kind = ("DATE" if column in ("fim_treino", "data_referencia") else
                            "BOOLEAN" if pd.api.types.is_bool_dtype(dtype) else
                            "BIGINT" if pd.api.types.is_integer_dtype(dtype) else
                            "DOUBLE PRECISION" if pd.api.types.is_float_dtype(dtype) else "TEXT")
                    definitions.append(sql.SQL("{} {} NOT NULL").format(sql.Identifier(column), sql.SQL(kind)))
                definitions.append(sql.SQL("PRIMARY KEY ({})").format(
                    sql.SQL(", ").join(map(sql.Identifier, TABLES[name]))))
                cursor.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
                    table, sql.SQL(", ").join(definitions)))
                cursor.execute(sql.SQL("TRUNCATE TABLE {}").format(table))
                with cursor.copy(sql.SQL("COPY {} ({}) FROM STDIN").format(
                        table, sql.SQL(", ").join(map(sql.Identifier, frame.columns)))) as copy:
                    for row in frame.itertuples(index=False, name=None):
                        copy.write_row(tuple(v.item() if hasattr(v, "item") else v for v in row))
                cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(table))
                if cursor.fetchone()[0] != len(frame):
                    raise ValueError(f"A contagem carregada não confere: {name}")
                print(f"Gold {name}: {len(frame)} linhas")


if __name__ == "__main__":
    main()
