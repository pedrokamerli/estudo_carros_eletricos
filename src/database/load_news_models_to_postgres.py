"""Carrego rankings documentados em tabelas separadas das séries oficiais completas."""

import pandas as pd
from psycopg import sql

from src.database.connection import get_connection
from src.transformation.news_models_to_silver import OUTPUT


def main():
    """Atualizo Silver, Gold e cobertura em uma única transação."""
    frame = pd.read_parquet(OUTPUT)
    if frame.empty or frame.duplicated(["fonte_id", "posicao"]).any():
        raise ValueError("Silver de notícias vazia ou duplicada.")
    definitions = []
    for column in frame:
        dtype = frame[column].dtype
        kind = ("TIMESTAMP" if pd.api.types.is_datetime64_any_dtype(dtype) else
                "BOOLEAN" if pd.api.types.is_bool_dtype(dtype) else
                "BIGINT" if pd.api.types.is_integer_dtype(dtype) else "TEXT")
        definitions.append(sql.SQL("{} {}").format(sql.Identifier(column), sql.SQL(kind)))
    definitions.append(sql.SQL("PRIMARY KEY (fonte_id, posicao)"))
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS silver; CREATE SCHEMA IF NOT EXISTS gold;")
            cursor.execute(sql.SQL("CREATE TABLE IF NOT EXISTS silver.ranking_modelos_noticias ({})").format(
                sql.SQL(", ").join(definitions)))
            cursor.execute("TRUNCATE TABLE silver.ranking_modelos_noticias")
            with cursor.copy(sql.SQL("COPY silver.ranking_modelos_noticias ({}) FROM STDIN").format(
                    sql.SQL(", ").join(map(sql.Identifier, frame.columns)))) as copy:
                for row in frame.itertuples(index=False, name=None):
                    values = []
                    for value in row:
                        values.append(None if pd.isna(value) else
                                      value.to_pydatetime() if isinstance(value, pd.Timestamp) else
                                      value.item() if hasattr(value, "item") else value)
                    copy.write_row(values)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gold.ranking_modelos_noticias
                    (LIKE silver.ranking_modelos_noticias INCLUDING ALL);
                TRUNCATE TABLE gold.ranking_modelos_noticias;
                INSERT INTO gold.ranking_modelos_noticias SELECT * FROM silver.ranking_modelos_noticias;
            """)
            coverage_query = """
                SELECT fonte_id, publicador, origem_declarada, tipo_fonte, url_fonte,
                       inicio_periodo, fim_periodo, tipo_periodo, escopo_tecnologias, granularidade,
                       COUNT(*) AS modelos_listados,
                       COUNT(quantidade_emplacada) AS modelos_com_quantidade,
                       COUNT(*) - COUNT(quantidade_emplacada) AS modelos_sem_quantidade,
                       SUM(quantidade_emplacada) AS soma_quantidades_informadas,
                       MAX(total_mercado_publicado) AS total_mercado_publicado,
                       CASE WHEN COUNT(*) = COUNT(quantidade_emplacada)
                            THEN MAX(total_mercado_publicado) - SUM(quantidade_emplacada)
                            ELSE NULL END AS diferenca_total_menos_top_publicado
                FROM gold.ranking_modelos_noticias
                GROUP BY fonte_id, publicador, origem_declarada, tipo_fonte, url_fonte,
                         inicio_periodo, fim_periodo, tipo_periodo, escopo_tecnologias, granularidade
            """
            cursor.execute("CREATE TABLE IF NOT EXISTS gold.cobertura_rankings_modelos_noticias AS " + coverage_query + " WITH NO DATA")
            cursor.execute("TRUNCATE TABLE gold.cobertura_rankings_modelos_noticias")
            cursor.execute("INSERT INTO gold.cobertura_rankings_modelos_noticias " + coverage_query)
            cursor.execute("SELECT COUNT(*) FROM gold.ranking_modelos_noticias")
            if cursor.fetchone()[0] != len(frame):
                raise ValueError("A contagem carregada não confere com a Silver.")
            print(f"Rankings de notícias carregados: {len(frame)} registros; {frame['fonte_id'].nunique()} fontes/períodos.")


if __name__ == "__main__":
    main()
