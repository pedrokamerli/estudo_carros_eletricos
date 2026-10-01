"""Confiro unidades, reconciliação e regras dos novos cálculos do motor."""
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from src.analysis.market_intelligence import growth_table, partial_association
from src.analysis.forecast_challengers import CHALLENGERS, challenger_predict
from src.ingestion.download_charging_evidence import extract
from src.ingestion.download_price_evidence import parse_price

class MarketIntelligenceTests(unittest.TestCase):
    def test_growth_uses_same_months_and_contributions_sum_to_100(self):
        rows = [{"data_referencia":pd.Timestamp(year,month,1),"uf":uf,"emplacamentos":value}
                for uf,value in (("SP",10),("RJ",20)) for year in (2024,2025,2026) for month in range(1,9)]
        frame = pd.DataFrame(rows)
        frame.loc[frame.data_referencia.dt.year.eq(2026),"emplacamentos"] *= 2
        table = growth_table(frame,["uf"])
        self.assertAlmostEqual(table.contribuicao_crescimento_percentual.sum(),100)
        self.assertTrue(table.crescimento_percentual.eq(100).all())

    def test_no_previous_registrations_has_no_infinite_rate(self):
        frame = pd.DataFrame({"uf":["SP"],"data_referencia":[pd.Timestamp("2026-01-01")],"emplacamentos":[10]})
        self.assertTrue(np.isnan(growth_table(frame,["uf"]).iloc[0].crescimento_percentual))

    def test_challengers_cannot_see_future_values(self):
        dates = pd.date_range("2024-01-01",periods=32,freq="MS")
        values = np.arange(32,dtype=float)*100+500
        changed = values.copy()
        changed[25:] = 999999
        for method in CHALLENGERS:
            for horizon in (1,2,3):
                self.assertAlmostEqual(challenger_predict(values,dates,25,horizon,method),challenger_predict(changed,dates,25,horizon,method))

    def test_new_models_preserve_constant_series(self):
        dates = pd.date_range("2024-01-01",periods=32,freq="MS")
        for method in ("drift_12m","holt_amortecido","tendencia_log_6m"):
            self.assertAlmostEqual(challenger_predict(np.repeat(100.,32),dates,25,3,method),100,places=6)

    def test_changed_source_fails_instead_of_inventing_numbers(self):
        with self.assertRaises(ValueError):
            extract("Artigo sem dados.")

    def test_brazilian_announced_price_is_numeric(self):
        self.assertEqual(parse_price("115.800,00."),115800)

    def test_partial_correlation_is_finite(self):
        rng = np.random.default_rng(42)
        city = pd.DataFrame({"uf_ibge":["SP"]*25+["PR"]*25,
             "populacao_censo_2022":rng.uniform(1000,100000,50),
             "rendimento_domiciliar_per_capita_medio_2022_reais":rng.uniform(1000,3000,50),
             "veiculos_eletrificados_por_100_mil_habitantes":rng.uniform(0,1000,50)})
        result = partial_association(city)
        self.assertEqual(result["n_municipios"],50)
        self.assertTrue(-1 <= result["coeficiente_parcial_spearman"] <= 1)

    def test_real_exports_reconcile_and_cover_all_questions(self):
        data = Path(__file__).resolve().parents[1]/"data/portfolio"
        questions = pd.read_csv(data/"perguntas_evidencias_motor.csv")
        self.assertEqual(questions.pergunta_id.tolist(),list(range(1,16)))
        self.assertFalse(questions[["resposta","arquivo_evidencia","limite"]].isna().any().any())
        regions = pd.read_csv(data/"inteligencia_crescimento_regioes.csv")
        self.assertEqual(regions.jan_ago_2026.sum(),261009)
        geography = pd.read_csv(data/"inteligencia_capitais_interior.csv")
        self.assertEqual(geography.jan_ago_2026.sum(),261009)
        self.assertAlmostEqual(geography.contribuicao_crescimento_percentual.sum(),100,places=4)
        pressure = pd.read_csv(data/"inteligencia_recarga_regional.csv")
        self.assertAlmostEqual(pressure.participacao_nacional_percentual.sum(),100)
        self.assertEqual(len(pressure),5)
        self.assertTrue(pressure.limite.str.contains("não mede").all())

    def test_bauru_peers_and_prices_keep_distinct_units(self):
        data = Path(__file__).resolve().parents[1]/"data/portfolio"
        peers = pd.read_csv(data/"estudo_bauru_pares_socioeconomicos.csv")
        self.assertEqual(len(peers),11)
        self.assertEqual(peers.iloc[0].municipio_chave,"BAURU")
        self.assertFalse(peers.municipio_chave.eq("SAO PAULO").any())
        prices = pd.read_csv(data/"preco_vs_emplacamentos_estudo_2024.csv")
        self.assertEqual(len(prices),4)
        self.assertTrue(prices.preco_anunciado_reais.gt(0).all())
        self.assertTrue(prices.limite.str.contains("sem inferência").all())
        projected = pd.read_csv(data/"ml_desafio_projecoes_experimentais.csv")
        self.assertTrue(projected.fonte.eq("ABVE").all())
        self.assertTrue(projected.segmento_veiculos.eq("veiculos_leves_plugin").all())

    def test_challenger_validation_selection_cannot_see_test(self):
        from src.analysis.forecast_ml import evaluate
        dates = pd.date_range("2024-01-01",periods=32,freq="MS")
        frame = pd.DataFrame({"data_referencia":dates,"emplacamentos_mes":np.arange(32)*100+500,"categoria_fenabrave":"teste"})
        changed = frame.copy()
        changed.loc[25:,"emplacamentos_mes"] = 999999
        methods = ("persistencia","drift_12m","holt_amortecido","tendencia_log_6m")
        outputs = [evaluate(f,methods=methods,predictor=challenger_predict) for f in (frame,changed)]
        self.assertEqual(outputs[0]["ml_selecao_modelos"].iloc[0].metodo,outputs[1]["ml_selecao_modelos"].iloc[0].metodo)
        pd.testing.assert_frame_equal(outputs[0]["ml_backtest_detalhe"].query("etapa == 'validacao'").reset_index(drop=True),outputs[1]["ml_backtest_detalhe"].query("etapa == 'validacao'").reset_index(drop=True))
