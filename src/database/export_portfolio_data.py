"""Exporto recortes agregados do PostgreSQL para demonstrar o projeto no GitHub."""

from __future__ import annotations

from pathlib import Path

from src.database.connection import get_connection


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "data" / "portfolio"

# Compartilho tabelas pequenas e agregadas, preservando o nome que informa a origem.
EXPORTS = {
    "evolucao_frota_nacional.csv": """
        SELECT * FROM gold.evolucao_frota_nacional
        ORDER BY ano_referencia, mes_referencia
    """,
    "emplacamentos_fenabrave_mensais.csv": """
        SELECT * FROM gold.emplacamentos_fenabrave_mensais
        ORDER BY ano_referencia, mes_referencia, categoria_fenabrave
    """,
    "ranking_marcas_fenabrave_mensal.csv": """
        SELECT * FROM gold.ranking_marcas_fenabrave_mensal
        ORDER BY ano_referencia, mes_referencia, categoria_fenabrave, posicao
    """,
    "frota_por_estado.csv": """
        SELECT * FROM gold.frota_por_estado
        ORDER BY ano_referencia, mes_referencia, uf
    """,
    "evolucao_frota_por_estado.csv": """
        SELECT * FROM gold.evolucao_frota_por_estado
        ORDER BY ano_referencia, mes_referencia, uf
    """,
    "frota_capital_vs_interior.csv": """
        SELECT * FROM gold.frota_capital_vs_interior
        ORDER BY ano_referencia, mes_referencia, tipo_localidade
    """,
    "frota_municipal_ultimo_mes.csv": """
        SELECT * FROM gold.frota_por_municipio
        WHERE (ano_referencia, mes_referencia) = (
            SELECT ano_referencia, mes_referencia
            FROM gold.frota_por_municipio
            ORDER BY ano_referencia DESC, mes_referencia DESC
            LIMIT 1
        )
        ORDER BY total_veiculos_eletrificados DESC
    """,
    "penetracao_municipal_ibge.csv": """
        SELECT * FROM gold.penetracao_municipal_ibge
        ORDER BY participacao_eletrificada_na_frota_percentual DESC NULLS LAST
    """,
    "oportunidade_municipal_preliminar.csv": """
        SELECT * FROM gold.oportunidade_municipal_preliminar
        ORDER BY pib_per_capita_aproximado DESC
    """,
    "correlacao_municipal_socioeconomia_adocao.csv": """
        SELECT * FROM gold.correlacao_municipal_socioeconomia_adocao
        ORDER BY variavel_socioeconomica, indicador_adocao, metodo
    """,
    "emplacamentos_mensais_dados_fornecidos.csv": """
        SELECT * FROM gold.emplacamentos_mensais_fornecidos
        ORDER BY ano_referencia, mes_referencia, categoria_eletrificacao
    """,
    "ranking_marcas_modelos_dados_fornecidos.csv": """
        SELECT * FROM gold.ranking_marcas_modelos_fornecido
        ORDER BY ano_referencia, mes_referencia, total_emplacamentos DESC
    """,
}


def export_query(connection, file_name: str, query: str) -> int:
    """Escrevo um resultado SQL diretamente em CSV sem carregar tudo na memória."""
    destination = OUTPUT_PATH / file_name
    copy_query = f"COPY ({query}) TO STDOUT WITH (FORMAT CSV, HEADER TRUE, ENCODING 'UTF8')"
    with connection.cursor().copy(copy_query) as copy, destination.open("wb") as output_file:
        while chunk := copy.read():
            output_file.write(chunk)
    return destination.stat().st_size


def main() -> None:
    """Exporto apenas saídas analíticas aprovadas para compartilhamento no repositório."""
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        for file_name, query in EXPORTS.items():
            if "dados_fornecidos" in file_name:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT to_regclass('gold.emplacamentos_mensais_fornecidos') IS NOT NULL;")
                    if not cursor.fetchone()[0]:
                        print(f"Pulei {file_name}: a fonte fornecida pelo usuário não está carregada.")
                        continue
            size = export_query(connection, file_name, query)
            print(f"Exportado {file_name} ({size:,} bytes)")
    print(f"Exports do portfólio salvos em: {OUTPUT_PATH}")


if __name__ == "__main__":
    # Eu gero estes CSVs depois de atualizar as tabelas Gold do PostgreSQL.
    main()
