"""Construo fatos/dimensões e confiro conservação mensal antes de publicar para BI."""

import json
from pathlib import Path

from src.database.connection import get_connection
from src.utils.capitals import CAPITALS_BY_UF, UF_ABBREVIATION_BY_NAME

ROOT = Path(__file__).resolve().parents[2]
SQL_PATH = ROOT / "sql/modelo_dimensional_bi.sql"
REPORT = ROOT / "data/quality/modelo_bi.json"

# As restrições do banco testam chaves/nulos; estas consultas testam conteúdo e cobertura.
AUDITS = {
    "conservacao_frota_eletrificada_por_mes": '''
        WITH esperado AS (
            SELECT make_date(ano_referencia::int, mes_referencia::int, 1) AS data_referencia,
                   SUM(quantidade_veiculos) AS total FROM silver.frota_eletrificada
            GROUP BY ano_referencia, mes_referencia
        ), obtido AS (
            SELECT data_referencia, SUM(frota_eletrificada) AS total
            FROM bi.fato_frota_municipal GROUP BY data_referencia
        )
        SELECT COUNT(*) FROM esperado e FULL JOIN obtido b USING(data_referencia)
        WHERE e.total IS DISTINCT FROM b.total
    ''',
    "conservacao_frota_total_por_mes": '''
        WITH esperado AS (
            SELECT make_date(ano_referencia::int, mes_referencia::int, 1) AS data_referencia,
                   SUM(quantidade_veiculos) AS total FROM silver.frota_total_municipal
            GROUP BY ano_referencia, mes_referencia
        ), obtido AS (
            SELECT data_referencia, SUM(frota_total) AS total
            FROM bi.fato_frota_municipal GROUP BY data_referencia
        )
        SELECT COUNT(*) FROM esperado e FULL JOIN obtido b USING(data_referencia)
        WHERE e.total IS DISTINCT FROM b.total
    ''',
    "abve_preservada_por_mes_tecnologia": '''
        SELECT COUNT(*) FROM gold.abve_plugin_mensais e
        FULL JOIN bi.fato_emplacamentos_plugin_abve b USING(data_referencia, tecnologia)
        WHERE e.emplacamentos_mes IS DISTINCT FROM b.emplacamentos_mes
    ''',
    "fenabrave_preservada_por_mes_categoria_segmento": '''
        WITH esperado AS (
            SELECT make_date(ano_referencia::int, mes_referencia::int, 1) AS data_referencia,
                   categoria_fenabrave, segmento_veiculos, emplacamentos_mes
            FROM gold.emplacamentos_fenabrave_mensais
        )
        SELECT COUNT(*) FROM esperado e FULL JOIN bi.fato_emplacamentos_fenabrave b
        USING(data_referencia, categoria_fenabrave, segmento_veiculos)
        WHERE e.emplacamentos_mes IS DISTINCT FROM b.emplacamentos_mes
    ''',
    "universo_municipal_preservado": '''
        WITH esperado AS (SELECT DISTINCT uf, municipio FROM silver.frota_total_municipal)
        SELECT COUNT(*) FROM esperado e FULL JOIN bi.dim_municipio d USING(uf, municipio)
        WHERE e.uf IS NULL OR d.municipio_id IS NULL
    ''',
    "calendario_diario_continuo": '''
        SELECT (MAX(data) - MIN(data) + 1) - COUNT(*) FROM bi.dim_data
    ''',
    "fatos_somente_primeiro_dia_mes": '''
        SELECT COUNT(*) FROM (
            SELECT data_referencia FROM bi.fato_frota_municipal
            UNION ALL SELECT data_referencia FROM bi.fato_emplacamentos_plugin_abve
            UNION ALL SELECT data_referencia FROM bi.fato_emplacamentos_fenabrave
        ) f WHERE EXTRACT(DAY FROM data_referencia) <> 1
    ''',
    "frota_sem_uf_preservada": '''
        WITH esperado AS (
            SELECT make_date(ano_referencia::int, mes_referencia::int, 1) AS data_referencia,
                   SUM(quantidade_veiculos) AS total FROM silver.frota_eletrificada
            WHERE NOT uf_informada GROUP BY ano_referencia, mes_referencia
        ), obtido AS (
            SELECT data_referencia, SUM(frota_eletrificada) AS total
            FROM bi.fato_frota_municipal JOIN bi.dim_municipio USING(municipio_id)
            WHERE NOT uf_informada GROUP BY data_referencia
        )
        SELECT COUNT(*) FROM esperado e FULL JOIN obtido b USING(data_referencia)
        WHERE e.total IS DISTINCT FROM b.total
    ''',
}


def check_audit_result(name, result):
    """Um valor nulo também é falha: uma base vazia não pode passar por silêncio."""
    if result is None or result != 0:
        raise ValueError(f"Modelo BI reprovado: {name}; divergências={result}")


def main():
    report = {"verificacoes": {}, "tabelas": {}}
    # As dimensões/fatos anteriores ficam intactas se qualquer carga ou auditoria falhar.
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute("CREATE TEMP TABLE capital_lookup (uf TEXT PRIMARY KEY, capital TEXT, sigla TEXT) ON COMMIT DROP")
        cursor.executemany("INSERT INTO capital_lookup VALUES (%s, %s, %s)",
                           [(uf, capital, UF_ABBREVIATION_BY_NAME[uf]) for uf, capital in CAPITALS_BY_UF.items()])
        cursor.execute(SQL_PATH.read_text(encoding="utf-8"))
        for name, query in AUDITS.items():
            cursor.execute(query)
            result = cursor.fetchone()[0]
            check_audit_result(name, result)
            report["verificacoes"][name] = "aprovada"
        for name in ("dim_data", "dim_municipio", "fato_frota_municipal",
                     "fato_emplacamentos_plugin_abve", "fato_emplacamentos_fenabrave"):
            cursor.execute(f"SELECT COUNT(*) FROM bi.{name}")
            size = cursor.fetchone()[0]
            if size == 0:
                raise ValueError(f"Tabela BI vazia: {name}")
            report["tabelas"][name] = size
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
