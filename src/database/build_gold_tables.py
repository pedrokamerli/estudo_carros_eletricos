"""Reconstruo as tabelas Gold para consumo no Power BI e em análises SQL."""

from __future__ import annotations

from src.database.connection import get_connection


# Cada tabela Gold é derivada: eu posso recriá-la sempre que a Silver receber dados novos.
GOLD_STATEMENTS = [
    "CREATE SCHEMA IF NOT EXISTS gold;",
    "DROP TABLE IF EXISTS gold.frota_total_municipal;",
    """
    CREATE TABLE gold.frota_total_municipal AS
    SELECT ano_referencia, mes_referencia, uf, municipio,
           SUM(quantidade_veiculos)::BIGINT AS total_veiculos
    FROM silver.frota_total_municipal
    GROUP BY ano_referencia, mes_referencia, uf, municipio;
    """,
    "DROP TABLE IF EXISTS gold.frota_por_estado;",
    """
    CREATE TABLE gold.frota_por_estado AS
    SELECT ano_referencia, mes_referencia, uf,
           SUM(quantidade_veiculos)::BIGINT AS total_veiculos_eletrificados
    FROM silver.frota_eletrificada
    WHERE uf_informada = TRUE
    GROUP BY ano_referencia, mes_referencia, uf;
    """,
    "DROP TABLE IF EXISTS gold.frota_por_municipio;",
    """
    CREATE TABLE gold.frota_por_municipio AS
    SELECT ano_referencia, mes_referencia, uf, municipio, tipo_localidade,
           SUM(quantidade_veiculos)::BIGINT AS total_veiculos_eletrificados
    FROM silver.frota_eletrificada
    WHERE uf_informada = TRUE
    GROUP BY ano_referencia, mes_referencia, uf, municipio, tipo_localidade;
    """,
    "DROP TABLE IF EXISTS gold.frota_capital_vs_interior;",
    """
    CREATE TABLE gold.frota_capital_vs_interior AS
    WITH resumo AS (
        SELECT ano_referencia, mes_referencia, tipo_localidade,
               SUM(quantidade_veiculos)::BIGINT AS total_veiculos_eletrificados
        FROM silver.frota_eletrificada
        WHERE uf_informada = TRUE AND tipo_localidade IN ('capital', 'interior')
        GROUP BY ano_referencia, mes_referencia, tipo_localidade
    )
    SELECT *,
           ROUND(100.0 * total_veiculos_eletrificados
                 / NULLIF(SUM(total_veiculos_eletrificados) OVER (
                     PARTITION BY ano_referencia, mes_referencia
                 ), 0), 2) AS participacao_percentual
    FROM resumo;
    """,
    "DROP TABLE IF EXISTS gold.frota_por_categoria_eletrificacao;",
    """
    CREATE TABLE gold.frota_por_categoria_eletrificacao AS
    SELECT ano_referencia, mes_referencia, categoria_eletrificacao,
           SUM(quantidade_veiculos)::BIGINT AS total_veiculos_eletrificados
    FROM silver.frota_eletrificada
    GROUP BY ano_referencia, mes_referencia, categoria_eletrificacao;
    """,
    "DROP TABLE IF EXISTS gold.evolucao_frota_nacional;",
    """
    CREATE TABLE gold.evolucao_frota_nacional AS
    WITH frota_mensal AS (
        SELECT ano_referencia, mes_referencia,
               SUM(quantidade_veiculos)::BIGINT AS total_veiculos_eletrificados,
               COALESCE(SUM(quantidade_veiculos) FILTER (WHERE uf_informada), 0)::BIGINT AS total_veiculos_uf_informada,
               COALESCE(SUM(quantidade_veiculos) FILTER (WHERE NOT uf_informada), 0)::BIGINT AS total_veiculos_sem_uf
        FROM silver.frota_eletrificada
        GROUP BY ano_referencia, mes_referencia
    ),
    base_com_anterior AS (
        SELECT *,
               LAG(total_veiculos_eletrificados, 1) OVER (
                   ORDER BY ano_referencia, mes_referencia
               ) AS total_mes_anterior,
               LAG(total_veiculos_eletrificados, 12) OVER (
                   ORDER BY ano_referencia, mes_referencia
               ) AS total_ano_anterior
        FROM frota_mensal
    )
    SELECT ano_referencia, mes_referencia, total_veiculos_eletrificados,
           total_veiculos_uf_informada, total_veiculos_sem_uf,
           total_mes_anterior,
           total_ano_anterior,
           ROUND(
               100.0 * (total_veiculos_eletrificados - total_mes_anterior)
               / NULLIF(total_mes_anterior, 0), 2
           ) AS crescimento_percentual_mensal,
           ROUND(
               100.0 * (total_veiculos_eletrificados - total_ano_anterior)
               / NULLIF(total_ano_anterior, 0), 2
           ) AS crescimento_percentual_anual
    FROM base_com_anterior;
    """,
    "DROP TABLE IF EXISTS gold.evolucao_frota_por_estado;",
    """
    CREATE TABLE gold.evolucao_frota_por_estado AS
    WITH frota_mensal AS (
        SELECT ano_referencia, mes_referencia, uf,
               SUM(quantidade_veiculos)::BIGINT AS total_veiculos_eletrificados
        FROM silver.frota_eletrificada
        WHERE uf_informada = TRUE
        GROUP BY ano_referencia, mes_referencia, uf
    ),
    base_com_anterior AS (
        SELECT *,
               LAG(total_veiculos_eletrificados, 1) OVER (
                   PARTITION BY uf ORDER BY ano_referencia, mes_referencia
               ) AS total_mes_anterior,
               LAG(total_veiculos_eletrificados, 12) OVER (
                   PARTITION BY uf ORDER BY ano_referencia, mes_referencia
               ) AS total_ano_anterior
        FROM frota_mensal
    )
    SELECT *,
           ROUND(100.0 * (total_veiculos_eletrificados - total_mes_anterior)
                 / NULLIF(total_mes_anterior, 0), 2) AS crescimento_percentual_mensal,
           ROUND(100.0 * (total_veiculos_eletrificados - total_ano_anterior)
                 / NULLIF(total_ano_anterior, 0), 2) AS crescimento_percentual_anual
    FROM base_com_anterior;
    """,
    "CREATE INDEX IF NOT EXISTS idx_gold_estado_periodo ON gold.frota_por_estado (ano_referencia, mes_referencia);",
    "CREATE INDEX IF NOT EXISTS idx_gold_municipio_periodo ON gold.frota_por_municipio (ano_referencia, mes_referencia);",
    "DROP TABLE IF EXISTS gold.emplacamentos_fenabrave_mensais;",
    """
    CREATE TABLE gold.emplacamentos_fenabrave_mensais AS
    WITH base AS (
        SELECT *, MAKE_DATE(ano_referencia, mes_referencia, 1) AS data_referencia
        FROM silver.fenabrave_emplacamentos_mensais
    )
    SELECT atual.ano_referencia, atual.mes_referencia, atual.data_referencia,
           atual.categoria_fenabrave, atual.segmento_veiculos,
           atual.emplacamentos_mes,
           ROUND(
               100.0 * (atual.emplacamentos_mes - anterior.emplacamentos_mes)
               / NULLIF(anterior.emplacamentos_mes, 0), 2
           ) AS crescimento_mensal_percentual,
           anterior_ano.emplacamentos_mes AS emplacamentos_mes_ano_anterior,
           ROUND(
               100.0 * (atual.emplacamentos_mes - anterior_ano.emplacamentos_mes)
               / NULLIF(anterior_ano.emplacamentos_mes, 0), 2
           ) AS crescimento_anual_percentual,
           atual.emplacamentos_acumulado_ano,
           atual.emplacamentos_acumulado_ano_anterior,
           atual.pagina_pdf,
           atual.url_fonte,
           atual.metodo_extracao
    FROM base AS atual
    LEFT JOIN base AS anterior
      ON anterior.data_referencia = atual.data_referencia - INTERVAL '1 month'
     AND anterior.categoria_fenabrave = atual.categoria_fenabrave
     AND anterior.segmento_veiculos = atual.segmento_veiculos
    LEFT JOIN base AS anterior_ano
      ON anterior_ano.data_referencia = atual.data_referencia - INTERVAL '1 year'
     AND anterior_ano.categoria_fenabrave = atual.categoria_fenabrave
     AND anterior_ano.segmento_veiculos = atual.segmento_veiculos;
    """,
    "DROP TABLE IF EXISTS gold.emplacamentos_abve_mensais;",
    """
    CREATE TABLE gold.emplacamentos_abve_mensais AS
    WITH base AS (
        SELECT *, MAKE_DATE(ano_referencia, mes_referencia, 1) AS data_referencia
        FROM silver.abve_emplacamentos_mensais
    ),
    defasagens AS (
        SELECT *,
               LAG(emplacamentos_total_painel, 1) OVER (
                   ORDER BY data_referencia
               ) AS total_mes_anterior,
               LAG(regra_classificacao, 1) OVER (
                   ORDER BY data_referencia
               ) AS regra_mes_anterior,
               LAG(emplacamentos_total_painel, 12) OVER (
                   ORDER BY data_referencia
               ) AS total_ano_anterior,
               LAG(regra_classificacao, 12) OVER (
                   ORDER BY data_referencia
               ) AS regra_ano_anterior
        FROM base
    )
    SELECT ano_referencia, mes_referencia, data_referencia,
           emplacamentos_total_painel, emplacamentos_bev, emplacamentos_phev,
           emplacamentos_hev, emplacamentos_hev_flex, emplacamentos_mhev,
           soma_tecnologias_publicadas, divergencia_total_vs_tecnologias,
           regra_classificacao,
           CASE WHEN regra_classificacao = regra_mes_anterior THEN total_mes_anterior END
               AS emplacamentos_mes_anterior_comparavel,
           CASE WHEN regra_classificacao = regra_mes_anterior THEN ROUND(
               100.0 * (emplacamentos_total_painel - total_mes_anterior)
               / NULLIF(total_mes_anterior, 0), 2
           ) END AS crescimento_mensal_percentual,
           CASE WHEN regra_classificacao = regra_ano_anterior THEN total_ano_anterior END
               AS emplacamentos_mes_ano_anterior_comparavel,
           CASE WHEN regra_classificacao = regra_ano_anterior THEN ROUND(
               100.0 * (emplacamentos_total_painel - total_ano_anterior)
               / NULLIF(total_ano_anterior, 0), 2
           ) END AS crescimento_anual_percentual,
           ROUND(100.0 * emplacamentos_bev
                 / NULLIF(soma_tecnologias_publicadas, 0), 2) AS participacao_bev_percentual,
           ROUND(100.0 * emplacamentos_phev
                 / NULLIF(soma_tecnologias_publicadas, 0), 2) AS participacao_phev_percentual,
           ROUND(100.0 * emplacamentos_hev
                 / NULLIF(soma_tecnologias_publicadas, 0), 2) AS participacao_hev_percentual,
           ROUND(100.0 * emplacamentos_hev_flex
                 / NULLIF(soma_tecnologias_publicadas, 0), 2) AS participacao_hev_flex_percentual,
           url_fonte, data_captura, metodo_extracao
    FROM defasagens;
    """,
    "DROP TABLE IF EXISTS gold.infraestrutura_recarga_abve;",
    """
    CREATE TABLE gold.infraestrutura_recarga_abve AS
    SELECT nivel_geografico, escopo_ranking, regiao, municipio, uf, posicao,
           pontos_ac, pontos_dc, pontos_total, participacao_nacional_percentual,
           data_referencia, data_publicacao, data_captura, url_fonte, metodo_extracao
    FROM silver.abve_infraestrutura_recarga;
    """,
    "DROP TABLE IF EXISTS gold.ranking_marcas_fenabrave_mensal;",
    """
    CREATE TABLE gold.ranking_marcas_fenabrave_mensal AS
    SELECT marca.ano_referencia, marca.mes_referencia, marca.categoria_fenabrave,
           marca.posicao, marca.marca, marca.quantidade_emplacada,
           marca.participacao_percentual AS participacao_percentual_relatorio,
           ROUND(
               100.0 * marca.quantidade_emplacada
               / NULLIF(vendas.emplacamentos_mes, 0), 2
           ) AS participacao_percentual_calculada,
           marca.segmento_veiculos, marca.pagina_pdf, marca.url_fonte,
           marca.metodo_extracao
    FROM silver.fenabrave_marcas_mensais AS marca
    JOIN silver.fenabrave_emplacamentos_mensais AS vendas
      USING (ano_referencia, mes_referencia, categoria_fenabrave, segmento_veiculos);
    """,
]

