"""Testo o novo rodapé sem enfraquecer os controles de nulos da SENATRAN."""

import unittest

import pandas as pd

from src.transformation.bronze_to_silver import separate_verified_total_footer


class FooterTests(unittest.TestCase):
    def sample(self):
        return pd.DataFrame({"UF": ["SAO PAULO", "SAO PAULO", None],
                             "Município": ["SAO PAULO", "CAMPINAS", None],
                             "Combustível Veículo": ["ELETRICO", "GASOLINA", None],
                             "Qtd. Veículos": [10, 20, 30]})

    def test_total_separated_without_changing_bronze(self):
        source = self.sample()
        result, metadata = separate_verified_total_footer(source)
        self.assertEqual(len(source), 3)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["Qtd. Veículos"].sum(), 30)
        self.assertTrue(metadata["conciliacao_rodape_aprovada"])

    def test_incorrect_total_rejected(self):
        source = self.sample()
        source.loc[2, "Qtd. Veículos"] = 31
        with self.assertRaises(ValueError):
            separate_verified_total_footer(source)

    def test_missing_keys_in_middle_rejected(self):
        source = self.sample().iloc[[0, 2, 1]].reset_index(drop=True)
        with self.assertRaises(ValueError):
            separate_verified_total_footer(source)

    def test_no_footer_keeps_all_detail(self):
        result, metadata = separate_verified_total_footer(self.sample().iloc[:2])
        self.assertEqual(len(result), 2)
        self.assertFalse(metadata["rodape_total_separado"])


if __name__ == "__main__":
    unittest.main()
