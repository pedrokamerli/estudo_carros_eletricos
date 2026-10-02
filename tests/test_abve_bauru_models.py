import unittest
from pathlib import Path
import pandas as pd


class AbveBauruModelTests(unittest.TestCase):
    def test_real_export_is_city_scoped_and_nonnegative(self):
        path=Path(__file__).resolve().parents[1]/"data/portfolio/abve_bauru_modelos.csv"
        if not path.exists():
            self.skipTest("captura ABVE Bauru ainda não executada")
        frame=pd.read_csv(path)
        self.assertFalse(frame.empty)
        self.assertTrue(frame.municipio.eq("Bauru").all())
        self.assertTrue(frame.uf.eq("SP").all())
        self.assertTrue(frame.emplacamentos.ge(0).all())
        self.assertFalse(frame[["marca","modelo","tecnologia"]].isna().any().any())
        self.assertEqual(frame.duplicated(["ano_referencia","mes_referencia","marca","modelo","tecnologia"]).sum(),0)
        self.assertTrue(frame.ano_referencia.ge(2022).all())


if __name__ == "__main__":
    unittest.main()
