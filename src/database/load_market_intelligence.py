"""Carrego somente as novas tabelas de inteligência, numa transação verificável."""
import hashlib
import json
from pathlib import Path
import pandas as pd
from psycopg import sql
from src.database.connection import get_connection

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/"data/portfolio"
FILES = ["inteligencia_crescimento_estados","inteligencia_crescimento_regioes",
         "inteligencia_crescimento_municipios","inteligencia_capitais_interior",
         "inteligencia_contribuicao_marcas","inteligencia_concentracao_marcas",
         "inteligencia_recarga_regional","inteligencia_recarga_cidades_top20","inteligencia_associacao_controlada",
         "estudo_bauru_mensal","estudo_bauru_comparadores","estudo_bauru_pares_socioeconomicos",
         "recarga_nacional_evidencias","precos_anunciados_evidencias","preco_vs_emplacamentos_estudo_2024",
         "perguntas_evidencias_motor","ml_desafio_backtest_detalhe","ml_desafio_backtest_metricas",
         "ml_desafio_diagnostico_vies","ml_desafio_selecao_modelos","ml_desafio_projecoes_experimentais",
         "precos_historicos_documentais","bauru_estudo_sintese","ml_registro_prospectivo","ml_avaliacao_prospectiva","bauru_modelos_mensal","bauru_modelos_ranking","bauru_modelos_reconciliacao"]
if (DATA/"bauru_recarga_evidencias.csv").exists():
    FILES.append("bauru_recarga_evidencias")
if (DATA/"bauru_recarga_inventario.csv").exists():
    FILES.append("bauru_recarga_inventario")
if (DATA/"bauru_solar_context.csv").exists():
    FILES.append("bauru_solar_context")
for _name in ("inmetro_catalogo_marca_ano", "inmetro_catalogo_modelo"):
    if (DATA/f"{_name}.csv").exists():
        FILES.append(_name)
for _name in ("precos_resumo_marca", "precos_resumo_marca_tecnologia"):
    if (DATA/f"{_name}.csv").exists():
        FILES.append(_name)
if (DATA/"bauru_modelos_tecnologia_preco.csv").exists():
    FILES.append("bauru_modelos_tecnologia_preco")
RECREATE = {"bauru_modelos_tecnologia_preco"}

def main():
    frames = {name:pd.read_csv(DATA/f"{name}.csv") for name in FILES}
    for name,frame in frames.items():
        if frame.empty:
            raise ValueError(f"Export vazio: {name}.")
        # Faço a chave sobre a linha inteira, preservando nulos sem inventar valores.
        frame["id_evidencia"] = [hashlib.sha256(json.dumps([None if pd.isna(v) else v for v in row],ensure_ascii=False,default=str).encode()).hexdigest() for row in frame.itertuples(index=False,name=None)]
        if frame.id_evidencia.duplicated().any():
            raise ValueError(f"Evidências duplicadas: {name}.")
        if "data_referencia" in frame:
            frame["data_referencia"] = pd.to_datetime(frame.data_referencia,errors="raise").dt.date
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS gold")
            for name,frame in frames.items():
                table = sql.Identifier("gold",name)
                if name in RECREATE:
                    # Tabela nova, derivada e versionada: permite corrigir tipos
                    # quando um export inicial só continha nulos em uma coluna.
                    cursor.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(table))
                definitions = []
                for col in frame:
                    kind = "DATE" if col == "data_referencia" else "BIGINT" if pd.api.types.is_integer_dtype(frame[col]) else "DOUBLE PRECISION" if pd.api.types.is_float_dtype(frame[col]) else "TEXT"
                    definitions.append(sql.SQL("{} {}").format(sql.Identifier(col),sql.SQL(kind)))
                definitions.append(sql.SQL("PRIMARY KEY (id_evidencia)"))
                cursor.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(table,sql.SQL(", ").join(definitions)))
                # Aceito apenas acréscimos de campos: não apago nem converto colunas antigas.
                for definition in definitions[:-1]:
                    cursor.execute(sql.SQL("ALTER TABLE {} ADD COLUMN IF NOT EXISTS {}").format(table,definition))
                # Atualizo apenas estes derivados regeneráveis; fontes e tabelas antigas ficam intactas.
                cursor.execute(sql.SQL("DELETE FROM {}").format(table))
                with cursor.copy(sql.SQL("COPY {} ({}) FROM STDIN").format(table,sql.SQL(", ").join(map(sql.Identifier,frame.columns)))) as copy:
                    for row in frame.itertuples(index=False,name=None):
                        copy.write_row(tuple(None if pd.isna(v) else v.item() if hasattr(v,"item") else v for v in row))
                cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(table))
                if cursor.fetchone()[0] != len(frame):
                    raise ValueError(f"Contagem divergente: {name}.")
                print(f"gold.{name}: {len(frame)} linhas conferidas.")

if __name__ == "__main__":
    main()
