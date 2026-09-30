"""Transformo os indicadores municipais brutos do IBGE em uma dimensão Silver."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IBGE_BRONZE_PATH = PROJECT_ROOT / "data" / "bronze" / "ibge"
IBGE_SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "ibge" / "indicadores_municipais.parquet"
LOCALITIES_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"


def normalize_municipality_name(value: str) -> str:
    """Crio uma chave de texto sem acentos para cruzar fontes que escrevem municípios de formas diferentes."""
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(character for character in normalized if not unicodedata.combining(character)).upper().strip()


def read_sidra_files(file_pattern: str, value_column: str) -> pd.DataFrame:
    """Uno os arquivos brutos por UF e mantenho código, nome e valor publicados pelo IBGE."""
    rows: list[dict[str, object]] = []
    for file_path in sorted(IBGE_BRONZE_PATH.glob(file_pattern)):
        records = json.loads(file_path.read_text(encoding="utf-8"))
        for record in records[1:]:
            rows.append(
                {
                    "codigo_ibge": str(record["D1C"]),
                    "municipio_ibge": record["D1N"],
                    value_column: float(record["V"]),
                }
            )
    return pd.DataFrame(rows)


def get_municipality_locations() -> pd.DataFrame:
    """Baixo a lista oficial de municípios para obter a UF associada a cada código IBGE."""
    response = pd.read_json(LOCALITIES_URL)
    locations = response[["id", "nome", "microrregiao"]].copy()
    locations["codigo_ibge"] = locations["id"].astype(str)
    def get_uf_code(item: dict[str, object]) -> str:
        """Uso a estrutura regional nova quando um município não possui microrregião antiga."""
        microregion = item["microrregiao"]
        if microregion is not None:
            return microregion["mesorregiao"]["UF"]["sigla"]

        # Boa Esperança do Norte (MT) usa apenas a regionalização imediata na API atual.
        immediate_region = item["regiao-imediata"]
        return immediate_region["regiao-intermediaria"]["UF"]["sigla"]

    locations["uf"] = response.apply(get_uf_code, axis=1)
    return locations[["codigo_ibge", "uf"]]


def main() -> None:
    """Crio uma dimensão econômica municipal com os anos de referência explícitos."""
    pib = read_sidra_files("pib_municipal_2023_uf_*.json", "pib_corrente_mil_reais_2023")
    population = read_sidra_files("populacao_censo_2022_uf_*.json", "populacao_censo_2022")
    income = read_sidra_files(
        "rendimento_per_capita_censo_2022_uf_*.json",
        "rendimento_domiciliar_per_capita_medio_2022_reais",
    )
    if pib.empty or population.empty or income.empty:
        raise FileNotFoundError("Execute primeiro a coleta Bronze do IBGE.")

    indicators = pib.merge(population, on=["codigo_ibge", "municipio_ibge"], how="inner")
    indicators = indicators.merge(income, on=["codigo_ibge", "municipio_ibge"], how="inner")
    indicators = indicators.merge(get_municipality_locations(), on="codigo_ibge", how="left")
    # O SIDRA acrescenta " - UF" ao município; removo isso só da chave usada no cruzamento.
    indicators["municipio_chave"] = indicators["municipio_ibge"].str.replace(
        r"\s-\s[A-Z]{2}$", "", regex=True
    ).map(normalize_municipality_name)
    # Calculo apenas uma aproximação, pois PIB e população possuem anos de referência diferentes.
    indicators["pib_per_capita_aproximado"] = (
        indicators["pib_corrente_mil_reais_2023"] * 1_000 / indicators["populacao_censo_2022"]
    )
    indicators["fonte"] = (
        "IBGE SIDRA: tabela 5938 (PIB 2023), 4709 (população 2022) "
        "e 10295/variável 13431 (renda domiciliar per capita 2022)"
    )

    IBGE_SILVER_PATH.parent.mkdir(parents=True, exist_ok=True)
    indicators.to_parquet(IBGE_SILVER_PATH, index=False)
    print(f"Municípios IBGE processados: {len(indicators)}")
    print(f"Arquivo Silver: {IBGE_SILVER_PATH}")


if __name__ == "__main__":
    # Executo a transformação somente depois da coleta Bronze estar pronta.
    main()
