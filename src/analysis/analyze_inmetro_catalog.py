"""Resumo o catálogo técnico do Inmetro sem tratá-lo como base de vendas."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "portfolio"


def main() -> None:
    frame = pd.read_csv(DATA / "inmetro_versoes_eletrificadas.csv")
    frame["autonomia_eletrica_ensaio_km"] = pd.to_numeric(frame["autonomia_eletrica_ensaio_km"], errors="coerce")
    frame["consumo_energetico_mj_km"] = pd.to_numeric(frame["consumo_energetico_mj_km"], errors="coerce")
    valid = frame.dropna(subset=["marca", "modelo", "ano_ciclo"]).copy()
    by_brand = (valid.groupby(["ano_ciclo", "marca"], as_index=False)
                .agg(versoes_catalogadas=("id_registro", "nunique"),
                     modelos_catalogados=("modelo", "nunique"),
                     autonomia_mediana_ensaio_km=("autonomia_eletrica_ensaio_km", "median"),
                     consumo_mediano_mj_km=("consumo_energetico_mj_km", "median")))
    by_brand["limite_uso"] = "Catálogo PBEV/Inmetro; não representa vendas, preço ou autonomia real em trânsito."
    by_brand.to_csv(DATA / "inmetro_catalogo_marca_ano.csv", index=False)
    by_model = (valid.groupby(["marca", "modelo"], as_index=False)
                .agg(anos_catalogados=("ano_ciclo", lambda s: ",".join(map(str, sorted(set(s))))),
                     versoes_catalogadas=("id_registro", "nunique"),
                     autonomia_min_ensaio_km=("autonomia_eletrica_ensaio_km", "min"),
                     autonomia_mediana_ensaio_km=("autonomia_eletrica_ensaio_km", "median"),
                     autonomia_max_ensaio_km=("autonomia_eletrica_ensaio_km", "max"),
                     consumo_mediano_mj_km=("consumo_energetico_mj_km", "median")))
    by_model["limite_uso"] = "Modelo técnico catalogado; não cruzado automaticamente com emplacamentos."
    by_model.to_csv(DATA / "inmetro_catalogo_modelo.csv", index=False)
    print(f"Inmetro: {len(by_brand)} linhas marca/ano e {len(by_model)} modelos técnicos resumidos.")


if __name__ == "__main__":
    main()
