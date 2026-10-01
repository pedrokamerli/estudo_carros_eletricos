"""Confiro a matemática das comparações que conto no painel."""
import unittest
import pandas as pd
from src.dashboard.story import comparable_years, percent_change, ranked_share

class StoryTests(unittest.TestCase):
    def test_partial_year_is_compared_to_same_months(self):
        dates = pd.date_range("2024-01-01","2026-08-01",freq="MS")
        frame = pd.DataFrame({"data_referencia":dates,"tecnologia":"BEV","emplacamentos":10})
        self.assertEqual(comparable_years(frame,["BEV"]).Emplacamentos.tolist(),[80,80,80])
        with self.assertRaises(ValueError):
            comparable_years(frame,["BEV"],12)

    def test_share_denominator_includes_all_brands(self):
        frame = pd.DataFrame({"marca":["A","B","C"],"emplacamentos":[50,30,20]})
        self.assertEqual(ranked_share(frame,["marca"]).iloc[0]["Participação (%)"],50)

    def test_zero_denominator_is_not_infinite_growth(self):
        self.assertIsNone(percent_change(10,0))
        self.assertEqual(percent_change(20,10),100)

    def test_missing_technology_is_not_silently_zero(self):
        frame = pd.DataFrame({"data_referencia":pd.date_range("2024-01-01",periods=8,freq="MS"),"tecnologia":"BEV","emplacamentos":10})
        with self.assertRaises(ValueError):
            comparable_years(frame,["BEV","PHEV"])
