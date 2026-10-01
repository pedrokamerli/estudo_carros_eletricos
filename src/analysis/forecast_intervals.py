"""Separo seleção, calibração e teste para auditar faixas experimentais de um mês."""

import math
import numpy as np
import pandas as pd
from src.analysis.forecast_ml import OUTPUT, predict


def calibrate(group, level=0.80):
    """Escolho pelos primeiros três alvos e calibro nos quatro restantes da validação."""
    group = group.copy()
    group["data_referencia"] = pd.to_datetime(group.data_referencia)
    group = group.loc[group.horizonte_meses.eq(1)]
    validation = group.loc[group.etapa.eq("validacao")]
    dates = sorted(validation.data_referencia.unique())
    if len(dates) != 7:
        raise ValueError("Preciso de sete meses de validação para este protocolo separado.")
    selection = validation.loc[validation.data_referencia.isin(dates[:3])]
    scores = selection.groupby("metodo").erro_absoluto.sum() / selection.groupby("metodo").real.sum()
    method = scores.sort_values(kind="stable").index[0]
    calibration = validation.loc[validation.metodo.eq(method) & validation.data_referencia.isin(dates[3:])]
    if len(calibration) != 4 or (calibration.previsto <= 0).any():
        raise ValueError("Calibração incompleta ou previsão não positiva.")
    residual = (calibration.real - calibration.previsto).abs() / calibration.previsto
    rank = math.ceil((len(residual) + 1) * level)
    if rank > len(residual):
        raise ValueError("A amostra não suporta esse nível nominal com quantil finito.")
    q = float(np.sort(residual)[rank - 1])
    test = group.loc[group.etapa.eq("teste") & group.metodo.eq(method)].copy()
    if test.empty or test.data_referencia.min() <= calibration.data_referencia.max():
        raise ValueError("Teste precisa ocorrer após toda a calibração.")
    test["limite_inferior"] = (test.previsto * (1 - q)).clip(lower=0)
    test["limite_superior"] = test.previsto * (1 + q)
    test["coberto"] = test.real.between(test.limite_inferior, test.limite_superior)
    return method, q, test, calibration.data_referencia.max()


def main():
    details, reports, futures = [], [], []
    for source, key, filename in (("SENATRAN_frota", "regiao", "ml_frota_regional_backtest_detalhe.csv"),
                                  ("ABVE_emplacamentos", "tecnologia", "ml_abve_backtest_detalhe.csv")):
        frame = pd.read_csv(OUTPUT / filename)
        for target, group in frame.groupby(key):
            method, q, test, calibration_end = calibrate(group)
            test["fonte_alvo"] = source
            test["alvo"] = target
            test["nivel_nominal_percentual"] = 80
            test["fim_calibracao"] = calibration_end
            test["status"] = "experimental_sem_garantia_temporal"
            details.append(test[["fonte_alvo", "alvo", "metodo", "data_referencia", "fim_treino", "real", "previsto", "limite_inferior", "limite_superior", "coberto", "nivel_nominal_percentual", "fim_calibracao", "status"]])
            coverage = 100 * test.coberto.mean()
            reports.append(dict(fonte_alvo=source, alvo=target, metodo=method, n_selecao=3, n_calibracao=4,
                                n_teste=len(test), nivel_nominal_percentual=80, cobertura_teste_percentual=coverage,
                                amplitude_media=float((test.limite_superior - test.limite_inferior).mean()),
                                quantil_erro_relativo=q, fim_calibracao=calibration_end,
                                status="cobertura_insuficiente" if coverage < 80 else "cobertura_observada_amostra_pequena_nao_aprovado"))
            series = pd.read_csv(OUTPUT / ("frota_regional_mensal.csv" if key == "regiao" else "abve_plugin_mensais.csv"))
            series = series.loc[series[key].eq(target)].sort_values("data_referencia")
            dates = pd.DatetimeIndex(pd.to_datetime(series.data_referencia))
            value_col = "total_veiculos_eletrificados" if key == "regiao" else "emplacamentos_mes"
            values = series[value_col].to_numpy(dtype=float)
            predicted = predict(values, dates, len(values), 1, method)
            futures.append(dict(fonte_alvo=source, alvo=target, metodo=method,
                                fim_treino=dates[-1], data_referencia=dates[-1] + pd.DateOffset(months=1),
                                previsto=predicted, limite_inferior=max(0, predicted * (1 - q)),
                                limite_superior=predicted * (1 + q), nivel_nominal_percentual=80,
                                status="experimental_sem_garantia_temporal"))
    for name, frame in (("ml_intervalos_detalhe", pd.concat(details, ignore_index=True)),
                        ("ml_intervalos_cobertura", pd.DataFrame(reports)),
                        ("ml_intervalos_projecoes", pd.DataFrame(futures))):
        frame.to_csv(OUTPUT / f"{name}.csv", index=False)
    print(pd.DataFrame(reports).to_string(index=False))


if __name__ == "__main__":
    main()
