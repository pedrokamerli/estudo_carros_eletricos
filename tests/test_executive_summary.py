import unittest
from pathlib import Path


class ExecutiveSummaryTest(unittest.TestCase):
    def test_resumo_executivo_tem_numeros_e_limitacoes(self):
        text = Path("docs/resumo_executivo.md").read_text(encoding="utf-8")
        self.assertIn("A pergunta de negócio", text)
        self.assertIn("Bauru", text)
        self.assertIn("As previsões são experimentais", text)
        self.assertIn("Gerado por", text)


if __name__ == "__main__":
    unittest.main()
