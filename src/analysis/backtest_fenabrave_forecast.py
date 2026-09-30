"""Comparo baselines de previsão com meses que ficaram fora do treino."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "fenabrave" / "emplacamentos_mensais.parquet"
METRICS_PATH = PROJECT_ROOT / "data" / "portfolio" / "backtest_previsao_fenabrave.csv"
DETAIL_PATH = PROJECT_ROOT / "data" / "portfolio" / "backtest_detalhe_previsao_fenabrave.csv"
HOLDOUT_MONTHS = 7
TRAINING_MONTHS_MINIMUM = 24


def make_monthly_date(dataframe: pd.DataFrame) -> pd.Series:
    """Crio uma data mensal real para ordenar e descrever cada competência."""
    return pd.to_datetime(
        dataframe["ano_referencia"].astype(str)
        + "-"
        + dataframe["mes_referencia"].astype(str).str.zfill(2)
        + "-01"
    )


def forecast_holdout(values: np.ndarray, train_size: int) -> dict[str, np.ndarray]:
    """Gero previsões um passo à frente sem usar o valor que estou tentando prever."""
    forecasts: dict[str, list[float]] = {
        "persistencia_ultimo_mes": [],
        "media_movel_3_meses": [],
        "ingenuo_sazonal_12_meses": [],
    }

    for index in range(train_size, len(values)):
        forecasts["persistencia_ultimo_mes"].append(float(values[index - 1]))
        forecasts["media_movel_3_meses"].append(float(np.mean(values[index - 3 : index])))
        forecasts["ingenuo_sazonal_12_meses"].append(float(values[index - 12]))

    # Ajusto a tendência apenas no treino e a projeto para as competências de teste.
    training_indexes = np.arange(train_size, dtype=float)
    coefficients = np.polyfit(training_indexes, values[:train_size], deg=1)
    test_indexes = np.arange(train_size, len(values), dtype=float)
    forecasts["tendencia_linear"] = np.polyval(coefficients, test_indexes).tolist()
    return {name: np.asarray(prediction, dtype=float) for name, prediction in forecasts.items()}


def main() -> None:
    """Avalio os baselines, salvo o detalhe do teste e resumo os erros observados."""
    if not SILVER_PATH.exists():
        raise FileNotFoundError(
            "Silver FENABRAVE ausente. Execute primeiro a pipeline de ingestão e transformação."
        )

    source = pd.read_parquet(SILVER_PATH)
    comparable = source.loc[
        source["segmento_veiculos"].eq("autos_e_comerciais_leves")
    ].copy()
    comparable["data_referencia"] = make_monthly_date(comparable)

    details: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    for category, group in comparable.groupby("categoria_fenabrave", sort=True):
        group = group.sort_values("data_referencia").reset_index(drop=True)
        values = group["emplacamentos_mes"].to_numpy(dtype=float)
        train_size = len(values) - HOLDOUT_MONTHS
        if train_size < TRAINING_MONTHS_MINIMUM or train_size <= 12:
            raise ValueError(
                f"A série {category} tem {train_size} meses de treino; "
                f"preciso de pelo menos {TRAINING_MONTHS_MINIMUM}."
            )

        predictions = forecast_holdout(values, train_size)
        actual_values = values[train_size:]
        test_dates = group.loc[train_size:, "data_referencia"].tolist()
        train_dates = group.loc[: train_size - 1, "data_referencia"]

        for method, predicted_values in predictions.items():
            errors = predicted_values - actual_values
            absolute_errors = np.abs(errors)
            percentage_errors = absolute_errors / np.maximum(actual_values, 1) * 100
            summaries.append(
                {
                    "fonte": "FENABRAVE",
                    "categoria_fenabrave": category,
                    "segmento_veiculos": "autos_e_comerciais_leves",
                    "metodo": method,
                    "meses_treino": train_size,
                    "inicio_treino": train_dates.iloc[0].date().isoformat(),
                    "fim_treino": train_dates.iloc[-1].date().isoformat(),
                    "meses_teste": len(actual_values),
                    "inicio_teste": test_dates[0].date().isoformat(),
                    "fim_teste": test_dates[-1].date().isoformat(),
                    "mae": round(float(np.mean(absolute_errors)), 2),
                    "rmse": round(float(np.sqrt(np.mean(errors**2))), 2),
                    "mape_percentual": round(float(np.mean(percentage_errors)), 2),
                }
            )

            for index, (date, actual, predicted, error, absolute_error, percentage_error) in enumerate(
                zip(test_dates, actual_values, predicted_values, errors, absolute_errors, percentage_errors),
                start=1,
            ):
                details.append(
                    {
                        "fonte": "FENABRAVE",
                        "data_referencia": date.date().isoformat(),
                        "ano_referencia": date.year,
                        "mes_referencia": date.month,
                        "categoria_fenabrave": category,
                        "segmento_veiculos": "autos_e_comerciais_leves",
                        "metodo": method,
                        "emplacamentos_reais": int(actual),
                        "emplacamentos_previstos": round(float(predicted), 2),
                        "erro_previsto_menos_real": round(float(error), 2),
                        "erro_absoluto": round(float(absolute_error), 2),
                        "erro_percentual_absoluto": round(float(percentage_error), 2),
                        "passo_no_teste": index,
                    }
                )

    metrics_dataframe = pd.DataFrame(summaries).sort_values(
        ["categoria_fenabrave", "mae"]
    )
    details_dataframe = pd.DataFrame(details).sort_values(
        ["categoria_fenabrave", "data_referencia", "metodo"]
    )
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    metrics_dataframe.to_csv(METRICS_PATH, index=False, encoding="utf-8-sig")
    details_dataframe.to_csv(DETAIL_PATH, index=False, encoding="utf-8-sig")

    print(f"Backtest salvo: {METRICS_PATH} ({len(metrics_dataframe)} métricas).")
    print(f"Previsões no teste salvas: {DETAIL_PATH} ({len(details_dataframe)} linhas).")
    print(metrics_dataframe[["categoria_fenabrave", "metodo", "mae", "rmse", "mape_percentual"]].to_string(index=False))
    print("Esses resultados são um backtest; ainda não publico previsão futura como resultado validado.")


if __name__ == "__main__":
    # Inicio a avaliação somente depois de a Silver FENABRAVE existir.
    main()
