"""Confiro conteúdo e restrições no PostgreSQL real, somente quando habilito a integração."""

import os
import unittest

import psycopg

from src.database.connection import get_connection


@unittest.skipUnless(os.getenv("EV_RUN_BI_INTEGRATION_TESTS") == "1", "PostgreSQL local não solicitado")
class BIIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.connection = get_connection()

    def tearDown(self):
        self.connection.close()

    def test_frota_preserved_by_locality_and_month(self):
        # Conferência por localidade, além da conciliação nacional feita na carga.
        with self.connection.cursor() as cursor:
            cursor.execute('''
                WITH eletrificados AS (
                    SELECT ano_referencia, mes_referencia, uf, municipio,
                           SUM(quantidade_veiculos) AS qtd
                    FROM silver.frota_eletrificada GROUP BY ano_referencia, mes_referencia, uf, municipio
                ), esperado AS (
                    SELECT make_date(t.ano_referencia::int, t.mes_referencia::int, 1) AS data_referencia,
                           t.uf, t.municipio, t.total_veiculos AS total, COALESCE(e.qtd, 0) AS eletrificada
                    FROM gold.frota_total_municipal t LEFT JOIN eletrificados e
                    USING(ano_referencia, mes_referencia, uf, municipio)
                ), obtido AS (
                    SELECT f.*, d.uf, d.municipio FROM bi.fato_frota_municipal f
                    JOIN bi.dim_municipio d USING(municipio_id)
                )
                SELECT COUNT(*) FROM esperado e FULL JOIN obtido b USING(data_referencia, uf, municipio)
                WHERE e.total IS DISTINCT FROM b.frota_total
                   OR e.eletrificada IS DISTINCT FROM b.frota_eletrificada
            ''')
            self.assertEqual(cursor.fetchone()[0], 0)

    def test_abve_is_not_joined_to_fenabrave(self):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT fonte FROM bi.fato_emplacamentos_plugin_abve")
            self.assertEqual(cursor.fetchall(), [("ABVE",)])
            cursor.execute("SELECT DISTINCT fonte FROM bi.fato_emplacamentos_fenabrave")
            self.assertEqual(cursor.fetchall(), [("FENABRAVE",)])

    def test_orphan_locality_is_rejected(self):
        # Mesmo se algum teste falhar, nenhuma linha artificial permanece no banco.
        with self.connection.transaction(force_rollback=True):
            with self.assertRaises(psycopg.errors.ForeignKeyViolation):
                with self.connection.transaction(), self.connection.cursor() as cursor:
                    cursor.execute("INSERT INTO bi.fato_frota_municipal VALUES ('2024-01-01', 'localidade_teste_inexistente', 0, 0)")

    def test_electrified_above_denominator_is_rejected(self):
        with self.connection.transaction(force_rollback=True):
            with self.assertRaises(psycopg.errors.CheckViolation):
                with self.connection.transaction(), self.connection.cursor() as cursor:
                    cursor.execute('''
                        UPDATE bi.fato_frota_municipal SET frota_eletrificada = frota_total + 1
                        WHERE (data_referencia, municipio_id) = (
                            SELECT data_referencia, municipio_id FROM bi.fato_frota_municipal LIMIT 1
                        )
                    ''')


if __name__ == "__main__":
    unittest.main()