OPTIONAL_MARKET_STATEMENTS = [
    "DROP TABLE IF EXISTS gold.emplacamentos_mensais_fornecidos;",
    """
    CREATE TABLE gold.emplacamentos_mensais_fornecidos AS
    SELECT ano_referencia, mes_referencia, categoria_eletrificacao,
           SUM(quantidade_emplacada)::BIGINT AS total_emplacamentos,
           BOOL_AND(origem_oficial_confirmada) AS origem_oficial_confirmada
    FROM silver.mercado_ev_fornecido
    GROUP BY ano_referencia, mes_referencia, categoria_eletrificacao;
    """,
    "DROP TABLE IF EXISTS gold.ranking_marcas_modelos_fornecido;",
    """
    CREATE TABLE gold.ranking_marcas_modelos_fornecido AS
    SELECT ano_referencia, mes_referencia, marca, modelo, categoria_eletrificacao,
           SUM(quantidade_emplacada)::BIGINT AS total_emplacamentos,
           BOOL_AND(origem_oficial_confirmada) AS origem_oficial_confirmada
    FROM silver.mercado_ev_fornecido
    GROUP BY ano_referencia, mes_referencia, marca, modelo, categoria_eletrificacao;
    """,
    "CREATE INDEX IF NOT EXISTS idx_gold_ranking_periodo ON gold.ranking_marcas_modelos_fornecido (ano_referencia, mes_referencia);",
]


