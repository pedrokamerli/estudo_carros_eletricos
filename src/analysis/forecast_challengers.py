"""Testo métodos sensíveis à tendência sem apagar o experimento anterior."""
import hashlib
import json
from importlib.metadata import version
from pathlib import Path
import numpy as np
import pandas as pd
from src.analysis.forecast_ml import METHODS, evaluate, predict

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/"data/portfolio"
# Registro os candidatos antes de executar. Não busco parâmetros no teste conhecido.
CHALLENGERS = METHODS+("drift_12m","holt_amortecido","tendencia_log_6m")

def challenger_predict(values, dates, origin, horizon, method):
    history = np.asarray(values[:origin],dtype=float)
    if method in METHODS:
        return predict(values,dates,origin,horizon,method)
    if method == "drift_12m":
        forecast = history[-1]+horizon*(history[-1]-history[-12])/11
    elif method == "holt_amortecido":
        # Uso equações de Holt com tendência amortecida e parâmetros fixos explícitos.
        alpha,beta,phi = .6,.2,.8
        level,trend = history[0],history[1]-history[0]
        for observed in history[1:]:
            previous = level
            level = alpha*observed+(1-alpha)*(level+phi*trend)
            trend = beta*(level-previous)+(1-beta)*phi*trend
        forecast = level+sum(phi**h for h in range(1,horizon+1))*trend
    elif method == "tendencia_log_6m":
        # Ajusto o ritmo recente somente com os seis últimos valores já conhecidos.
        x = np.arange(6,dtype=float)
        slope,intercept = np.polyfit(x,np.log1p(history[-6:]),1)
        forecast = np.expm1(intercept+slope*(5+horizon))
    else:
        raise ValueError("Método não registrado no protocolo.")
    if not np.isfinite(forecast):
        raise ValueError("Previsão não finita.")
    return max(0,float(forecast))

def main():
    source_path = DATA/"abve_publico_tecnologia_gold.csv"
    source = pd.read_csv(source_path,parse_dates=["data_referencia"])
    source = source.loc[source.tecnologia.isin(["BEV","PHEV"])].rename(columns={"tecnologia":"categoria_fenabrave","emplacamentos":"emplacamentos_mes"})
    frames = evaluate(source,methods=CHALLENGERS,predictor=challenger_predict)
    detail = frames["ml_backtest_detalhe"]
    bias = detail.groupby(["categoria_fenabrave","etapa","metodo","horizonte_meses"]).apply(
        lambda g:pd.Series({"vies_percentual":100*(g.previsto-g.real).sum()/g.real.sum(),
                           "meses_subestimados":int(g.previsto.lt(g.real).sum()),
                           "n_previsoes":len(g)}),include_groups=False).reset_index()
    frames["ml_diagnostico_vies"] = bias
    protocol = {"candidatos":CHALLENGERS,"holt":{"alpha":.6,"beta":.2,"phi":.8},
                "treino_inicial_meses":18,"validacao":"jul/2025–jan/2026","teste":"fev–ago/2026",
                "horizontes":[1,2,3],"selecao":"menor WAPE médio nos três horizontes da validação",
                "sha256_entrada":hashlib.sha256(source_path.read_bytes()).hexdigest(),
                "sha256_codigo_desafio":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "sha256_codigo_avaliador":hashlib.sha256((ROOT/"src/analysis/forecast_ml.py").read_bytes()).hexdigest(),
                "versao_numpy":np.__version__,"versao_sklearn":version("scikit-learn"),
                "limite":"Reanálise exploratória: resultados do teste já conhecidos no desenvolvimento. Sem teste prospectivo novo, sem aprovação operacional e sem intervalos novos.",
                "fonte_metodo":"https://otexts.com/fpp3/holt.html"}
    directory = ROOT/"output/analysis"
    directory.mkdir(parents=True,exist_ok=True)
    (directory/"ml_desafio_protocolo.json").write_text(json.dumps(protocol,ensure_ascii=False,indent=2),encoding="utf-8")
    for name,frame in frames.items():
        frame = frame.rename(columns={"categoria_fenabrave":"tecnologia"})
        # O avaliador é compartilhado, mas esta fonte/alvo são ABVE, não FENABRAVE.
        frame["fonte"] = "ABVE"
        frame["segmento_veiculos"] = "veiculos_leves_plugin"
        frame["sha256_entrada"] = protocol["sha256_entrada"]
        frame["tipo_avaliacao"] = "reanalise_exploratoria_teste_ja_conhecido"
        frame.to_csv(DATA/f"{name.replace('ml_','ml_desafio_',1)}.csv",index=False,float_format="%.6f")
    print(frames["ml_selecao_modelos"].to_string(index=False))

if __name__ == "__main__":
    main()
