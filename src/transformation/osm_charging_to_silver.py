"""Preparo objetos de recarga OSM como uma camada exploratória para o mapa."""

import json

import pandas as pd

from src.ingestion.download_osm_charging import OUTPUT as INPUT, ROOT, validate_response

OUTPUT = ROOT / "data/silver/infrastructure/recarga_osm.parquet"


def transform(payload):
    validate_response(payload)
    metadata = payload["portfolio_metadata"]
    if metadata.get("license") != "ODbL-1.0":
        raise ValueError("Licença OSM ausente ou inesperada.")
    rows = []
    for element in payload["elements"]:
        tags = element.get("tags", {})
        kind = element["type"]
        if kind not in {"node", "way", "relation"} or tags.get("amenity") != "charging_station":
            raise ValueError("Objeto fora do escopo da consulta.")
        # Nós têm coordenadas próprias; vias/relações usam centro aproximado.
        coordinates = element if kind == "node" else element.get("center", {})
        latitude, longitude = coordinates.get("lat"), coordinates.get("lon")
        if latitude is None or longitude is None:
            raise ValueError("Objeto sem coordenadas; preciso revisar antes de publicar.")
        if not (-90 <= float(latitude) <= 90 and -180 <= float(longitude) <= 180):
            raise ValueError("Coordenadas inválidas.")
        osm_key = f"{kind}/{element['id']}"
        access = tags.get("access")
        # Não assumo acesso público quando a comunidade não preencheu a tag.
        access_group = (
            "publico_declarado" if access == "yes" else
            "restrito_declarado" if access in {"private", "no", "customers", "permit", "destination"} else
            "nao_informado" if not access else "outro_valor_revisar"
        )
        rows.append({
            "osm_id": osm_key, "nome": tags.get("name"),
            "operador": tags.get("operator"), "rede": tags.get("network"),
            "latitude": float(latitude), "longitude": float(longitude),
            "coordenada_aproximada": kind != "node",
            "municipio_declarado": tags.get("addr:city"),
            "uf_declarada": tags.get("addr:state"),
            "acesso_original": access, "acesso_classificado": access_group,
            "capacidade_original": tags.get("capacity"),
            "conectores_tags_json": json.dumps({k: v for k, v in tags.items() if k.startswith("socket:")}, ensure_ascii=False, sort_keys=True),
            "url_objeto": f"https://www.openstreetmap.org/{osm_key}",
            "data_edicao_osm": element.get("timestamp"),
            "data_base_osm": payload.get("osm3s", {}).get("timestamp_osm_base"),
            "data_coleta_utc": metadata["captured_at_utc"],
            "fonte": "OpenStreetMap", "licenca": "ODbL-1.0",
            "atribuicao": "© OpenStreetMap contributors",
            "url_licenca": "https://www.openstreetmap.org/copyright",
            "unidade": "objeto_mapeado_nao_numero_de_carregadores",
        })
    frame = pd.DataFrame(rows)
    if frame["osm_id"].duplicated().any():
        raise ValueError("Objetos OSM duplicados na captura.")
    # Chaves diferentes podem representar o mesmo local; não prometo deduplicação física.
    return frame


def main():
    frame = transform(json.loads(INPUT.read_text(encoding="utf-8")))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(OUTPUT, index=False)
    print(f"Silver OSM: {len(frame)} objetos.")
    print(frame["acesso_classificado"].value_counts().to_string())
    print(f"Município declarado: {frame['municipio_declarado'].notna().sum()} objetos.")


if __name__ == "__main__":
    main()
