"""Baixo o cadastro oficial de geração distribuída da ANEEL e resumo Bauru.

O arquivo é usado como contexto municipal de oferta solar. Ele não identifica
o dono de cada carro e, portanto, não prova que uma recarga ocorreu em casa.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BRONZE = ROOT / "data" / "bronze" / "aneel"
OUTPUT = ROOT / "data" / "portfolio" / "bauru_solar_context.csv"
URL = "https://dadosabertos.aneel.gov.br/dataset/5e0fafd2-21b9-4d5b-b622-40438d40aba2/resource/cd29f6eb-e08d-4db7-b6fb-ed6e3b682d27/download/empreendimento-geracao-distribuida.parquet"


def _find_column(frame: pd.DataFrame, names: tuple[str, ...]) -> str:
    normalized = {str(c).strip().upper(): c for c in frame.columns}
    for name in names:
        if name in normalized:
            return str(normalized[name])
    raise KeyError(f"Não encontrei coluna entre {names}. Colunas: {list(frame.columns)}")


def main() -> None:
    BRONZE.mkdir(parents=True, exist_ok=True)
    target = BRONZE / "empreendimento-geracao-distribuida.parquet"
    if not target.exists():
        with requests.get(URL, stream=True, timeout=180) as response:
            response.raise_for_status()
            with target.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output.write(chunk)
    frame = pd.read_parquet(target)
    city = _find_column(frame, ("MUNICIPIO", "MUNICÍPIO", "NOMMUNICIPIO"))
    uf = _find_column(frame, ("UF", "SIGUF"))
    source = _find_column(frame, ("FONTE", "FONTE_GERACAO", "FONTE GERACAO", "DSCFONTEGERACAO"))
    capacity = _find_column(frame, ("POTENCIA_INSTALADA_KW", "POTÊNCIA_INSTALADA_KW", "POTENCIA INSTALADA (KW)", "MDAPOTENCIAINSTALADAKW"))
    filtered = frame[(frame[city].astype(str).str.upper().str.strip() == "BAURU") & (frame[uf].astype(str).str.upper().str.strip() == "SP")].copy()
    if filtered.empty:
        raise ValueError("A ANEEL não retornou empreendimentos de Bauru/SP.")
    capacity_numeric = pd.to_numeric(filtered[capacity], errors="coerce").fillna(0)
    # A ANEEL nomeia a fonte como "Radiação solar" no cadastro atual.
    solar_mask = filtered[source].astype(str).str.upper().str.contains("SOLAR|FOTOVOLTA", na=False, regex=True)
    summary = pd.DataFrame([{
        "municipio": "BAURU",
        "uf": "SP",
        "empreendimentos_geracao_distribuida": int(len(filtered)),
        "empreendimentos_fotovoltaicos": int(solar_mask.sum()),
        "potencia_total_kw": round(float(capacity_numeric.sum()), 3),
        "potencia_fotovoltaica_kw": round(float(capacity_numeric[solar_mask].sum()), 3),
        "fonte": "ANEEL - Relação de empreendimentos de geração distribuída",
        "arquivo_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "observacao": "Contexto municipal de geração distribuída; não identifica proprietários de veículos nem local de recarga.",
    }])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"ANEEL: {len(filtered)} empreendimentos em Bauru; resumo salvo em {OUTPUT}.")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
