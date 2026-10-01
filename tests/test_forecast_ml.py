"""Confiro invariantes temporais essenciais para a confiabilidade do experimento."""

import unittest

import numpy as np
import pandas as pd

from src.analysis.forecast_ml import METHODS, features, predict, validate_series


class ForecastTemporalTests(unittest.TestCase):
    def test_future_values_do_not_change_forecast(self):
        dates = pd.date_range("2024-02-01", periods=31, freq="MS")
        values = np.arange(31, dtype=float) * 100 + 500
        changed = values.copy()
        changed[24:] = 999999
        for method in METHODS:
            for horizon in (1, 2, 3):
                self.assertAlmostEqual(predict(values, dates, 24, horizon, method),
                                       predict(changed, dates, 24, horizon, method))
        np.testing.assert_equal(features(values, dates, 24, 3), features(changed, dates, 24, 3))

    def test_missing_month_is_rejected(self):
        dates = pd.date_range("2024-02-01", periods=32, freq="MS").delete(10)
        with self.assertRaises(ValueError):
            validate_series(pd.DataFrame({"data_referencia": dates, "emplacamentos_mes": 100}))

    def test_negative_count_is_rejected(self):
        frame = pd.DataFrame({"data_referencia": pd.date_range("2024-02-01", periods=31, freq="MS"),
                              "emplacamentos_mes": 100})
        frame.loc[3, "emplacamentos_mes"] = -1
        with self.assertRaises(ValueError):
            validate_series(frame)


if __name__ == "__main__":
    unittest.main()
