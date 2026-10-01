"""Coleto contexto econômico mensal oficial, sem chave e sem inventar lacunas."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
BRONZE = ROOT / "data/bronze/bcb"
OUTPUT = ROOT / "data/silver/contexto_bcb.parquet"
SERIES = {
    433: "ipca_variacao_mensal",
    4390: "selic_acumulada_mes",
    25471: "juros_pf_aquisicao_veiculos_mes",
}
PERIODS = pd.date_range("2024-01-01", "2026-08-01", freq="MS")


def normalize(payload, code):
    """Exijo um valor por mês e preservo inflação negativa, que pode ser legítima."""
    frame = pd.DataFrame(payload)
    if set(frame.columns) != {"data", "valor"}:
        raise ValueError("Estrutura inesperada na resposta SGS.")
    frame["data_referencia"] = pd.to_datetime(frame["data"], format="%d/%m/%Y", errors="raise")
    frame["valor"] = pd.to_numeric(frame["valor"], errors="raise")
    frame = frame.sort_values("data_referencia")
    if not pd.DatetimeIndex(frame.data_referencia).equals(PERIODS):
        raise ValueError("SGS com mês ausente, duplicado ou fora do recorte.")
    if frame.valor.isna().any() or not frame.valor.map(lambda x: float("-inf") < x < float("inf")).all():
        raise ValueError("Valor econômico nulo ou não finito.")
    if code != 433 and frame.valor.lt(0).any():
        raise ValueError("Taxa de juros negativa precisa de revisão.")
    frame["codigo_sgs"] = code
    frame["indicador"] = SERIES[code]
    frame["unidade"] = "percentual_ao_mes"
    return frame.drop(columns="data")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Busco uma nova versão, mantendo snapshots anteriores.")
    args = parser.parse_args()
    BRONZE.mkdir(parents=True, exist_ok=True)
    frames = []
    for code in SERIES:
        cache = BRONZE / f"sgs_{code}_202401_202608.json"
        # O envelope guarda resposta, URL e captura juntos: cache não muda a data da coleta.
        if cache.exists() and not args.refresh:
            envelope = json.loads(cache.read_text(encoding="utf-8"))
        else:
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
            response = requests.get(url, params={"formato": "json", "dataInicial": "01/01/2024", "dataFinal": "31/08/2026"}, timeout=45)
            response.raise_for_status()
            payload = response.json()
            normalize(payload, code)  # Não publico uma captura incompleta como válida.
            envelope = {"url_fonte": response.url, "data_captura": datetime.now(timezone.utc).isoformat(), "dados": payload}
            serialized = json.dumps(envelope, ensure_ascii=False, indent=2)
            digest = hashlib.sha256(serialized.encode()).hexdigest()
            (BRONZE / f"snapshot_{code}_{digest}.json").write_text(serialized, encoding="utf-8")
            temporary = cache.with_suffix(".part")
            temporary.write_text(serialized, encoding="utf-8")
            temporary.replace(cache)
        frame = normalize(envelope["dados"], code)
        frame["url_fonte"] = envelope["url_fonte"]
        frame["data_captura"] = envelope["data_captura"]
        frame["data_publicacao"] = None  # SGS não devolve a data histórica de divulgação.
        frame["sha256_snapshot"] = hashlib.sha256(json.dumps(envelope, sort_keys=True).encode()).hexdigest()
        frames.append(frame)
    combined = pd.concat(frames, ignore_index=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(OUTPUT, index=False)
    print(f"BCB: {len(combined)} observações reais, três indicadores, 32 meses por indicador.")


if __name__ == "__main__":
    main()
