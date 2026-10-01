"""Exporto recortes agregados do PostgreSQL para demonstrar o projeto no GitHub."""

from __future__ import annotations

from pathlib import Path

from src.database.connection import get_connection


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "data" / "portfolio"

# Compartilho tabelas pequenas e agregadas, preservando o nome que informa a origem.
EXPORTS = {
    "perfil_carga_ons_mensal_hora.csv": "SELECT * FROM gold.perfil_carga_ons_mensal_hora ORDER BY data_referencia, id_subsistema, hora",
    "contexto_economico_bcb.csv": "SELECT * FROM gold.contexto_economico_bcb ORDER BY data_referencia, codigo_sgs",
    "frota_regional_mensal.csv": "SELECT * FROM gold.frota_regional_mensal ORDER BY regiao, data_referencia",
    "ml_macro_detalhe.csv": "SELECT * FROM gold.ml_macro_detalhe ORDER BY tecnologia, etapa, fim_treino, metodo",
    "ml_macro_metricas.csv": "SELECT * FROM gold.ml_macro_metricas ORDER BY tecnologia, etapa, metodo",
    "ml_macro_selecao.csv": "SELECT * FROM gold.ml_macro_selecao ORDER BY tecnologia",
    "ml_frota_regional_backtest_detalhe.csv": "SELECT * FROM gold.ml_frota_regional_backtest_detalhe ORDER BY regiao, etapa, fim_treino, horizonte_meses, metodo",
    "ml_frota_regional_backtest_metricas.csv": "SELECT * FROM gold.ml_frota_regional_backtest_metricas ORDER BY regiao, etapa, horizonte_meses, metodo",
    "ml_frota_regional_selecao_modelos.csv": "SELECT * FROM gold.ml_frota_regional_selecao_modelos ORDER BY regiao",
    "ml_frota_regional_projecoes_experimentais.csv": "SELECT * FROM gold.ml_frota_regional_projecoes_experimentais ORDER BY regiao, data_referencia",
    "bi_dim_data.csv": "SELECT * FROM bi.dim_data ORDER BY data",
    "bi_dim_municipio.csv": "SELECT * FROM bi.dim_municipio ORDER BY uf, municipio",
    "bi_fato_frota_municipal.csv": "SELECT * FROM bi.fato_frota_municipal ORDER BY data_referencia, municipio_id",
    "bi_fato_emplacamentos_plugin_abve.csv": "SELECT * FROM bi.fato_emplacamentos_plugin_abve ORDER BY data_referencia, tecnologia",
    "bi_fato_emplacamentos_fenabrave.csv": "SELECT * FROM bi.fato_emplacamentos_fenabrave ORDER BY data_referencia, categoria_fenabrave, segmento_veiculos",
    "recarga_osm.csv": "SELECT * FROM gold.recarga_osm ORDER BY osm_id",
    "abve_plugin_mensais.csv": "SELECT * FROM gold.abve_plugin_mensais ORDER BY tecnologia, data_referencia",
    "ml_abve_backtest_detalhe.csv": "SELECT * FROM gold.ml_abve_backtest_detalhe ORDER BY tecnologia, etapa, fim_treino, horizonte_meses, metodo",
    "ml_abve_backtest_metricas.csv": "SELECT * FROM gold.ml_abve_backtest_metricas ORDER BY tecnologia, etapa, horizonte_meses, metodo",
    "ml_abve_selecao_modelos.csv": "SELECT * FROM gold.ml_abve_selecao_modelos ORDER BY tecnologia",
    "ml_abve_projecoes_experimentais.csv": "SELECT * FROM gold.ml_abve_projecoes_experimentais ORDER BY tecnologia, data_referencia",
    "ranking_modelos_noticias_gold.csv": "SELECT * FROM gold.ranking_modelos_noticias ORDER BY fonte_id, posicao",
    "cobertura_rankings_modelos_noticias.csv": "SELECT * FROM gold.cobertura_rankings_modelos_noticias ORDER BY inicio_periodo, fim_periodo, fonte_id",
    "sensibilidade_oportunidade.csv": "SELECT * FROM gold.sensibilidade_oportunidade ORDER BY percentil_economia, percentil_adocao",
    "ml_backtest_detalhe.csv": "SELECT * FROM gold.ml_backtest_detalhe ORDER BY categoria_fenabrave, etapa, fim_treino, horizonte_meses, metodo",
    "ml_backtest_metricas.csv": "SELECT * FROM gold.ml_backtest_metricas ORDER BY categoria_fenabrave, etapa, horizonte_meses, metodo",
    "ml_selecao_modelos.csv": "SELECT * FROM gold.ml_selecao_modelos ORDER BY categoria_fenabrave",
    "ml_projecoes_experimentais.csv": "SELECT * FROM gold.ml_projecoes_experimentais ORDER BY categoria_fenabrave, data_referencia",
    "evolucao_frota_nacional.csv": """
        SELECT * FROM gold.evolucao_frota_nacional
        ORDER BY ano_referencia, mes_referencia
    """,
    "emplacamentos_fenabrave_mensais.csv": """
        SELECT * FROM gold.emplacamentos_fenabrave_mensais
        ORDER BY ano_referencia, mes_referencia, categoria_fenabrave
    """,
    "emplacamentos_abve_mensais_gold.csv": """
        SELECT * FROM gold.emplacamentos_abve_mensais
        ORDER BY ano_referencia, mes_referencia
    """,
    "infraestrutura_recarga_abve_gold.csv": """
        SELECT * FROM gold.infraestrutura_recarga_abve
        ORDER BY CASE nivel_geografico WHEN 'nacional' THEN 1 WHEN 'regiao' THEN 2
                 WHEN 'estado' THEN 3 ELSE 4 END, posicao NULLS LAST
    """,
    "ranking_marcas_fenabrave_mensal.csv": """
        SELECT * FROM gold.ranking_marcas_fenabrave_mensal
        ORDER BY ano_referencia, mes_referencia, categoria_fenabrave, posicao
    """,
    "backtest_previsao_fenabrave.csv": """
        SELECT * FROM gold.backtest_previsao_fenabrave
        ORDER BY categoria_fenabrave, mae
    """,
    "backtest_detalhe_previsao_fenabrave.csv": """
        SELECT * FROM gold.backtest_detalhe_previsao_fenabrave
        ORDER BY categoria_fenabrave, data_referencia, metodo
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
