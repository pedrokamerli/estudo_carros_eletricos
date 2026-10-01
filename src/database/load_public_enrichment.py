"""Publico novas bases documentadas em uma transação, mantendo nulos reais."""

from pathlib import Path
import pandas as pd
from psycopg import sql
from src.database.connection import get_connection

ROOT = Path(__file__).resolve().parents[2]
FILES = {f"abve_publico_{n}": f"abve_publico_{n}_gold.csv" for n in ("tecnologia", "modelo", "municipio")}
FILES["inmetro_versoes_eletrificadas"] = "inmetro_versoes_eletrificadas.csv"


def main():
    frames = {name: pd.read_csv(ROOT / "data/portfolio" / filename) for name, filename in FILES.items()}
    for frame in frames.values():
        if "data_referencia" in frame:
            frame["data_referencia"] = pd.to_datetime(frame.data_referencia, errors="raise").dt.date
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS gold")
            for name, frame in frames.items():
                if frame.empty or frame.id_registro.isna().any() or frame.id_registro.duplicated().any():
                    raise ValueError(f"Identificadores inválidos: {name}")
                table = sql.Identifier("gold", name)
                defs = []
                for col in frame:
                    kind = "DATE" if col == "data_referencia" else "BIGINT" if pd.api.types.is_integer_dtype(frame[col]) else "DOUBLE PRECISION" if pd.api.types.is_float_dtype(frame[col]) else "TEXT"
                    defs.append(sql.SQL("{} {}").format(sql.Identifier(col), sql.SQL(kind)))
                defs.append(sql.SQL("PRIMARY KEY (id_registro)"))
                cursor.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(table, sql.SQL(", ").join(defs)))
                cursor.execute(sql.SQL("TRUNCATE TABLE {}").format(table))
                with cursor.copy(sql.SQL("COPY {} ({}) FROM STDIN").format(table, sql.SQL(", ").join(map(sql.Identifier, frame.columns)))) as copy:
                    for row in frame.itertuples(index=False, name=None):
                        copy.write_row(tuple(None if pd.isna(v) else v.item() if hasattr(v, "item") else v for v in row))
                cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(table))
                if cursor.fetchone()[0] != len(frame):
                    raise ValueError("Contagem carregada não confere.")
                print(f"Gold {name}: {len(frame)} linhas.")


if __name__ == "__main__":
    main()
