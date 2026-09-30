"""Baixo indicadores municipais oficiais do IBGE para complementar a análise de frota."""

from __future__ import annotations

import json
from pathlib import Path

import requests

# Encontro a raiz do projeto sem repetir o caminho do meu computador no código.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_PATH = PROJECT_ROOT / "data" / "bronze" / "ibge"
IBGE_API_URL = "https://apisidra.ibge.gov.br/values"
UF_CODES = [11, 12, 13, 14, 15, 16, 17, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 35, 41, 42, 43, 50, 51, 52, 53]


def download_sidra_table(table: int, variable: int, period: int, uf_code: int) -> list[dict[str, str]]:
    """Busco os municípios de uma UF para evitar uma chamada nacional pesada ao SIDRA."""
    url = f"{IBGE_API_URL}/t/{table}/n6/in%20n3%20{uf_code}/v/{variable}/p/{period}"
    response = requests.get(url, headers={"User-Agent": "Brazil-EV-Data-Platform"}, timeout=120)
    response.raise_for_status()
    return response.json()


def main() -> None:
    """Salvo as respostas brutas do IBGE por UF para manter a camada Bronze rastreável."""
    BRONZE_PATH.mkdir(parents=True, exist_ok=True)
    for uf_code in UF_CODES:
        # A tabela 5938 fornece PIB municipal; os valores divulgados são de 2023.
        pib_data = download_sidra_table(table=5938, variable=37, period=2023, uf_code=uf_code)
        pib_path = BRONZE_PATH / f"pib_municipal_2023_uf_{uf_code}.json"
        pib_path.write_text(json.dumps(pib_data, ensure_ascii=False), encoding="utf-8")

        # A tabela 4709 fornece a população residente do Censo Demográfico de 2022.
        population_data = download_sidra_table(table=4709, variable=93, period=2022, uf_code=uf_code)
        population_path = BRONZE_PATH / f"populacao_censo_2022_uf_{uf_code}.json"
        population_path.write_text(json.dumps(population_data, ensure_ascii=False), encoding="utf-8")
        print(f"UF {uf_code}: PIB 2023 e população 2022 baixados.")


if __name__ == "__main__":
    # Executo a coleta apenas quando chamo este arquivo diretamente pelo Python.
    main()
