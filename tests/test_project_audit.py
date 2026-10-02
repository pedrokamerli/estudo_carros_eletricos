import unittest
from pathlib import Path
import pandas as pd


class ProjectAuditTest(unittest.TestCase):
    def test_auditoria_tem_todos_os_campos_e_nao_tem_erro_de_leitura(self):
        path = Path("data/portfolio/auditoria_exports.csv")
        self.assertTrue(path.exists())
        frame = pd.read_csv(path)
        expected = {"arquivo", "linhas", "colunas", "linhas_duplicadas", "valores_numericos_negativos", "sha256", "status"}
        self.assertTrue(expected.issubset(frame.columns))
        self.assertFalse((frame.status == "ERRO").any())
        self.assertTrue((frame.linhas > 0).all())


if __name__ == "__main__":
    unittest.main()
