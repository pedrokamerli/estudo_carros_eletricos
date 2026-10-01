"""Baixo os informativos mensais públicos de emplacamentos da FENABRAVE."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_PATH = PROJECT_ROOT / "data" / "bronze" / "fenabrave"
MANIFEST_PATH = BRONZE_PATH / "manifesto_relatorios_mensais.json"
BASE_URL = "https://www.fenabrave.org.br/portal/files"
START_YEAR = 2024
START_MONTH = 1
END_YEAR = 2026
END_MONTH = 8


def report_periods() -> list[tuple[int, int]]:
    """Crio o calendário mensal pedido, sem presumir que o arquivo já foi publicado."""
    periods = []
    for year in range(START_YEAR, END_YEAR + 1):
        first_month = START_MONTH if year == START_YEAR else 1
        last_month = END_MONTH if year == END_YEAR else 12
        periods.extend((year, month) for month in range(first_month, last_month + 1))
    return periods


def download_report(year: int, month: int) -> dict[str, object]:
    """Guardo cada PDF bruto, validando seu formato e download antes do nome final."""
    file_name = f"{year}_{month:02d}_02.pdf"
    source_url = f"{BASE_URL}/{file_name}"
    destination = BRONZE_PATH / file_name
    record: dict[str, object] = {
        "ano_referencia": year,
        "mes_referencia": month,
        "arquivo": file_name,
        "url_fonte": source_url,
        "data_coleta": date.today().isoformat(),
    }

    if destination.exists() and destination.stat().st_size > 0:
        record.update(status="ja_existia_localmente", tamanho_bytes=destination.stat().st_size)
        return record

    response = requests.get(
        source_url,
        headers={"User-Agent": "Brazil-EV-Data-Platform/1.0"},
        timeout=120,
        stream=True,
    )
    if response.status_code == 404:
        response.close()
        record["status"] = "nao_publicado_ou_arquivo_indisponivel"
        return record
    response.raise_for_status()

    temporary = destination.with_suffix(".pdf.part")
    received_bytes = 0
    try:
        with temporary.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)
                    received_bytes += len(chunk)
        with temporary.open("rb") as downloaded_file:
            has_pdf_signature = downloaded_file.read(5) == b"%PDF-"
        if received_bytes < 1_000 or not has_pdf_signature:
            raise ValueError(f"A resposta de {source_url} não parece ser um PDF válido.")
        expected_bytes = int(response.headers.get("Content-Length", 0))
        if expected_bytes and received_bytes != expected_bytes:
            raise IOError(
                f"Download incompleto em {file_name}: esperado {expected_bytes}, recebido {received_bytes}."
            )
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    finally:
        response.close()

    record.update(status="baixado", tamanho_bytes=received_bytes)
    return record


def main() -> None:
    """Coleto o que estiver publicado e documento indisponibilidades sem criar dados."""
    BRONZE_PATH.mkdir(parents=True, exist_ok=True)
    manifest = []
    for year, month in report_periods():
        record = download_report(year, month)
        manifest.append(record)
        print(f"{year}-{month:02d}: {record['status']}")

    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    collected = sum(record["status"] in {"baixado", "ja_existia_localmente"} for record in manifest)
    unavailable = sum(record["status"] == "nao_publicado_ou_arquivo_indisponivel" for record in manifest)
    print(f"Relatórios disponíveis: {collected}; indisponíveis: {unavailable}.")
    print(f"Manifesto salvo em: {MANIFEST_PATH}")


if __name__ == "__main__":
    # Inicio a coleta somente quando chamo este módulo pelo Python.
    main()
