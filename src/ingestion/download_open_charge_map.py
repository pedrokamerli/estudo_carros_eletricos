"""Baixo pontos de recarga do Brasil pela API Open Charge Map."""

from __future__ import annotations

import json
import os
from pathlib import Path

import requests

# Encontro a raiz do projeto sem deixar caminhos fixos no código.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_PATH = PROJECT_ROOT / "data" / "bronze" / "open_charge_map"
OUTPUT_PATH = BRONZE_PATH / "eletropostos_brasil.json"
API_URL = "https://api.openchargemap.io/v3/poi/"


def main() -> None:
    """Consulto o Brasil inteiro e preservo a resposta original na Bronze."""
    api_key = os.getenv("OCM_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Defina a variável OCM_API_KEY com a chave gratuita da Open Charge Map antes de executar."
        )

    # Uso parâmetros compactos para trazer apenas os campos necessários e evitar chamadas repetidas.
    parameters = {
        "output": "json",
        "countrycode": "BR",
        "maxresults": 10_000,
        "compact": "true",
        "verbose": "false",
    }
    headers = {
        "X-API-Key": api_key,
        "User-Agent": "Brazil-EV-Data-Platform",
    }
    response = requests.get(API_URL, params=parameters, headers=headers, timeout=120)
    response.raise_for_status()

    BRONZE_PATH.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(response.json(), ensure_ascii=False), encoding="utf-8"
    )
    print("Eletropostos baixados com sucesso.")
    print(f"Arquivo Bronze: {OUTPUT_PATH}")


if __name__ == "__main__":
    # Inicio a chamada somente quando executo este arquivo diretamente.
    main()
