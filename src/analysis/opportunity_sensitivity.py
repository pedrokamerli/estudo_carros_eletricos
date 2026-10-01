"""Confiro quanto meu filtro de oportunidade muda ao alterar os percentis."""

from src.database.connection import get_connection


def main():
    """Comparo nove cortes com a regra original de quartis, usando a mesma amostra."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gold.sensibilidade_oportunidade (
                    percentil_economia DOUBLE PRECISION NOT NULL,
                    percentil_adocao DOUBLE PRECISION NOT NULL,
                    municipios_amostra BIGINT NOT NULL,
                    limite_pib_per_capita DOUBLE PRECISION NOT NULL,
                    limite_renda DOUBLE PRECISION NOT NULL,
                    limite_adocao DOUBLE PRECISION NOT NULL,
                    municipios_selecionados BIGINT NOT NULL,
                    municipios_regra_original BIGINT NOT NULL,
                    intersecao_original BIGINT NOT NULL,
                    uniao_original BIGINT NOT NULL,
                    jaccard_original DOUBLE PRECISION NOT NULL,
                    ano_referencia_frota BIGINT NOT NULL,
                    mes_referencia_frota BIGINT NOT NULL,
                    PRIMARY KEY (percentil_economia, percentil_adocao)
                );
                TRUNCATE TABLE gold.sensibilidade_oportunidade;
                INSERT INTO gold.sensibilidade_oportunidade
                WITH cortes AS (
                    SELECT economia, adocao
                    FROM (VALUES (0.70), (0.75), (0.80)) e(economia)
                    CROSS JOIN (VALUES (0.20), (0.25), (0.30)) a(adocao)
                ), limites AS (
                    SELECT economia, adocao,
                        percentile_cont(economia) WITHIN GROUP (ORDER BY pib_per_capita_aproximado) AS pib,
                        percentile_cont(economia) WITHIN GROUP (ORDER BY rendimento_domiciliar_per_capita_medio_2022_reais) AS renda,
                        percentile_cont(adocao) WITHIN GROUP (ORDER BY veiculos_eletrificados_por_100_mil_habitantes) AS intensidade
                    FROM gold.oportunidade_municipal_preliminar CROSS JOIN cortes
                    GROUP BY economia, adocao
                ), flags AS (
                    SELECT l.*, m.ano_referencia_frota, m.mes_referencia_frota,
                        m.oportunidade_preliminar AS original,
                        (m.pib_per_capita_aproximado >= l.pib
                         AND m.rendimento_domiciliar_per_capita_medio_2022_reais >= l.renda
                         AND m.veiculos_eletrificados_por_100_mil_habitantes <= l.intensidade) AS selecionado
                    FROM gold.oportunidade_municipal_preliminar m CROSS JOIN limites l
                ), resumo AS (
                    SELECT economia, adocao, COUNT(*) AS amostra, pib, renda, intensidade,
                        COUNT(*) FILTER (WHERE selecionado) AS selecionados,
                        COUNT(*) FILTER (WHERE original) AS originais,
                        COUNT(*) FILTER (WHERE selecionado AND original) AS intersecao,
                        COUNT(*) FILTER (WHERE selecionado OR original) AS uniao,
                        MIN(ano_referencia_frota) AS ano, MIN(mes_referencia_frota) AS mes
                    FROM flags GROUP BY economia, adocao, pib, renda, intensidade
                )
                SELECT economia, adocao, amostra, pib, renda, intensidade,
                       selecionados, originais, intersecao, uniao,
                       CASE WHEN uniao = 0 THEN 1.0 ELSE intersecao::double precision / uniao END,
                       ano, mes FROM resumo;
            """)
            cursor.execute("SELECT * FROM gold.sensibilidade_oportunidade ORDER BY percentil_economia, percentil_adocao")
            rows = cursor.fetchall()
            if len(rows) != 9:
                raise ValueError("Esperava nove cenários de sensibilidade.")
            baseline = next(row for row in rows if row[0] == 0.75 and row[1] == 0.25)
            if baseline[6] != baseline[7] or baseline[10] != 1.0:
                raise ValueError("O corte original não reproduz a classificação de quartis.")
            print(f"Sensibilidade validada: 9 cenários; original seleciona {baseline[6]} municípios.")
            for row in rows:
                print(f"Economia P{row[0]*100:.0f}, adoção P{row[1]*100:.0f}: {row[6]} municípios; Jaccard {row[10]:.3f}")


if __name__ == "__main__":
    main()
