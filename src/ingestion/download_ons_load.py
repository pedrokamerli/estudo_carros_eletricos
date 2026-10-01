"""Coleto carga horária do ONS como contexto da rede, não como consumo de VEs."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
BRONZE = ROOT / "data/bronze/ons"
OUTPUT = ROOT / "data/portfolio"
BASE = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/curva-carga-ho/"
SOURCE = "https://dados.ons.org.br/dataset/curva-carga"


def profile(frame):
    """Resumo a potência média por mês/hora/subsistema e exponho cobertura horária."""
    required = {"id_subsistema", "nom_subsistema", "din_instante", "val_cargaenergiahomwmed"}
    if not required.issubset(frame.columns):
        raise ValueError("Layout ONS diferente do dicionário.")
    frame = frame.copy()
    frame["din_instante"] = pd.to_datetime(frame.din_instante, errors="raise")
    frame = frame.loc[frame.din_instante.ge("2024-01-01") & frame.din_instante.lt("2026-09-01")]
    if frame.empty or frame.duplicated(["id_subsistema", "din_instante"]).any():
        raise ValueError("Carga vazia ou hora duplicada por subsistema.")
    if not set(frame.id_subsistema).issubset({"N", "NE", "S", "SE"}):
        raise ValueError("Subsistema desconhecido.")
    values = pd.to_numeric(frame.val_cargaenergiahomwmed, errors="raise")
    frame["val_cargaenergiahomwmed"] = values.astype(float)
    if not np.isfinite(values).all() or values.lt(0).any():
        raise ValueError("Carga inválida. Não substituo dado ausente por zero.")
    if (frame.din_instante.dt.minute.ne(0) | frame.din_instante.dt.second.ne(0)).any():
        raise ValueError("Timestamp não horário.")
    frame["data_referencia"] = frame.din_instante.dt.to_period("M").dt.to_timestamp()
    frame["hora"] = frame.din_instante.dt.hour
    grouped = frame.groupby(["data_referencia", "id_subsistema", "nom_subsistema", "hora"], as_index=False)
    result = grouped.agg(carga_media_mw=("val_cargaenergiahomwmed", "mean"),
                         carga_maxima_mw=("val_cargaenergiahomwmed", "max"),
                         horas_observadas=("val_cargaenergiahomwmed", "size"))
    result["horas_esperadas_no_grupo"] = result.data_referencia.dt.days_in_month
    result["cobertura_percentual"] = 100 * result.horas_observadas / result.horas_esperadas_no_grupo
    # MW médio não é energia mensal. SE agrega Sudeste e Centro-Oeste, não uma UF.
    result["unidade"] = "MWmed"
    result["fonte"] = "ONS"
    result["url_fonte"] = SOURCE
    result["licenca_catalogo"] = "Creative Commons Atribuição"
    result["referencia_horaria"] = "hora_como_publicada_sem_conversao_de_fuso"
    result["limite_uso"] = "carga_total_subsistema_sem_identificacao_de_recarga_EV"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    BRONZE.mkdir(parents=True, exist_ok=True)
    frames, records = [], []
    for year in (2024, 2025, 2026):
        url = BASE + f"CURVA_CARGA_{year}.parquet"
        cache = BRONZE / f"CURVA_CARGA_{year}.parquet"
        metadata_path = cache.with_suffix(".json")
        if not cache.exists() or args.refresh:
            response = requests.get(url, timeout=45)
            response.raise_for_status()
            # Salvo uma versão imutável e só atualizo o cache após validar o Parquet.
            digest = hashlib.sha256(response.content).hexdigest()
            immutable = BRONZE / f"CURVA_CARGA_{year}_{digest}.parquet"
            immutable.write_bytes(response.content)
            frame = pd.read_parquet(immutable)
            profile(frame)
            cache.write_bytes(response.content)
            metadata = {"url_fonte": url, "sha256": digest, "data_captura": datetime.now(timezone.utc).isoformat()}
            metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if hashlib.sha256(cache.read_bytes()).hexdigest() != metadata["sha256"]:
                raise ValueError("Cache ONS alterado sem manifesto.")
            frame = pd.read_parquet(cache)
        frames.append(frame)
        records.append(metadata)
    result = profile(pd.concat(frames, ignore_index=True))
    if len(result) != 32 * 4 * 24:
        raise ValueError("Faltam grupos mês/subsistema/hora. Não completo com dados artificiais.")
    result["sha256_manifesto"] = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
    result["data_captura_mais_recente"] = max(r["data_captura"] for r in records)
    silver = ROOT / "data/silver/perfil_carga_ons.parquet"
    silver.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(silver, index=False)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT / "perfil_carga_ons_mensal_hora.csv", index=False)
    print(f"ONS: {len(result)} grupos mensais/horários; cobertura mínima {result.cobertura_percentual.min():.2f}%.")


if __name__ == "__main__":
    main()
