"""Confiro que a análise de baixa adoção não perde os municípios sem eletrificados."""

import unittest

import pandas as pd

from src.transformation.silver_to_gold import build_municipal_penetration_gold


class MunicipalCoverageTests(unittest.TestCase):
    def setUp(self):
        self.electric = pd.DataFrame({"uf": ["SAO PAULO"], "municipio": ["CIDADE A"],
                                      "ano_referencia": [2026], "mes_referencia": [7],
                                      "quantidade_veiculos": [2]})
        self.total = pd.DataFrame({"uf": ["SAO PAULO"] * 2, "municipio": ["CIDADE A", "CIDADE B"],
                                   "ano_referencia": [2026] * 2, "mes_referencia": [7] * 2,
                                   "quantidade_veiculos": [100, 200]})
        self.ibge = pd.DataFrame({"uf": ["SP"] * 2, "municipio_chave": ["CIDADE A", "CIDADE B"],
                                  "codigo_ibge": ["3500001", "3500002"], "populacao_censo_2022": [1000, 2000],
                                  "pib_per_capita_aproximado": [10000, 20000],
                                  "rendimento_domiciliar_per_capita_medio_2022_reais": [1000, 2000]})

    def test_zero_record_municipality_is_included(self):
        result = build_municipal_penetration_gold(self.electric, self.total, self.ibge)
        self.assertEqual(len(result), 2)
        zero = result.loc[result["municipio"].eq("CIDADE B")].iloc[0]
        self.assertEqual(zero["quantidade_veiculos"], 0)
        self.assertEqual(zero["participacao_eletrificada_na_frota_percentual"], 0)
        self.assertEqual(zero["codigo_ibge"], "3500002")

    def test_electric_without_denominator_is_rejected(self):
        with self.assertRaises(ValueError):
            build_municipal_penetration_gold(self.electric, self.total.iloc[1:], self.ibge)


if __name__ == "__main__":
    unittest.main()
