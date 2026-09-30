"""Reconstruo as tabelas Gold para consumo no Power BI e em análises SQL."""

from __future__ import annotations

from src.database.connection import get_connection


# Cada tabela Gold é derivada: eu posso recriá-la sempre que a Silver receber dados novos.
GOLD_STATEMENTS = [
    "CREATE SCHEMA IF NOT EXISTS gold;",
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
    SELECT ano_referencia, mes_referencia, tipo_localidade,
           SUM(quantidade_veiculos)::BIGINT AS total_veiculos_eletrificados
    FROM silver.frota_eletrificada
    WHERE uf_informada = TRUE
    GROUP BY ano_referencia, mes_referencia, tipo_localidade;
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
               SUM(quantidade_veiculos)::BIGINT AS total_veiculos_eletrificados
        FROM silver.frota_eletrificada
        WHERE uf_informada = TRUE
        GROUP BY ano_referencia, mes_referencia
    ),
    base_com_anterior AS (
        SELECT *, LAG(total_veiculos_eletrificados) OVER (
            ORDER BY ano_referencia, mes_referencia
        ) AS total_mes_anterior
        FROM frota_mensal
    )
    SELECT ano_referencia, mes_referencia, total_veiculos_eletrificados,
           total_mes_anterior,
           ROUND(
               100.0 * (total_veiculos_eletrificados - total_mes_anterior)
               / NULLIF(total_mes_anterior, 0), 2
           ) AS crescimento_percentual_mensal
    FROM base_com_anterior;
    """,
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
    "CREATE INDEX IF NOT EXISTS idx_gold_estado_periodo ON gold.frota_por_estado (ano_referencia, mes_referencia);",
    "CREATE INDEX IF NOT EXISTS idx_gold_municipio_periodo ON gold.frota_por_municipio (ano_referencia, mes_referencia);",
    "CREATE INDEX IF NOT EXISTS idx_gold_ranking_periodo ON gold.ranking_marcas_modelos_fornecido (ano_referencia, mes_referencia);",
]


def table_count(table_name: str) -> int:
    """Retorno a quantidade de linhas para mostrar o resultado da atualização."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            return cursor.fetchone()[0]


def main() -> None:
    """Executo toda a modelagem Gold dentro de uma única transação no PostgreSQL."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            for statement in GOLD_STATEMENTS:
                cursor.execute(statement)

    tables = [
        "gold.frota_por_estado",
        "gold.frota_por_municipio",
        "gold.frota_capital_vs_interior",
        "gold.frota_por_categoria_eletrificacao",
        "gold.evolucao_frota_nacional",
        "gold.emplacamentos_mensais_fornecidos",
        "gold.ranking_marcas_modelos_fornecido",
    ]
    print("Camada Gold atualizada:")
    for table in tables:
        print(f"- {table}: {table_count(table):,} linhas")


if __name__ == "__main__":
    # Eu só atualizo a Gold quando executo este módulo de propósito.
    main()
