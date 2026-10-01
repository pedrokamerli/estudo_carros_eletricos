"""Comparo ML e referências simples respeitando a ordem temporal dos dados."""

from pathlib import Path
from hashlib import sha256

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.analysis.backtest_fenabrave_forecast import SILVER_PATH, make_monthly_date


OUTPUT = Path(__file__).resolve().parents[2] / "data" / "portfolio"
METHODS = ("persistencia", "media_3m", "sazonal_12m", "ridge", "random_forest")
HORIZONS = (1, 2, 3)
MIN_TRAIN = 18
TEST_MONTHS = 7


def features(values, dates, origin, horizon):
    """Uso apenas valores anteriores à origem; o calendário futuro já é conhecido."""
    target_month = (dates[origin - 1] + pd.DateOffset(months=horizon)).month
    history = np.log1p(np.asarray(values[:origin], dtype=float))
    return [history[-1], history[-2], history[-3], history[-3:].mean(),
            origin + horizon - 1, np.sin(2 * np.pi * target_month / 12),
            np.cos(2 * np.pi * target_month / 12)]


def predict(values, dates, origin, horizon, method):
    """Ajusto um modelo direto para cada horizonte, sem receber alvos futuros."""
    history = np.asarray(values[:origin], dtype=float)
    if method == "persistencia":
        return float(history[-1])
    if method == "media_3m":
        return float(history[-3:].mean())
    if method == "sazonal_12m":
        return float(history[origin + horizon - 1 - 12])
    # Cada exemplo de treino termina antes da origem atual, inclusive seu alvo.
    training_origins = range(3, origin - horizon + 1)
    x = np.asarray([features(history, dates, i, horizon) for i in training_origins])
    y = np.log1p([history[i + horizon - 1] for i in training_origins])
    model = (make_pipeline(StandardScaler(), Ridge(alpha=10.0)) if method == "ridge"
             else RandomForestRegressor(n_estimators=100, max_depth=3,
                                        min_samples_leaf=3, random_state=42, n_jobs=1))
    model.fit(x, y)
    prediction = np.expm1(model.predict([features(history, dates, origin, horizon)])[0])
    if not np.isfinite(prediction):
        raise ValueError("O modelo produziu uma previsão não finita.")
    return max(0.0, float(prediction))


def validate_series(group):
    """Barro lacunas, duplicidade e valores inválidos antes da avaliação temporal."""
    dates = pd.DatetimeIndex(group["data_referencia"])
    expected = pd.date_range(dates.min(), dates.max(), freq="MS")
    if not dates.equals(expected):
        raise ValueError("A série precisa ter meses contínuos e únicos.")
    values = group["emplacamentos_mes"].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Emplacamentos precisam ser finitos e não negativos.")
    if len(values) - TEST_MONTHS < MIN_TRAIN + 6:
        raise ValueError("Preciso de treino, seis meses de validação e sete meses de teste.")
    return values, dates


def evaluate(source):
    """Avalio um alvo mensal comparável, com seleção antes dos meses de teste."""
    rows, futures = [], []
    for category, group in source.groupby("categoria_fenabrave", sort=True):
        group = group.sort_values("data_referencia")
        values, dates = validate_series(group)
        split = len(values) - TEST_MONTHS
        for stage, start, end in (("validacao", MIN_TRAIN, split), ("teste", split, len(values))):
            for origin in range(start, end):
                for horizon in HORIZONS:
                    target = origin + horizon - 1
                    if target >= end:
                        continue
                    for method in METHODS:
                        predicted = predict(values, dates, origin, horizon, method)
                        rows.append(dict(categoria_fenabrave=category, etapa=stage,
                                         metodo=method, horizonte_meses=horizon,
                                         fim_treino=dates[origin - 1].date().isoformat(),
                                         data_referencia=dates[target].date().isoformat(),
                                         real=float(values[target]), previsto=predicted))
    detail = pd.DataFrame(rows)
    detail["erro_absoluto"] = (detail["previsto"] - detail["real"]).abs()
    summaries = []
    for key, group in detail.groupby(["categoria_fenabrave", "etapa", "metodo", "horizonte_meses"]):
        error = group["previsto"] - group["real"]
        summaries.append(dict(zip(["categoria_fenabrave", "etapa", "metodo", "horizonte_meses"], key),
                              n_previsoes=len(group), mae=group["erro_absoluto"].mean(),
                              rmse=np.sqrt((error ** 2).mean()),
                              wape_percentual=100 * group["erro_absoluto"].sum() / group["real"].sum()))
    metrics = pd.DataFrame(summaries)
    selections = []
    for category, group in metrics.groupby("categoria_fenabrave"):
        # Dou peso igual aos três horizontes e congelo a escolha antes de ver o teste.
        scores = group.loc[group["etapa"].eq("validacao")].groupby("metodo")["wape_percentual"].mean()
        selected = scores.sort_values(kind="stable").index[0]
        test = group.loc[group["etapa"].eq("teste")].groupby("metodo")["wape_percentual"].mean()
        selections.append(dict(categoria_fenabrave=category, metodo=selected,
                               wape_validacao_medio=float(scores[selected]),
                               wape_teste_medio=float(test[selected]),
                               wape_persistencia_teste=float(test["persistencia"]),
                               supera_persistencia_teste=bool(test[selected] < test["persistencia"]),
                               status_avaliacao=("referencia_simples" if selected == "persistencia"
                                                else "supera_referencia_no_teste" if test[selected] < test["persistencia"]
                                                else "nao_supera_referencia_no_teste")))
        series = source.loc[source["categoria_fenabrave"].eq(category)].sort_values("data_referencia")
        values, dates = validate_series(series)
        for horizon in HORIZONS:
            futures.append(dict(fonte="FENABRAVE", categoria_fenabrave=category,
                                segmento_veiculos="autos_e_comerciais_leves", metodo=selected,
                                fim_treino=dates[-1].date().isoformat(), horizonte_meses=horizon,
                                data_referencia=(dates[-1] + pd.DateOffset(months=horizon)).date().isoformat(),
                                emplacamentos_previstos=predict(values, dates, len(values), horizon, selected),
                                status="projecao_experimental_sem_intervalo_calibrado"))
    return {"ml_backtest_detalhe": detail, "ml_backtest_metricas": metrics,
            "ml_selecao_modelos": pd.DataFrame(selections),
            "ml_projecoes_experimentais": pd.DataFrame(futures)}


def main():
    """Escolho na validação, avalio no teste e projeto três meses como experimento."""
    source = pd.read_parquet(SILVER_PATH)
    source = source.loc[source["segmento_veiculos"].eq("autos_e_comerciais_leves")].copy()
    source["data_referencia"] = make_monthly_date(source)
    frames = evaluate(source)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, dataframe in frames.items():
        # Registro a entrada exata e a versão da biblioteca para rastrear o experimento.
        dataframe["fonte"] = "FENABRAVE"
        dataframe["segmento_veiculos"] = "autos_e_comerciais_leves"
        dataframe["sha256_silver"] = sha256(SILVER_PATH.read_bytes()).hexdigest()
        dataframe["versao_sklearn"] = sklearn.__version__
        dataframe.to_csv(OUTPUT / f"{name}.csv", index=False, float_format="%.4f")
        print(f"{name}: {len(dataframe)} linhas")
    print(frames["ml_selecao_modelos"].to_string(index=False))


if __name__ == "__main__":
    main()
