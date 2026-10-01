"""Baixo a série mensal oficial de combustível publicada pela SENATRAN."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import requests

# Descubro a raiz do projeto sem depender do endereço fixo do meu computador.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_PATH = PROJECT_ROOT / "data" / "bronze" / "senatran"
MANIFEST_PATH = BRONZE_PATH / "manifest_coleta_combustivel.json"

# Estas são as páginas oficiais que consultei para montar a série histórica.
SOURCE_PAGES = {
    2024: "https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/frota-de-veiculos-2024",
    2025: "https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/frota-de-veiculos-2025",
    2026: "https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/frota-de-veiculos-2026",
}
MONTH_BY_NAME = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "maro": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12,
}
MONTH_NAME_BY_NUMBER = {
    1: "Janeiro", 2: "Fevereiro", 3: "Marco", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


class LinkCollector(HTMLParser):
    """Guardo os links encontrados sem adicionar dependências extras ao projeto."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attributes).get("href")
        if href:
            self.links.append(href)


def get_fuel_links(year: int) -> dict[int, str]:
    """Leio a página oficial do ano e encontro os links de combustível publicados."""
    page_url = SOURCE_PAGES[year]
    response = requests.get(page_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    response.raise_for_status()

    parser = LinkCollector()
    parser.feed(response.text)
    links_by_month: dict[int, str] = {}

    for href in parser.links:
        absolute_url = urljoin(page_url, href)
        match = re.search(r"COMBUSTIVEL_([A-Za-z]+)_(20\d{2})", absolute_url, re.IGNORECASE)
        if not match or int(match.group(2)) != year:
            continue

        month = MONTH_BY_NAME.get(match.group(1).lower())
        if month:
            links_by_month[month] = absolute_url

    return links_by_month


def make_destination_path(year: int, month: int) -> Path:
    """Padronizo o nome local, mesmo quando o portal publica nomes com pequenas variações."""
    file_name = f"D_Frota_por_UF_Municipio_COMBUSTIVEL_{MONTH_NAME_BY_NUMBER[month]}_{year}.xlsx"
    return BRONZE_PATH / file_name


def download_file(source_url: str, destination_path: Path) -> int:
    """Baixo um Excel em blocos e só gravo o nome final quando o arquivo está completo."""
    temporary_path = destination_path.with_suffix(".xlsx.part")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*",
    }
    downloaded_bytes = 0

    with requests.get(source_url, headers=headers, stream=True, timeout=120) as response:
        response.raise_for_status()
        expected_bytes = int(response.headers.get("Content-Length", 0))
        with temporary_path.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)
                    downloaded_bytes += len(chunk)

    if expected_bytes and downloaded_bytes != expected_bytes:
        temporary_path.unlink(missing_ok=True)
        raise IOError(f"Download incompleto: esperado {expected_bytes}, recebido {downloaded_bytes}.")

    temporary_path.replace(destination_path)
    return downloaded_bytes


def main() -> None:
    """Coleto somente jan/2024 a ago/2026, o recorte fechado do meu estudo."""
    BRONZE_PATH.mkdir(parents=True, exist_ok=True)
    links_by_period = {
        (year, month): link
        for year in SOURCE_PAGES
        for month, link in get_fuel_links(year).items()
    }
    manifest: list[dict[str, object]] = []

    for year in range(2024, 2027):
        last_month = 8 if year == 2026 else 12
        for month in range(1, last_month + 1):
            source_url = links_by_period.get((year, month))
            destination_path = make_destination_path(year, month)
            record: dict[str, object] = {
                "ano": year,
                "mes": month,
                "arquivo": destination_path.name,
                "url_fonte": source_url,
            }

            if source_url is None:
                # Registro a lacuna para deixar claro que ela veio da fonte, não da minha pipeline.
                record["status"] = "indisponivel_no_portal_oficial"
                print(f"{year}-{month:02d}: ainda não publicado no portal oficial.")
            elif destination_path.exists() and destination_path.stat().st_size > 0:
                record["status"] = "ja_existia_localmente"
                record["tamanho_bytes"] = destination_path.stat().st_size
                print(f"{year}-{month:02d}: arquivo local já encontrado.")
            else:
                print(f"{year}-{month:02d}: baixando arquivo oficial...")
                record["tamanho_bytes"] = download_file(source_url, destination_path)
                record["status"] = "baixado"

            manifest.append(record)

    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    downloaded = sum(record["status"] == "baixado" for record in manifest)
    unavailable = sum(record["status"] == "indisponivel_no_portal_oficial" for record in manifest)
    print(f"Coleta concluída: {downloaded} novos arquivos; {unavailable} meses indisponíveis.")
    print(f"Manifesto salvo em: {MANIFEST_PATH}")


if __name__ == "__main__":
    # Só inicio uma coleta quando executo este arquivo diretamente.
    main()
