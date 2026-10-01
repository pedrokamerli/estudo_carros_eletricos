"""Coleto agregados mensais publicados, sem transformar ausência em zero."""

import json
import hashlib
import sys
import time
from datetime import datetime, timezone
import pandas as pd
from src.ingestion.download_abve_public_panel import ROOT, BRONZE, PAGE, fetch_metadata, query_public


def decode_rows(response):
    """Recomponho dicionários e máscaras de repetição/nulos do painel público."""
    ds = response["results"][0]["result"]["data"]["dsr"]["DS"][0]
    if ds.get("RT"):
        raise ValueError("Consulta truncada; preciso de um recorte menor.")
    rows, schema, previous = [], None, None
    for block in ds["PH"]:
        for encoded in block["DM0"]:
            schema = encoded.get("S", schema)
            if schema is None:
                raise ValueError("Resposta sem esquema.")
            values, current = iter(encoded.get("C", [])), []
            for i, column in enumerate(schema):
                if encoded.get("Ø", 0) & (1 << i):
                    value = None
                elif encoded.get("R", 0) & (1 << i):
                    if previous is None:
                        raise ValueError("Repetição sem linha anterior.")
                    value = previous[i]
                else:
                    value = next(values)
                current.append(value)
            if next(values, None) is not None:
                raise ValueError("Colunas inesperadas.")
            rows.append([ds["ValueDicts"][col["DN"]][v] if "DN" in col and isinstance(v, int) else v
                         for col, v in zip(schema, current)])
            previous = current
    if len(rows) >= 10000:
        raise ValueError("Limite atingido; não publico como completo.")
    return rows


def main():
    metadata, api, headers, embed = fetch_metadata()
    BRONZE.mkdir(parents=True, exist_ok=True)
    common = [("Tcalendario", "Ano", "Column"), ("Tcalendario", "MêsNúmero", "Column")]
    specs = {
        "tecnologia": [("BaseVendas_ABVE", "Tipo_Tecnologia", "Column")],
        "modelo": [("BaseVendas_ABVE", "Fabricante", "Column"), ("BaseVendas_ABVE", "Modelo", "Column"), ("BaseVendas_ABVE", "Tipo_Tecnologia", "Column")],
        "municipio": [("Cadastro_Estado", "Estado", "Column"), ("Cadastro_Municipio", "Município", "Column"), ("BaseVendas_ABVE", "Tipo_Tecnologia", "Column")],
    }
    periods = [(y, m) for y in (2024, 2025, 2026) for m in range(1, 13) if y < 2026 or m <= 8]
    for name, dimensions in specs.items():
        records = []
        for year, month in ([(None, None)] if name == "tecnologia" else periods):
            cache = BRONZE / f"{name}_{year}_{month}.json"
            fields = common + dimensions + [("BaseVendas_ABVE", "Quantidade", "Measure")]
            if cache.exists():
                envelope = json.loads(cache.read_text(encoding="utf-8"))
            else:
                envelope = None
            if envelope is None or envelope.get("campos") != [list(f) for f in fields] or "--refresh" in sys.argv:
                response = query_public(metadata, api, headers, fields, year, month)
                envelope = {"pagina_fonte": PAGE, "data_captura": datetime.now(timezone.utc).isoformat(),
                            "campos": fields, "ano": year, "mes": month, "resposta": response}
                serialized = json.dumps(envelope, ensure_ascii=False)
                digest = hashlib.sha256(serialized.encode()).hexdigest()
                (BRONZE / f"captura_{digest}.json").write_text(serialized, encoding="utf-8")
                cache.write_text(serialized, encoding="utf-8")
                time.sleep(0.4)
            rows = decode_rows(envelope["resposta"])
            for row in rows:
                record = dict(zip([p for _, p, _ in fields], row))
                if record["Ano"] is None or record["MêsNúmero"] is None:
                    continue
                if (int(record["Ano"]), int(record["MêsNúmero"])) not in periods:
                    continue
                if year is not None and (record["Ano"], record["MêsNúmero"]) != (year, month):
                    raise ValueError("O painel não aplicou o filtro mensal.")
                record.update(data_captura=envelope["data_captura"], url_fonte=PAGE)
                records.append(record)
            print(f"ABVE {name}: {year}-{month}, {len(rows)} linhas.", flush=True)
        frame = pd.DataFrame(records).rename(columns={"Ano": "ano_referencia", "MêsNúmero": "mes_referencia", "Quantidade": "emplacamentos"})
        if frame.empty or frame.emplacamentos.isna().any() or (frame.emplacamentos < 0).any():
            raise ValueError(f"Agregado inválido: {name}")
        frame["data_referencia"] = pd.to_datetime(dict(year=frame.ano_referencia, month=frame.mes_referencia, day=1))
        frame["limite_uso"] = "medida_publica_ABVE_metodologia_painel_nao_frota"
        decoded = ROOT / "data/silver/abve_public"
        decoded.mkdir(parents=True, exist_ok=True)
        frame.to_csv(decoded / f"{name}_decodificado.csv", index=False)


if __name__ == "__main__":
    main()
