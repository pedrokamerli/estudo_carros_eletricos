"""Enriqueço modelos de Bauru somente quando a nomenclatura coincide exatamente."""
from __future__ import annotations

import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "portfolio"


def key(*parts: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", " ".join(str(p or "").upper() for p in parts))


def main() -> None:
    local = pd.read_csv(DATA / "bauru_modelos_ranking.csv")
    inmetro = pd.read_csv(DATA / "inmetro_versoes_eletrificadas.csv")
    prices = pd.read_csv(DATA / "precos_historicos_documentais.csv")
    local["chave_marca"] = local.marca.map(key)
    local["modelo_norm"] = local.modelo.map(key)
    inmetro["chave_marca"] = inmetro.marca.map(key)
    inmetro["modelo_norm"] = inmetro.modelo.map(key)
    # Faço o pareamento no nível de modelo, nunca invento uma versão ABVE.
    matches = []
    for row in local[["marca", "modelo", "chave_marca", "modelo_norm"]].drop_duplicates().itertuples(index=False):
        candidates = inmetro[(inmetro.chave_marca == row.chave_marca) & inmetro.modelo_norm.map(lambda value: value in row.modelo_norm)]
        if not candidates.empty:
            matches.append(candidates.assign(chave_modelo=key(row.marca, row.modelo), modelo_abve=row.modelo))
    matched_inmetro = pd.concat(matches, ignore_index=True) if matches else inmetro.iloc[0:0].copy()
    tech = (matched_inmetro.groupby("chave_modelo", as_index=False)
            .agg(anos_inmetro=("ano_ciclo", lambda s: ",".join(map(str, sorted(set(s))))),
                 versoes_inmetro=("id_registro", "nunique"),
                 autonomia_mediana_ensaio_km=("autonomia_eletrica_ensaio_km", "median"),
                 consumo_mediano_mj_km=("consumo_energetico_mj_km", "median")))
    tech["nivel_match_inmetro"] = "modelo_sem_versao"
    prices["chave_marca"] = prices.marca.map(key)
    prices["modelo_norm"] = prices.modelo_versao.map(key)
    price_matches = []
    for row in local[["marca", "modelo", "chave_marca", "modelo_norm"]].drop_duplicates().itertuples(index=False):
        candidates = prices[(prices.chave_marca == row.chave_marca) & prices.modelo_norm.map(lambda value: value in row.modelo_norm)]
        if not candidates.empty:
            price_matches.append(candidates.assign(chave_modelo=key(row.marca, row.modelo)))
    matched_prices = pd.concat(price_matches, ignore_index=True) if price_matches else prices.iloc[0:0].copy()
    price = (matched_prices.groupby("chave_modelo", as_index=False)
             .agg(anuncios_preco=("preco_anunciado_reais", "size"),
                  preco_mediano_reais=("preco_anunciado_reais", "median"),
                  data_preco_inicio=("data_anuncio", "min"), data_preco_fim=("data_anuncio", "max")))
    local["chave_modelo"] = local.apply(lambda r: key(r.marca, r.modelo), axis=1)
    result = local.merge(tech, on="chave_modelo", how="left").merge(price, on="chave_modelo", how="left")
    result["status_inmetro"] = result.autonomia_mediana_ensaio_km.notna().map({True: "modelo_correspondido_sem_versao", False: "sem_correspondencia_segura"})
    result["status_preco"] = result.preco_mediano_reais.notna().map({True: "modelo_correspondido_sem_versao", False: "sem_correspondencia_segura"})
    result["limite_enriquecimento"] = "Pareamento conservador no nível de modelo; a versão não é atribuída. Inmetro é ensaio, preço é anúncio, ABVE é emplacamento."
    result.drop(columns=["chave_modelo", "chave_marca", "modelo_norm"], inplace=True)
    result.to_csv(DATA / "bauru_modelos_tecnologia_preco.csv", index=False)
    print(f"Bauru enriquecido: {len(result)} modelos; Inmetro {result.status_inmetro.str.startswith('modelo_').sum()} matches de modelo; preço {result.status_preco.str.startswith('modelo_').sum()} matches de modelo.")


if __name__ == "__main__":
    main()
