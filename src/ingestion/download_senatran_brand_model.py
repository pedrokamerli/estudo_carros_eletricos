"""Baixo, quando necessário, um recorte mensal de marca e modelo da SENATRAN."""

from __future__ import annotations

import zipfile
from argparse import ArgumentParser
from pathlib import Path

import requests

# Descubro a raiz do projeto para não depender de caminhos fixos do computador.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_SENATRAN_PATH = PROJECT_ROOT / "data" / "bronze" / "senatran"

# Consulto a API do catálogo público para encontrar o recurso oficial mais tarde.
CKAN_PACKAGE_URL = (
    "https://dados.transportes.gov.br/api/3/action/package_show"
    "?id=registro-nacional-de-veiculos-automotores-renavam"
)
MONTH_NAMES = {
    1: "janeiro", 2: "fevereiro", 3: "marco", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}


def build_resource_file_name(year: int, month: int) -> str:
    """Monto o nome usado pelo catálogo oficial para o mês escolhido."""
    if month not in MONTH_NAMES:
        raise ValueError("O mês precisa ser um número de 1 a 12.")

    return (
        "i_frota_por_uf_municipio_marca_e_modelo_ano_"
        f"{MONTH_NAMES[month]}_{year}.zip"
    )


def find_resource_url(resource_file_name: str) -> str:
    """Encontro a URL oficial do arquivo desejado usando a API CKAN."""
    # Peço os metadados do conjunto de dados ao catálogo oficial.
    response = requests.get(CKAN_PACKAGE_URL, timeout=60)
    response.raise_for_status()

    resources = response.json()["result"]["resources"]

    # Procuro o recurso pelo nome para não depender de uma URL fixa no código.
    for resource in resources:
        if resource["url"].endswith(resource_file_name):
            return resource["url"]

    raise FileNotFoundError(
        f"A API CKAN não encontrou o recurso: {resource_file_name}"
    )


def download_file(url: str, destination: Path) -> None:
    """Baixo o ZIP em partes e só substituo o arquivo final quando ele estiver completo."""
    # Uso um arquivo temporário para não deixar um ZIP incompleto com o nome oficial.
    temporary_path = destination.with_suffix(".zip.part")
    temporary_path.parent.mkdir(parents=True, exist_ok=True)

    # stream=True evita carregar um arquivo grande inteiro na memória.
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        expected_size = int(response.headers.get("Content-Length", 0))
        downloaded_size = 0

        with temporary_path.open("wb") as file:
            # Salvo blocos de 1 MB por vez, o que torna o download mais estável.
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)

    # Confirmo que o servidor entregou todos os bytes que informou no cabeçalho.
    if expected_size and downloaded_size != expected_size:
        temporary_path.unlink(missing_ok=True)
        raise IOError(
            "Download incompleto: "
            f"esperado {expected_size} bytes, recebido {downloaded_size} bytes."
        )

    # Só agora substituo o arquivo antigo; assim um download interrompido não corrompe a Bronze.
    temporary_path.replace(destination)


def extract_zip(zip_path: Path, destination: Path) -> list[str]:
    """Extraio os arquivos originais do ZIP para uma pasta Bronze separada."""
    destination.mkdir(parents=True, exist_ok=True)

    # O ZipFile valida a estrutura do arquivo antes de liberar seu conteúdo.
    with zipfile.ZipFile(zip_path) as zip_file:
        file_names = zip_file.namelist()
        zip_file.extractall(destination)

    return file_names


def get_arguments() -> tuple[int, int, bool]:
    """Leio o mês solicitado sem esconder que esta fonte é pesada."""
    parser = ArgumentParser(
        description="Baixa um único recorte mensal de marca e modelo da SENATRAN."
    )
    parser.add_argument("--year", type=int, required=True, help="Ano, por exemplo 2025.")
    parser.add_argument("--month", type=int, required=True, help="Mês de 1 a 12.")
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Extrai o TXT; uso isso só quando vou processar o arquivo.",
    )
    arguments = parser.parse_args()
    return arguments.year, arguments.month, arguments.extract


def main(year: int, month: int, extract: bool) -> None:
    """Executo a coleta de apenas um mês para não ocupar espaço sem necessidade."""
    resource_file_name = build_resource_file_name(year, month)
    zip_path = BRONZE_SENATRAN_PATH / resource_file_name
    extract_path = BRONZE_SENATRAN_PATH / f"marca_modelo_{year}_{month:02d}"

    print("Consultando a API de dados abertos da SENATRAN...")
    resource_url = find_resource_url(resource_file_name)

    print("Baixando a base de marcas e modelos...")
    download_file(resource_url, zip_path)

    if not extract:
        print("ZIP preservado sem extrair: essa escolha economiza bastante espaço.")
        print(f"Local: {zip_path}")
        return

    print("Extraindo os arquivos originais para a Bronze...")
    file_names = extract_zip(zip_path, extract_path)

    print("Coleta concluída com sucesso!")
    print(f"ZIP preservado em: {zip_path}")
    print(f"Arquivos extraídos: {len(file_names)}")
    for file_name in file_names:
        print(f"- {file_name}")


if __name__ == "__main__":
    # Eu escolho o mês na execução; assim não baixo uma série pesada por acidente.
    selected_year, selected_month, should_extract = get_arguments()
    main(selected_year, selected_month, should_extract)
