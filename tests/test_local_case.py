"""Confiro geografia, condições comerciais e preservação da previsão futura."""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from src.analysis.bauru_case import freeze_future, summarize
from src.ingestion.download_bauru_charging import belongs
from src.ingestion.download_price_history import extract_byd, extract_gwm
from src.analysis.evaluate_frozen_predictions import evaluate


class LocalCaseTests(unittest.TestCase):
    def test_polygon_excludes_hole_and_outside(self):
        geometry = dict(type="Polygon",coordinates=[[[0,0],[4,0],[4,4],[0,4],[0,0]],[[1,1],[2,1],[2,2],[1,2],[1,1]]])
        self.assertTrue(belongs(3,3,geometry))
        self.assertFalse(belongs(1.5,1.5,geometry))
        self.assertFalse(belongs(5,3,geometry))
        self.assertTrue(belongs(0,3,geometry))

    def test_changed_price_pages_fail_closed(self):
        for parser in (extract_byd,extract_gwm):
            with self.assertRaises(ValueError):
                parser("Sem tabela de preços.")

    def test_real_price_capture_parses_full_sources(self):
        data = Path(__file__).resolve().parents[1]/"data/portfolio"
        frame = pd.read_csv(data/"precos_historicos_documentais.csv")
        self.assertEqual(len(frame),39)
        self.assertEqual(set(frame.marca),{"BYD","GWM","Mercedes-Benz"})
        self.assertTrue(frame.preco_anunciado_reais.gt(0).all())
        self.assertTrue(frame.loc[frame.marca.eq("GWM"),"condicao"].str.contains("promocional").any())
        self.assertFalse(frame[["url_fonte","sha256_html","data_anuncio"]].isna().any().any())

    def test_peers_aggregate_growth_not_average_rates(self):
        data = Path(__file__).resolve().parents[1]/"data/portfolio"
        peers = pd.read_csv(data/"estudo_bauru_pares_socioeconomicos.csv")
        result = summarize(peers)
        self.assertEqual(result["jan_ago_2026"],859)
        self.assertAlmostEqual(result["crescimento_pares_agregado_percentual"],136.163863,places=5)
        with self.assertRaises(ValueError):
            summarize(pd.concat([peers,peers.iloc[[0]]]))

    def test_freeze_excludes_current_month_and_cannot_rewrite(self):
        frame = pd.DataFrame({"data_referencia":["2026-09-01","2026-10-01","2026-11-01"],"emplacamentos_previstos":[1,2,3]})
        now = datetime(2026,10,1,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"registry.json"
            original = freeze_future(frame,path,now)
            self.assertEqual(len(original["previsoes"]),1)
            frame.emplacamentos_previstos = 999
            self.assertEqual(freeze_future(frame,path,now),original)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")),original)

    def test_future_evaluation_does_not_invent_actual_or_zero(self):
        registry = {"registrado_em_utc":"2026-10-01T12:00:00+00:00",
                    "previsoes":[dict(tecnologia="BEV",data_referencia="2026-11-01",emplacamentos_previstos=100)]}
        observed = pd.DataFrame([dict(tecnologia="BEV",data_referencia="2026-08-01",emplacamentos=80)])
        result = evaluate(registry,observed,datetime(2026,10,1,tzinfo=timezone.utc))
        self.assertTrue(pd.isna(result.observado.iloc[0]))
        self.assertTrue(pd.isna(result.erro_absoluto.iloc[0]))
        observed = pd.DataFrame([dict(tecnologia="BEV",data_referencia="2026-11-01",emplacamentos=0)])
        result = evaluate(registry,observed,datetime(2026,12,1,tzinfo=timezone.utc))
        self.assertEqual(result.erro_absoluto.iloc[0],100)
        self.assertTrue(pd.isna(result.erro_percentual.iloc[0]))

    def test_future_evaluation_rejects_duplicates_and_past_targets(self):
        registry = {"registrado_em_utc":"2026-10-01T12:00:00+00:00",
                    "previsoes":[dict(tecnologia="BEV",data_referencia="2026-09-01",emplacamentos_previstos=100)]}
        observed = pd.DataFrame([dict(tecnologia="BEV",data_referencia="2026-08-01",emplacamentos=80)])
        with self.assertRaises(ValueError):
            evaluate(registry,observed,datetime(2026,12,1,tzinfo=timezone.utc))
        with self.assertRaises(ValueError):
            evaluate(registry,pd.concat([observed,observed]),datetime(2026,12,1,tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
