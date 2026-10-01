"""Testo se contexto econômico melhora a previsão nacional, sem prometer causalidade."""

import hashlib
import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.analysis.forecast_ml import OUTPUT, features, predict, validate_series
from src.ingestion.download_bcb_context import OUTPUT as MACRO_INPUT
from src.transformation.abve_plugin_to_silver import OUTPUT as SALES_INPUT


def macro_features(values, dates, macro, origin):
    """Uso contexto dois meses antes do último mês de vendas observado na origem."""
    # A defasagem reduz risco de divulgação tardia, mas não substitui vintages históricos.
    return features(values, dates, origin, 1) + macro.iloc[origin - 3].tolist()


def evaluate_macro(source, macro):
    detail = []
    for tech, group in source.groupby("tecnologia"):
        group = group.sort_values("data_referencia")
        values, dates = validate_series(group)
        aligned = macro.reindex(dates)
        if aligned.isna().any().any():
            raise ValueError("Contexto econômico incompleto para os meses do alvo.")
        split = len(values) - 7
        for origin in range(18, len(values)):
            train_origins = range(3, origin)
            x = [macro_features(values, dates, aligned, i) for i in train_origins]
            y = np.log1p([values[i] for i in train_origins])
            model = make_pipeline(StandardScaler(), Ridge(alpha=10.0))
            model.fit(x, y)
            prediction = max(0.0, float(np.expm1(model.predict([macro_features(values, dates, aligned, origin)])[0])))
            predictions = {"ridge_macro_lag2": prediction,
                           "ridge_sem_macro": predict(values, dates, origin, 1, "ridge"),
                           "persistencia": values[origin - 1]}
            for method, result in predictions.items():
                if not np.isfinite(result):
                    raise ValueError("Previsão não finita.")
                detail.append(dict(tecnologia=tech, etapa="validacao" if origin < split else "teste",
                                   metodo=method, fim_treino=dates[origin - 1],
                                   competencia_macro=dates[origin - 3], data_referencia=dates[origin],
                                   real=values[origin], previsto=result))
    frame = pd.DataFrame(detail)
    frame["erro_absoluto"] = (frame.real - frame.previsto).abs()
    rows = []
    for key, group in frame.groupby(["tecnologia", "etapa", "metodo"]):
        rows.append(dict(zip(["tecnologia", "etapa", "metodo"], key), n_previsoes=len(group),
                         mae=group.erro_absoluto.mean(), wape_percentual=100 * group.erro_absoluto.sum() / group.real.sum()))
    metrics = pd.DataFrame(rows)
    selections = []
    for tech, group in metrics.groupby("tecnologia"):
        # Congelo a escolha pela validação; o teste é apenas a avaliação final.
        winner = group.loc[group.etapa.eq("validacao")].sort_values("wape_percentual", kind="stable").iloc[0]
        test = group.loc[group.etapa.eq("teste")].set_index("metodo").wape_percentual
        selections.append(dict(tecnologia=tech, metodo=winner.metodo,
                               wape_validacao=winner.wape_percentual,
                               wape_teste=test[winner.metodo],
                               wape_persistencia_teste=test["persistencia"],
                               supera_persistencia_teste=bool(test[winner.metodo] < test["persistencia"])))
    return {"ml_macro_detalhe": frame, "ml_macro_metricas": metrics,
            "ml_macro_selecao": pd.DataFrame(selections)}


def main():
    sales = pd.read_parquet(SALES_INPUT)
    context = pd.read_parquet(MACRO_INPUT)
    macro = context.pivot(index="data_referencia", columns="indicador", values="valor").sort_index()
    frames = evaluate_macro(sales, macro)
    for name, frame in frames.items():
        frame["status"] = "experimento_retrospectivo_sem_vintages_sem_causalidade"
        frame["fonte_alvo"] = "ABVE"
        frame["fonte_contexto"] = "BCB_SGS"
        frame["sha256_alvo"] = hashlib.sha256(SALES_INPUT.read_bytes()).hexdigest()
        frame["sha256_contexto"] = hashlib.sha256(MACRO_INPUT.read_bytes()).hexdigest()
        frame["versao_sklearn"] = sklearn.__version__
        OUTPUT.mkdir(parents=True, exist_ok=True)
        frame.to_csv(OUTPUT / f"{name}.csv", index=False)
    print(frames["ml_macro_selecao"].to_string(index=False))
    # Não crio cenários de juros futuros nem previsões operacionais a partir deste teste.


if __name__ == "__main__":
    main()
