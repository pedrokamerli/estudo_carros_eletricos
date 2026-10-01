"""Confiro que rankings incompletos não viram quantidades ou períodos inventados."""

import unittest

import pandas as pd

from src.transformation.news_models_to_silver import SOURCES, SNAPSHOT, validate_and_join


class NewsModelsTests(unittest.TestCase):
    def setUp(self):
        self.records = pd.read_csv(SNAPSHOT, dtype="string")
        self.sources = pd.read_csv(SOURCES, dtype="string")

    def test_unknown_quantity_remains_unknown(self):
        result = validate_and_join(self.records, self.sources)
        self.assertEqual(len(result), 65)
        self.assertEqual(result["quantidade_emplacada"].isna().sum(), 9)
        february = result.loc[result["fonte_id"].eq("abve_202402")]
        self.assertTrue(february["quantidade_emplacada"].isna().all())

    def test_duplicate_position_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_and_join(pd.concat([self.records, self.records.iloc[:1]]), self.sources)

    def test_missing_rank_position_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_and_join(self.records.iloc[1:], self.sources)

    def test_accumulated_period_cannot_be_monthly(self):
        self.sources.loc[self.sources["fonte_id"].eq("abve_202404_ytd"), "tipo_periodo"] = "mensal"
        with self.assertRaises(ValueError):
            validate_and_join(self.records, self.sources)

    def test_unknown_source_is_rejected(self):
        self.records.loc[0, "fonte_id"] = "sem_fonte"
        with self.assertRaises(ValueError):
            validate_and_join(self.records, self.sources)


if __name__ == "__main__":
    unittest.main()
