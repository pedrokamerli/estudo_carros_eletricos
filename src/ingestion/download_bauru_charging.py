"""Cruzo uma captura local de recarga com a malha oficial de Bauru, sem chave API."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
import pandas as pd
import requests
from src.ingestion.download_osm_charging import ROOT, ENDPOINT, validate_response
from src.transformation.osm_charging_to_silver import transform

BOUNDARY_URL = "https://servicodados.ibge.gov.br/api/v3/malhas/municipios/3506003?formato=application/vnd.geo%2Bjson&qualidade=maxima"
DIRECTORY = ROOT / "data/bronze/bauru_recarga"


def in_ring(x, y, ring):
    """Uso o cruzamento de raios; incluo pontos exatamente na borda municipal."""
    inside = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
        cross = (x-ax)*(by-ay)-(y-ay)*(bx-ax)
        if abs(cross) < 1e-10 and min(ax,bx) <= x <= max(ax,bx) and min(ay,by) <= y <= max(ay,by):
            return True
        if (ay > y) != (by > y) and x < (bx-ax)*(y-ay)/(by-ay)+ax:
            inside = not inside
    return inside


def polygons(geometry):
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"]]
    if geometry["type"] == "MultiPolygon":
        return geometry["coordinates"]
    raise ValueError("Malha municipal não é um polígono.")


def belongs(x, y, geometry):
    return any(in_ring(x,y,p[0]) and not any(in_ring(x,y,hole) for hole in p[1:]) for p in polygons(geometry))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh",action="store_true")
    args = parser.parse_args()
    DIRECTORY.mkdir(parents=True,exist_ok=True)
    boundary_path, capture_path = DIRECTORY/"malha_ibge.json", DIRECTORY/"captura_osm.json"
    if not boundary_path.exists() or args.refresh:
        response = requests.get(BOUNDARY_URL,timeout=40)
        response.raise_for_status()
        boundary = response.json()
        if len(boundary.get("features",[])) != 1:
            raise ValueError("Preciso de exatamente uma malha municipal.")
        polygons(boundary["features"][0]["geometry"])
        boundary_path.write_bytes(response.content)
    boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    geometry = boundary["features"][0]["geometry"]
    points = [point for polygon in polygons(geometry) for point in polygon[0]]
    west,east = min(p[0] for p in points),max(p[0] for p in points)
    south,north = min(p[1] for p in points),max(p[1] for p in points)
    query = f'[out:json][timeout:45];nwr["amenity"="charging_station"]({south},{west},{north},{east});out center meta;'
    if not capture_path.exists() or args.refresh:
        failures = []
        for endpoint in (ENDPOINT,"https://overpass.kumi.systems/api/interpreter"):
            try:
                response = requests.get(endpoint,params={"data":query},timeout=(15,55),
                    headers={"User-Agent":"Pedro-EV-Portfolio/1.0 (github.com/pedrokamerli/estudo_carros_eletricos)"})
                response.raise_for_status()
                payload = response.json()
                validate_response(payload)
                break
            except (requests.RequestException, ValueError) as exc:
                failures.append(f"{endpoint}: {exc}")
        else:
            raise RuntimeError("Não consegui uma captura local íntegra: "+"; ".join(failures))
        # Uma resposta vazia ou parcial não apaga a última captura válida.
        validate_response(payload)
        payload["portfolio_metadata"] = dict(captured_at_utc=datetime.now(timezone.utc).isoformat(),
            endpoint=endpoint,query=query,license="ODbL-1.0",attribution="© OpenStreetMap contributors")
        capture_path.write_text(json.dumps(payload,ensure_ascii=False),encoding="utf-8")
    frame = transform(json.loads(capture_path.read_text(encoding="utf-8")))
    frame = frame.loc[[belongs(row.longitude,row.latitude,geometry) for row in frame.itertuples()]].copy()
    if frame.empty:
        raise ValueError("OSM não retornou objetos dentro de Bauru. Isso não comprova ausência de recarga.")
    frame["codigo_ibge"] = "3506003"
    frame["municipio_validado_malha"] = "BAURU"
    frame["url_malha"] = BOUNDARY_URL
    frame["sha256_malha"] = hashlib.sha256(boundary_path.read_bytes()).hexdigest()
    frame["sha256_captura"] = hashlib.sha256(capture_path.read_bytes()).hexdigest()
    # Capacidade e conectores são declarações comunitárias, não teste de funcionamento.
    frame["funcionamento_verificado"] = False
    frame["limite"] = "Inventário comunitário parcial na data real da captura. Objetos não equivalem a estações físicas únicas; centro aproximado pode afetar a classificação de vias/relações. Não mede disponibilidade, ocupação ou demanda horária."
    frame.to_csv(ROOT/"data/portfolio/bauru_recarga_inventario.csv",index=False)
    print(f"Bauru: {len(frame)} objetos OSM dentro da malha IBGE; funcionamento não verificado.")


if __name__ == "__main__":
    main()
