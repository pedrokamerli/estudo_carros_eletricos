"""Disponibilizo o contexto BCB em Silver e Gold sem misturar unidades com vendas."""

import pandas as pd
from src.database.connection import get_connection
from src.ingestion.download_bcb_context import OUTPUT


def main():
    frame = pd.read_parquet(OUTPUT)
    if len(frame) != 96 or frame.duplicated(["codigo_sgs", "data_referencia"]).any():
        raise ValueError("Contexto BCB sem as 96 observações únicas esperadas.")
    with get_connection() as connection, connection.cursor() as cursor:
        for schema in ("silver", "gold"):
            # Os nomes são constantes do meu código, não entrada fornecida externamente.
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS {schema}.contexto_economico_bcb (
                data_referencia DATE NOT NULL, codigo_sgs INTEGER NOT NULL,
                indicador TEXT NOT NULL, valor DOUBLE PRECISION NOT NULL,
                unidade TEXT NOT NULL, url_fonte TEXT NOT NULL, data_captura TIMESTAMPTZ NOT NULL,
                data_publicacao DATE, sha256_snapshot TEXT NOT NULL,
                PRIMARY KEY (data_referencia, codigo_sgs))""")
            cursor.execute(f"TRUNCATE {schema}.contexto_economico_bcb")
            with cursor.copy(f"COPY {schema}.contexto_economico_bcb (data_referencia,codigo_sgs,indicador,valor,unidade,url_fonte,data_captura,data_publicacao,sha256_snapshot) FROM STDIN") as copy:
                for row in frame[["data_referencia", "codigo_sgs", "indicador", "valor", "unidade", "url_fonte", "data_captura", "data_publicacao", "sha256_snapshot"]].itertuples(index=False, name=None):
                    copy.write_row(tuple(None if pd.isna(v) else v for v in row))
            cursor.execute(f"SELECT COUNT(*) FROM {schema}.contexto_economico_bcb")
            if cursor.fetchone()[0] != 96:
                raise ValueError("Carga econômica não conciliada.")
    print("Contexto BCB: 96 observações conciliadas em Silver/Gold.")


if __name__ == "__main__":
    main()
