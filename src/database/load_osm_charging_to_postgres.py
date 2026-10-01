"""Disponibilizo o mapa OSM sem substituir os totais oficiais/agregados de recarga."""

import pandas as pd
from psycopg import sql

from src.database.connection import get_connection
from src.transformation.osm_charging_to_silver import OUTPUT


def main():
    frame = pd.read_parquet(OUTPUT)
    if frame.empty or frame["osm_id"].duplicated().any():
        raise ValueError("Silver OSM vazia ou duplicada.")
    definitions = []
    for column in frame:
        kind = "BOOLEAN" if column == "coordenada_aproximada" else (
            "DOUBLE PRECISION" if column in {"latitude", "longitude"} else "TEXT")
        definitions.append(sql.SQL("{} {}").format(sql.Identifier(column), sql.SQL(kind)))
    definitions.append(sql.SQL("PRIMARY KEY (osm_id)"))
    # Atualizo as duas camadas em uma transação, preservando a versão anterior se falhar.
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS silver; CREATE SCHEMA IF NOT EXISTS gold;")
        cursor.execute(sql.SQL("CREATE TABLE IF NOT EXISTS silver.recarga_osm ({})").format(sql.SQL(", ").join(definitions)))
        cursor.execute("TRUNCATE silver.recarga_osm")
        with cursor.copy(sql.SQL("COPY silver.recarga_osm ({}) FROM STDIN").format(
                sql.SQL(", ").join(map(sql.Identifier, frame.columns)))) as copy:
            for row in frame.itertuples(index=False, name=None):
                copy.write_row(tuple(None if pd.isna(value) else value for value in row))
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gold.recarga_osm (LIKE silver.recarga_osm INCLUDING ALL);
            TRUNCATE gold.recarga_osm;
            INSERT INTO gold.recarga_osm SELECT * FROM silver.recarga_osm;
        ''')
        cursor.execute("SELECT COUNT(*) FROM gold.recarga_osm")
        if cursor.fetchone()[0] != len(frame):
            raise ValueError("Contagem no banco diferente da Silver.")
    print(f"Mapa exploratório OSM carregado: {len(frame)} objetos.")


if __name__ == "__main__":
    main()
