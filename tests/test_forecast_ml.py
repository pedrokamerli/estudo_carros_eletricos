"""Confiro invariantes temporais essenciais para a confiabilidade do experimento."""

import unittest

import numpy as np
import pandas as pd

from src.analysis.forecast_ml import METHODS, evaluate, features, predict, validate_series


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

    def test_test_values_do_not_change_validation_selection(self):
        # Confirmo também a seleção, não apenas a previsão individual: o teste não escolhe o método.
        frame = pd.DataFrame({"data_referencia": pd.date_range("2024-01-01", periods=32, freq="MS"),
                              "emplacamentos_mes": np.arange(32) * 100 + 500,
                              "categoria_fenabrave": "alvo_teste"})
        changed = frame.copy()
        changed.loc[25:, "emplacamentos_mes"] = 999999
        original_outputs = evaluate(frame)
        changed_outputs = evaluate(changed)
        pd.testing.assert_frame_equal(
            original_outputs["ml_backtest_detalhe"].query("etapa == 'validacao'").reset_index(drop=True),
            changed_outputs["ml_backtest_detalhe"].query("etapa == 'validacao'").reset_index(drop=True))
        self.assertEqual(original_outputs["ml_selecao_modelos"].iloc[0]["metodo"],
                         changed_outputs["ml_selecao_modelos"].iloc[0]["metodo"])


if __name__ == "__main__":
    unittest.main()