def table_count(table_name: str) -> int:
    """Retorno a quantidade de linhas para mostrar o resultado da atualização."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            return cursor.fetchone()[0]


def market_silver_exists() -> bool:
    """Confiro se a tabela de mercado fornecida existe antes de gerar Gold opcional."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('silver.mercado_ev_fornecido') IS NOT NULL;")
            return bool(cursor.fetchone()[0])


def main() -> None:
    """Executo toda a modelagem Gold dentro de uma única transação no PostgreSQL."""
    has_market_data = market_silver_exists()
    with get_connection() as connection:
        with connection.cursor() as cursor:
            for statement in GOLD_STATEMENTS:
                cursor.execute(statement)
            # O total nacional inclui UF desconhecida; só os rankings geográficos a excluem.
            # Confiro todas as competências antes de confirmar a transação.
            cursor.execute('''
                WITH esperado AS (
                    SELECT ano_referencia, mes_referencia, SUM(quantidade_veiculos)::BIGINT AS total
                    FROM silver.frota_eletrificada GROUP BY ano_referencia, mes_referencia
                )
                SELECT COUNT(*) FROM esperado e FULL JOIN gold.evolucao_frota_nacional g
                    USING (ano_referencia, mes_referencia)
                WHERE e.total IS DISTINCT FROM g.total_veiculos_eletrificados
                   OR g.total_veiculos_eletrificados IS DISTINCT FROM
                      g.total_veiculos_uf_informada + g.total_veiculos_sem_uf
            ''')
            if cursor.fetchone()[0]:
                raise ValueError("Gold nacional não conserva os totais mensais da Silver.")
            if has_market_data:
                for statement in OPTIONAL_MARKET_STATEMENTS:
                    cursor.execute(statement)

    tables = [
        "gold.frota_por_estado",
        "gold.frota_total_municipal",
        "gold.frota_por_municipio",
        "gold.frota_capital_vs_interior",
        "gold.frota_por_categoria_eletrificacao",
        "gold.evolucao_frota_nacional",
        "gold.evolucao_frota_por_estado",
        "gold.emplacamentos_fenabrave_mensais",
        "gold.emplacamentos_abve_mensais",
        "gold.infraestrutura_recarga_abve",
        "gold.ranking_marcas_fenabrave_mensal",
    ]
    if has_market_data:
        tables.extend([
            "gold.emplacamentos_mensais_fornecidos",
            "gold.ranking_marcas_modelos_fornecido",
        ])
    else:
        print("Fonte de mercado fornecida não carregada; vou gerar as Gold disponíveis de SENATRAN/IBGE.")
    print("Camada Gold atualizada:")
    for table in tables:
        print(f"- {table}: {table_count(table):,} linhas")


if __name__ == "__main__":
    # Eu só atualizo a Gold quando executo este módulo de propósito.
    main()
