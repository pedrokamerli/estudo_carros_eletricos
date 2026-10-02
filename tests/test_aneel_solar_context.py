import unittest
from pathlib import Path
import pandas as pd


class AneelSolarContextTest(unittest.TestCase):
    def test_resumo_bauru_tem_solar_e_potencia_positiva(self):
        path = Path("data/portfolio/bauru_solar_context.csv")
        self.assertTrue(path.exists())
        frame = pd.read_csv(path)
        self.assertEqual(len(frame), 1)
        row = frame.iloc[0]
        self.assertEqual(row["municipio"], "BAURU")
        self.assertEqual(row["uf"], "SP")
        self.assertGreater(int(row["empreendimentos_fotovoltaicos"]), 0)
        self.assertGreater(float(row["potencia_fotovoltaica_kw"]), 0)


if __name__ == "__main__":
    unittest.main()
