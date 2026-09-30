"""Baixo indicadores municipais oficiais do IBGE para complementar a análise de frota."""

from __future__ import annotations

import json
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Encontro a raiz do projeto sem repetir o caminho do meu computador no código.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_PATH = PROJECT_ROOT / "data" / "bronze" / "ibge"
IBGE_API_URL = "https://apisidra.ibge.gov.br/values"
UF_CODES = [11, 12, 13, 14, 15, 16, 17, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 35, 41, 42, 43, 50, 51, 52, 53]
SESSION = requests.Session()
SESSION.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=5,
            connect=5,
            read=3,
            status=5,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
        )
    ),
)


def download_sidra_table(table: int, variable: int, period: int, uf_code: int) -> list[dict[str, str]]:
    """Busco os municípios de uma UF para evitar uma chamada nacional pesada ao SIDRA."""
    url = f"{IBGE_API_URL}/t/{table}/n6/in%20n3%20{uf_code}/v/{variable}/p/{period}"
    response = SESSION.get(url, headers={"User-Agent": "Brazil-EV-Data-Platform"}, timeout=120)
    response.raise_for_status()
    return response.json()


def main() -> None:
    """Salvo as respostas brutas do IBGE por UF para manter a camada Bronze rastreável."""
    BRONZE_PATH.mkdir(parents=True, exist_ok=True)
    for uf_code in UF_CODES:
        # A tabela 5938 fornece PIB municipal; os valores divulgados são de 2023.
        pib_path = BRONZE_PATH / f"pib_municipal_2023_uf_{uf_code}.json"
        pib_data = load_or_download(pib_path, table=5938, variable=37, period=2023, uf_code=uf_code)

        # A tabela 4709 fornece a população residente do Censo Demográfico de 2022.
        population_path = BRONZE_PATH / f"populacao_censo_2022_uf_{uf_code}.json"
        population_data = load_or_download(
            population_path, table=4709, variable=93, period=2022, uf_code=uf_code
        )

        # A tabela 10295/variável 13431 informa renda domiciliar per capita média do Censo.
        income_path = BRONZE_PATH / f"rendimento_per_capita_censo_2022_uf_{uf_code}.json"
        income_data = load_or_download(
            income_path, table=10295, variable=13431, period=2022, uf_code=uf_code
        )
        print(f"UF {uf_code}: PIB 2023, população e renda domiciliar 2022 válidos na Bronze.")


def load_or_download(
    path: Path, table: int, variable: int, period: int, uf_code: int
) -> list[dict[str, str]]:
    """Reaproveito um JSON Bronze íntegro; se faltar, baixo com retentativas HTTP."""
    if path.exists():
        try:
            cached_data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(cached_data, list) and len(cached_data) > 1:
                return cached_data
        except (json.JSONDecodeError, OSError):
            pass

    data = download_sidra_table(table=table, variable=variable, period=period, uf_code=uf_code)
    if not isinstance(data, list) or len(data) <= 1:
        raise ValueError(f"A resposta do SIDRA veio vazia ou inválida: tabela {table}, UF {uf_code}.")
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


if __name__ == "__main__":
    # Executo a coleta apenas quando chamo este arquivo diretamente pelo Python.
    main()
