import unittest
from pathlib import Path
import pandas as pd


class InmetroCatalogTest(unittest.TestCase):
    def test_resumos_tecnicos_tem_medidas_e_limite(self):
        for name in ("inmetro_catalogo_marca_ano.csv", "inmetro_catalogo_modelo.csv"):
            frame = pd.read_csv(Path("data/portfolio") / name)
            self.assertGreater(len(frame), 0)
            self.assertIn("limite_uso", frame.columns)
        model = pd.read_csv("data/portfolio/inmetro_catalogo_modelo.csv")
        self.assertTrue((model["versoes_catalogadas"] > 0).all())


if __name__ == "__main__":
    unittest.main()
