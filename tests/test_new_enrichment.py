"""Testo as regras novas sem depender da rede ou de uma senha de banco."""

import unittest
import pandas as pd
from src.ingestion.capture_abve_aggregates import decode_rows
from src.transformation.inmetro_to_silver import numeric, parse_row, expand_merged_rows
from src.analysis.forecast_intervals import calibrate
from src.transformation.abve_public_to_silver import validate_frames


class EnrichmentTests(unittest.TestCase):
    def test_dictionary_literals_repeats_and_nulls(self):
        ds = {"PH": [{"DM0": [{"S": [{"N": "G0", "DN": "D0"}, {"N": "M0"}], "C": [0, 10]},
                               {"C": [20], "R": 1}, {"C": ["literal", 30]}, {"C": [40], "Ø": 1}]}],
              "ValueDicts": {"D0": ["BEV"]}}
        response = {"results": [{"result": {"data": {"dsr": {"DS": [ds]}}}}]}
        self.assertEqual(decode_rows(response), [["BEV", 10], ["BEV", 20], ["literal", 30], [None, 40]])
        ds["RT"] = ["more"]
        with self.assertRaises(ValueError):
            decode_rows(response)

    def test_inmetro_units_and_null_version_both_layouts(self):
        for size, consumption, autonomy in ((28, 23, 24), (33, 28, 29)):
            row = [""] * size
            row[1:6] = ["MARCA TESTE", "MODELO", "", "EV", "Elétrico"]
            row[2] = "Carro teste"
            row[consumption], row[autonomy] = "0,88", "300"
            parsed = parse_row(row, 2026, 1, {"url_fonte": "fonte", "sha256": "hash", "data_captura": "hoje"})
            self.assertEqual(parsed["autonomia_eletrica_ensaio_km"], 300)
            self.assertEqual(parsed["consumo_energetico_mj_km"], .88)
            self.assertIsNone(parsed["versao"])

    def test_merged_versions_are_separate(self):
        row = [""] * 33
        row[1:4] = ["VOLVO\nVOLVO", "XC90\nXC90", "T8 AWD ULTD\nAWD ULT BLA"]
        row[28:30] = ["0,88\n0,88", "47\n47"]
        result = expand_merged_rows(row)
        self.assertEqual(len(result), 2)
        self.assertEqual([r[3] for r in result], ["T8 AWD ULTD", "AWD ULT BLA"])
        with self.assertRaises(ValueError):
            numeric("0,88 0,88")
        with self.assertRaises(ValueError):
            numeric("-10")

    def test_test_results_cannot_choose_or_calibrate(self):
        rows = []
        for method, error in (("persistencia", 10), ("media_3", 20)):
            for i, date in enumerate(pd.date_range("2025-07-01", periods=14, freq="MS")):
                rows.append(dict(metodo=method, horizonte_meses=1, etapa="validacao" if i < 7 else "teste",
                                 data_referencia=date, previsto=100, real=100 + error, erro_absoluto=error))
        frame = pd.DataFrame(rows)
        method, q, _, end = calibrate(frame)
        frame.loc[frame.etapa.eq("teste"), "real"] = 10000
        changed = calibrate(frame)
        self.assertEqual((method, q, end), (changed[0], changed[1], changed[3]))
        self.assertEqual(q, .1)
        with self.assertRaises(ValueError):
            calibrate(frame, level=.90)

    def test_monthly_reconciliation_rejects_changed_total(self):
        frame = pd.DataFrame({"data_referencia": pd.date_range("2024-01-01", "2026-08-01", freq="MS").strftime("%Y-%m-%d"),
                              "Tipo_Tecnologia": "BEV", "emplacamentos": 10})
        validate_frames({"tecnologia": frame, "modelo": frame.assign(Fabricante="X", Modelo="Y")})
        changed = frame.assign(Fabricante="X", Modelo="Y")
        changed.loc[0, "emplacamentos"] = 11
        with self.assertRaises(ValueError):
            validate_frames({"tecnologia": frame, "modelo": changed})


if __name__ == "__main__":
    unittest.main()
