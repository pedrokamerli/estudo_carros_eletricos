import unittest
import pandas as pd


class PriceHistoryAnalysisTest(unittest.TestCase):
    def test_resumo_de_precos_tem_tres_marcas_e_limites(self):
        summary = pd.read_csv("data/portfolio/precos_resumo_marca.csv")
        self.assertEqual(set(summary.marca), {"BYD", "GWM", "Mercedes-Benz"})
        self.assertTrue((summary.preco_minimo_reais > 0).all())
        self.assertIn("limite_uso", summary.columns)
