"""Comparo previsões congeladas com novos meses, sem retreinar ou inventar observações."""
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from src.analysis.bauru_case import ROOT, DATA


def evaluate(registry, observed, now):
    observed = observed.copy()
    observed["data_referencia"] = pd.to_datetime(observed.data_referencia)
    if observed.duplicated(["tecnologia","data_referencia"]).any():
        raise ValueError("Observações mensais duplicadas; não somo versões da mesma evidência.")
    amounts = pd.to_numeric(observed.emplacamentos,errors="raise")
    if amounts.isna().any() or not np.isfinite(amounts).all() or amounts.lt(0).any() or amounts.mod(1).ne(0).any():
        raise ValueError("Emplacamentos observados precisam ser contagens inteiras não negativas.")
    registered = pd.Timestamp(registry["registrado_em_utc"]).tz_convert(None).replace(day=1).normalize()
    current_month = pd.Timestamp(now.date()).replace(day=1)
    rows = []
    for prediction in registry["previsoes"]:
        target = pd.Timestamp(prediction["data_referencia"])
        if target <= registered:
            raise ValueError("Alvo não era futuro no mês de registro.")
        actual = observed.loc[observed.tecnologia.eq(prediction["tecnologia"]) & observed.data_referencia.eq(target)]
        ready = target < current_month and len(actual) == 1
        value = int(actual.emplacamentos.iloc[0]) if ready else None
        forecast = float(prediction["emplacamentos_previstos"])
        if not np.isfinite(forecast) or forecast < 0:
            raise ValueError("Previsão congelada inválida.")
        rows.append(dict(tecnologia=prediction["tecnologia"],data_referencia=target.date().isoformat(),
            previsto_congelado=forecast,observado=value,erro_absoluto=abs(forecast-value) if ready else None,
            erro_percentual=100*abs(forecast-value)/value if ready and value else None,
            status="comparado_com_observacao_posterior" if ready else "aguardando_mes_encerrado_e_observacao",
            registrado_em_utc=registry["registrado_em_utc"],avaliado_em_utc=now.isoformat(),
            limite="Registro prospectivo de um único horizonte/tecnologia, não aprovação operacional. Sem observado não calculo erro; valor zero não recebe erro percentual infinito."))
    return pd.DataFrame(rows)


def main():
    registry = json.loads((ROOT/"data/registry/previsoes_congeladas_2026_10.json").read_text(encoding="utf-8"))
    observed = pd.read_csv(DATA/"abve_publico_tecnologia_gold.csv")
    observed["data_referencia"] = pd.to_datetime(dict(year=observed.ano_referencia,month=observed.mes_referencia,day=1))
    result = evaluate(registry,observed,datetime.now(timezone.utc))
    result.to_csv(DATA/"ml_avaliacao_prospectiva.csv",index=False)
    print(result[["tecnologia","data_referencia","status"]].to_string(index=False))


if __name__ == "__main__":
    main()
