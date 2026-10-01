"""Confiro cobertura, conservação regional e proteção contra informação futura."""

import unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
import pandas as pd

from src.ingestion.download_bcb_context import normalize, PERIODS
from src.analysis.forecast_macro_abve import macro_features, evaluate_macro
from src.analysis.forecast_regional_fleet import aggregate
from src.ingestion.download_fenabrave_monthly_reports import report_periods
from src.ingestion.download_ons_load import profile
from src.transformation.bronze_to_silver import find_bronze_fuel_files


class NewSourceTests(unittest.TestCase):
    def payload(self):
        return [{"data": d.strftime("%d/%m/%Y"), "valor": "1.0"} for d in PERIODS]

    def test_bcb_complete_and_negative_inflation(self):
        payload = self.payload()
        payload[0]["valor"] = "-0.32"
        self.assertEqual(len(normalize(payload, 433)), 32)
        with self.assertRaises(ValueError):
            normalize(payload, 4390)

    def test_bcb_missing_and_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            normalize(self.payload()[:-1], 433)
        with self.assertRaises(ValueError):
            normalize(self.payload() + self.payload()[:1], 433)

    def test_bcb_nan_rejected(self):
        payload = self.payload()
        payload[0]["valor"] = "NaN"
        with self.assertRaises(ValueError):
            normalize(payload, 433)

    def test_regional_conservation_including_unknown(self):
        result = aggregate(pd.DataFrame(dict(ano_referencia=[2024, 2024], mes_referencia=[1, 1],
                                            uf=["SAO PAULO", "Sem Informação"], total_veiculos_eletrificados=[10, 7])))
        self.assertEqual(result.total_veiculos_eletrificados.sum(), 17)
        self.assertIn("UF não informada", result.regiao.tolist())

    def test_unknown_state_rejected(self):
        with self.assertRaises(ValueError):
            aggregate(pd.DataFrame(dict(ano_referencia=[2024], mes_referencia=[1], uf=["ERRO"], total_veiculos_eletrificados=[1])))

    def test_macro_feature_does_not_read_future(self):
        macro = pd.DataFrame(np.ones((32, 3)), index=PERIODS)
        before = macro_features(np.arange(32), PERIODS, macro, 18)
        macro.iloc[16:] = 999
        after = macro_features(np.arange(32), PERIODS, macro, 18)
        self.assertEqual(before, after)

    def test_test_targets_do_not_change_model_selection(self):
        source = pd.DataFrame(dict(tecnologia=["BEV"] * 32, data_referencia=PERIODS, emplacamentos_mes=np.arange(32) + 100))
        macro = pd.DataFrame(np.ones((32, 3)), index=PERIODS)
        original = evaluate_macro(source, macro)
        source.loc[25:, "emplacamentos_mes"] += 1000
        modified = evaluate_macro(source, macro)
        self.assertEqual(original["ml_macro_selecao"].metodo.tolist(), modified["ml_macro_selecao"].metodo.tolist())
        pd.testing.assert_frame_equal(original["ml_macro_detalhe"].query("etapa == 'validacao'"), modified["ml_macro_detalhe"].query("etapa == 'validacao'"))

    def test_requested_scope_stops_at_august(self):
        self.assertEqual(report_periods()[-1], (2026, 8))
        self.assertEqual(len(report_periods()), 32)

    def test_silver_ignores_bronze_after_cutoff(self):
        paths = [Path("D_Frota_por_UF_Municipio_COMBUSTIVEL_Agosto_2026.xlsx"),
                 Path("D_Frota_por_UF_Municipio_COMBUSTIVEL_Setembro_2026.xlsx")]
        with patch("src.transformation.bronze_to_silver.BRONZE_SENATRAN_PATH") as directory:
            directory.glob.return_value = paths
            self.assertEqual(find_bronze_fuel_files(), paths[:1])

    def test_ons_scope_and_duplicate(self):
        frame = pd.DataFrame(dict(id_subsistema=["N", "N"], nom_subsistema=["NORTE", "NORTE"],
                                  din_instante=["2026-08-01 00:00", "2026-09-01 00:00"], val_cargaenergiahomwmed=[100., 999.]))
        result = profile(frame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.carga_media_mw.iloc[0], 100.)
        with self.assertRaises(ValueError):
            profile(pd.concat([frame, frame], ignore_index=True))


if __name__ == "__main__":
    unittest.main()
