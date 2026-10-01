"""Consulto locais de recarga mapeados no Brasil sem precisar de chave API."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data/bronze/openstreetmap/recarga_brasil.json"
ENDPOINT = "https://overpass-api.de/api/interpreter"
QUERY = '''[out:json][timeout:90];
area["ISO3166-1"="BR"]["admin_level"="2"]->.br;
nwr["amenity"="charging_station"](area.br);
out center meta;'''


def validate_response(payload):
    # Rejeito respostas parciais: o Overpass pode retornar HTTP 200 com erro interno.
    if payload.get("remark") or not isinstance(payload.get("elements"), list):
        raise ValueError("Resposta Overpass incompleta ou inválida.")
    if not payload["elements"]:
        raise ValueError("Consulta vazia; não substituo a captura anterior.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Solicita uma nova captura.")
    args = parser.parse_args()
    # Reutilizo a captura local para não sobrecarregar um serviço comunitário.
    if OUTPUT.exists() and not args.refresh:
        validate_response(json.loads(OUTPUT.read_text(encoding="utf-8")))
        print(f"Reutilizando Bronze OSM: {OUTPUT}")
        return
    response = requests.post(
        ENDPOINT, data={"data": QUERY}, timeout=(15, 110),
        headers={"User-Agent": "Pedro-EV-Portfolio/1.0 (github.com/pedrokamerli/estudo_carros_eletricos)"},
    )
    response.raise_for_status()
    payload = response.json()
    validate_response(payload)
    # Guardo a consulta, licença e horário real da coleta junto da resposta original.
    payload["portfolio_metadata"] = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": ENDPOINT, "query": QUERY,
        "license": "ODbL-1.0", "attribution": "© OpenStreetMap contributors",
        "license_url": "https://www.openstreetmap.org/copyright",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    temporary.replace(OUTPUT)
    print(f"OSM: {len(payload['elements'])} objetos recebidos. Bronze: {OUTPUT}")


if __name__ == "__main__":
    main()
