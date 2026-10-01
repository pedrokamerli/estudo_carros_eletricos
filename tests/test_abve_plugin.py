"""Confiro que a pesquisa histórica não vira uma série artificial para ML."""

import unittest

import pandas as pd

from src.transformation.abve_plugin_to_silver import HISTORY, SNAPSHOT, build_series


class PluginTests(unittest.TestCase):
    def setUp(self):
        self.history = pd.read_csv(HISTORY)
        self.snapshot = pd.read_csv(SNAPSHOT)

    def test_annual_reconciliation_and_continuity(self):
        frame = build_series(self.history, self.snapshot)
        self.assertEqual(len(frame), 64)
        totals = frame.loc[frame.data_referencia.dt.year.eq(2024)].groupby("tecnologia").emplacamentos_mes.sum()
        self.assertEqual(totals.to_dict(), {"BEV": 61615, "PHEV": 64009})

    def test_missing_month_rejected(self):
        with self.assertRaises(ValueError):
            build_series(self.history.drop(index=5), self.snapshot)

    def test_incorrect_annual_total_rejected(self):
        self.history.loc[0, "emplacamentos_bev"] += 1
        with self.assertRaises(ValueError):
            build_series(self.history, self.snapshot)

    def test_negative_value_rejected(self):
        self.snapshot.loc[12, "emplacamentos_bev"] = -1
        with self.assertRaises(ValueError):
            build_series(self.history, self.snapshot)

    def test_source_required(self):
        self.history.loc[0, "url_fonte"] = None
        with self.assertRaises(ValueError):
            build_series(self.history, self.snapshot)

    def test_changed_definition_requires_review(self):
        self.snapshot.loc[12, "regra_classificacao"] = "nova_definicao_nao_revisada"
        with self.assertRaises(ValueError):
            build_series(self.history, self.snapshot)

    def test_unclosed_month_rejected(self):
        self.snapshot.loc[12, "data_captura"] = "2025-01-15"
        with self.assertRaises(ValueError):
            build_series(self.history, self.snapshot)


if __name__ == "__main__":
    unittest.main()
