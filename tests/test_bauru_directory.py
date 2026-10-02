import unittest
from pathlib import Path
import pandas as pd
class BauruDirectoryTests(unittest.TestCase):
    def test_real_directory_evidence_has_distinct_limits(self):
        path=Path(__file__).resolve().parents[1]/"data/portfolio/bauru_recarga_evidencias.csv"
        if not path.exists(): self.skipTest("coleta ainda não executada")
        frame=pd.read_csv(path); self.assertEqual(set(frame.fonte),{"Seguee","Carregados","MapaVolt"}); self.assertTrue(frame.limite.str.len().gt(30).all()); self.assertEqual(frame.loc[frame.fonte.eq("Seguee"),"estacoes_reportadas"].iloc[0],14); self.assertEqual(frame.loc[frame.fonte.eq("Carregados"),"confianca"].iloc[0],73)
if __name__=="__main__": unittest.main()
