"""Valido o snapshot geográfico de recarga publicado pela ABVE/Tupi."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "data" / "portfolio" / "infraestrutura_recarga_abve_snapshot.csv"
SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "abve"
PARQUET_PATH = SILVER_PATH / "infraestrutura_recarga.parquet"
KEY_COLUMNS = ["nivel_geografico", "regiao", "municipio", "uf"]
COUNT_COLUMNS = ["posicao", "pontos_ac", "pontos_dc", "pontos_total"]
PERCENTAGE_COLUMN = "participacao_nacional_percentual"
DATE_COLUMNS = ["data_referencia", "data_publicacao", "data_captura"]


def main() -> None:
    """Confiro totais, rankings parciais e participação regional sem extrapolar dados."""
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"Snapshot de recarga não encontrado: {SOURCE_PATH}")

    dataframe = pd.read_csv(SOURCE_PATH, dtype="string")
    required = KEY_COLUMNS + COUNT_COLUMNS + [PERCENTAGE_COLUMN] + DATE_COLUMNS + [
        "escopo_ranking", "url_fonte", "metodo_extracao"
    ]
    missing = sorted(set(required) - set(dataframe.columns))
    if missing:
        raise ValueError(f"Colunas ausentes no snapshot de recarga: {missing}")

    for column in COUNT_COLUMNS + [PERCENTAGE_COLUMN]:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="raise").astype("Int64" if column in COUNT_COLUMNS else "Float64")
    for column in DATE_COLUMNS:
        dataframe[column] = pd.to_datetime(dataframe[column], format="%Y-%m-%d", errors="raise").dt.date

    if dataframe[DATE_COLUMNS + ["url_fonte", "metodo_extracao"]].isna().any().any():
        raise ValueError("O snapshot contém data ou metadado de fonte vazio.")
    if dataframe.duplicated(KEY_COLUMNS).any():
        raise ValueError("O snapshot contém localidades duplicadas no mesmo nível geográfico.")
    if dataframe[COUNT_COLUMNS + [PERCENTAGE_COLUMN]].stack().lt(0).any():
        raise ValueError("O snapshot contém contagem ou participação negativa.")

    national = dataframe.loc[dataframe["nivel_geografico"].eq("nacional")]
    regions = dataframe.loc[dataframe["nivel_geografico"].eq("regiao")]
    municipalities = dataframe.loc[dataframe["nivel_geografico"].eq("municipio")]
    states = dataframe.loc[dataframe["nivel_geografico"].eq("estado")]
    if len(national) != 1 or len(regions) != 5 or len(municipalities) != 20 or len(states) != 20:
        raise ValueError("Esperava 1 total nacional, 5 regiões e os rankings das 20 cidades/UFs.")

    national_row = national.iloc[0]
    if (
        national_row["pontos_ac"] != 18_469
        or national_row["pontos_dc"] != 11_397
        or national_row["pontos_total"] != 29_866
        or national_row[PERCENTAGE_COLUMN] != 100.0
    ):
        raise ValueError("O total nacional não confere com o publicado pela ABVE/Tupi.")
    if (national_row["pontos_ac"] + national_row["pontos_dc"]) != national_row["pontos_total"]:
        raise ValueError("Pontos AC + DC não fecham com o total nacional.")

    for subset in (municipalities, states):
        if subset["escopo_ranking"].ne("top20").any():
            raise ValueError("O escopo do ranking foi alterado; não trate o top 20 como censo completo.")
        if not (subset["pontos_ac"] + subset["pontos_dc"]).equals(subset["pontos_total"]):
            raise ValueError("Pontos AC + DC não fecham em uma linha do ranking.")
        for _, group in subset.groupby("nivel_geografico"):
            if set(group["posicao"].astype(int)) != set(range(1, 21)):
                raise ValueError("O ranking precisa conter as posições de 1 a 20 sem lacunas.")

    if not regions[PERCENTAGE_COLUMN].sum().round(1) == 100.0:
        raise ValueError("As participações regionais não somam 100%.")
    if regions[["pontos_ac", "pontos_dc", "pontos_total"]].notna().any().any():
        raise ValueError("A fonte publicou participação percentual por região, não contagens regionais.")
    if dataframe["data_referencia"].nunique() != 1 or national_row["data_referencia"].isoformat() != "2026-08-31":
        raise ValueError("O snapshot não corresponde à referência de agosto/2026.")

    SILVER_PATH.mkdir(parents=True, exist_ok=True)
    dataframe.to_parquet(PARQUET_PATH, index=False)
    print(f"Silver de recarga validada: {len(dataframe)} linhas em {PARQUET_PATH}")
    print("Escopo: total nacional, participação por 5 regiões e rankings top 20 de municípios/UFs.")


if __name__ == "__main__":
    # Inicio a transformação apenas quando executo este módulo diretamente.
    main()
