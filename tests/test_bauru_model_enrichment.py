import unittest
import pandas as pd


class BauruModelEnrichmentTest(unittest.TestCase):
    def test_enriquecimento_preserva_granularidade_e_status(self):
        source = pd.read_csv("data/portfolio/bauru_modelos_ranking.csv")
        enriched = pd.read_csv("data/portfolio/bauru_modelos_tecnologia_preco.csv")
        self.assertEqual(len(source), len(enriched))
        self.assertIn("status_inmetro", enriched.columns)
        self.assertIn("status_preco", enriched.columns)
        self.assertTrue((enriched.status_inmetro.str.contains("modelo_correspondido|sem_correspondencia")).all())
