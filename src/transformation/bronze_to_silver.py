"""Transformo todos os arquivos mensais de combustível da SENATRAN em uma tabela Silver."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

from src.quality.senatran_quality import assess_bronze_dataframe, save_quality_report
from src.utils.capitals import CAPITALS_BY_UF
from src.utils.electrification import CATEGORY_BY_FUEL

# Uso logs para registrar as etapas executadas pela pipeline.
LOGGER = logging.getLogger(__name__)
# Encontro a raiz do projeto a partir deste próprio arquivo.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_SENATRAN_PATH = PROJECT_ROOT / "data" / "bronze" / "senatran"
SILVER_FILE_PATH = PROJECT_ROOT / "data" / "silver" / "senatran" / "frota_eletrificada.parquet"
QUALITY_REPORT_PATH = PROJECT_ROOT / "data" / "quality" / "senatran"

# Converto o mês escrito no nome oficial do arquivo para seu número.
MONTH_BY_NAME = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
    "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}
FUEL_FILE_PATTERN = re.compile(
    r"^D_Frota_por_UF_Municipio_COMBUSTIVEL_(?P<month>[A-Za-z]+)_(?P<year>20\d{2})\.xlsx$",
    re.IGNORECASE,
)


def get_period_from_file_name(raw_file_path: Path) -> tuple[int, int]:
    """Descubro ano e mês pelo nome original da SENATRAN para não digitar datas manualmente."""
    match = FUEL_FILE_PATTERN.match(raw_file_path.name)
    if not match:
        raise ValueError(
            "Nome de arquivo não reconhecido. Espero o padrão "
            "D_Frota_por_UF_Municipio_COMBUSTIVEL_Mes_Ano.xlsx."
        )

    month_name = match.group("month").lower()
    if month_name not in MONTH_BY_NAME:
        raise ValueError(f"Mês não reconhecido no arquivo: {raw_file_path.name}")

    return int(match.group("year")), MONTH_BY_NAME[month_name]


def find_bronze_fuel_files() -> list[Path]:
    """Encontro somente os arquivos mensais de combustível dentro do recorte do projeto."""
    files: list[Path] = []
    for raw_file_path in BRONZE_SENATRAN_PATH.glob("*.xlsx"):
        try:
            year, _ = get_period_from_file_name(raw_file_path)
        except ValueError:
            # Ignoro Excel de outro tipo para evitar misturar fontes diferentes por acidente.
            continue

        if 2024 <= year <= 2026:
            files.append(raw_file_path)

    # Ordeno por período para a tabela final já ficar organizada cronologicamente.
    return sorted(files, key=get_period_from_file_name)


def transform_one_file(raw_file_path: Path) -> pd.DataFrame:
    """Valido e transformo um único mês da Bronze para o padrão Silver."""
    year, month = get_period_from_file_name(raw_file_path)
    LOGGER.info("Lendo Bronze: %s", raw_file_path.name)

    # Leio o Excel e avalio sua qualidade antes de criar qualquer dado tratado.
    bronze_dataframe = pd.read_excel(raw_file_path)
    quality_report = assess_bronze_dataframe(bronze_dataframe)
    report_path = QUALITY_REPORT_PATH / f"quality_report_{year}_{month:02d}.json"
    save_quality_report(quality_report, report_path)

    if not quality_report["aprovado"]:
        raise ValueError(f"O arquivo {raw_file_path.name} não passou nas verificações de qualidade.")

    # Filtro somente os combustíveis que fazem parte da definição de frota eletrificada.
    silver_dataframe = bronze_dataframe.loc[
        bronze_dataframe["Combustível Veículo"].isin(CATEGORY_BY_FUEL.keys())
    ].copy()
    # Traduzo o combustível original para uma categoria mais útil nas análises.
    silver_dataframe["Categoria eletrificacao"] = silver_dataframe["Combustível Veículo"].map(CATEGORY_BY_FUEL)
    # Registro se a UF está disponível em vez de descartar registros com localização ausente.
    silver_dataframe["UF informada"] = silver_dataframe["UF"].ne("Sem Informação")
    silver_dataframe["Capital da UF"] = silver_dataframe["UF"].map(CAPITALS_BY_UF)
    silver_dataframe["Tipo localidade"] = "nao_informado"

    known_location_mask = silver_dataframe["UF informada"]
    silver_dataframe.loc[known_location_mask, "Tipo localidade"] = "interior"
    capital_mask = known_location_mask & silver_dataframe["Município"].eq(silver_dataframe["Capital da UF"])
    silver_dataframe.loc[capital_mask, "Tipo localidade"] = "capital"

    # Guardo o período do próprio arquivo para permitir séries mensais depois.
    silver_dataframe["Ano referencia"] = year
    silver_dataframe["Mes referencia"] = month
    silver_dataframe["Fonte"] = "SENATRAN"

    return silver_dataframe.rename(
        columns={
            "UF": "uf", "Município": "municipio", "Combustível Veículo": "combustivel_veiculo",
            "Qtd. Veículos": "quantidade_veiculos", "Categoria eletrificacao": "categoria_eletrificacao",
            "UF informada": "uf_informada", "Capital da UF": "capital_da_uf",
            "Tipo localidade": "tipo_localidade", "Ano referencia": "ano_referencia",
            "Mes referencia": "mes_referencia", "Fonte": "fonte",
        }
    )


def transform_bronze_to_silver(silver_file_path: Path = SILVER_FILE_PATH) -> pd.DataFrame:
    """Uno todos os meses disponíveis em uma única tabela Silver pronta para análise."""
    bronze_files = find_bronze_fuel_files()
    if not bronze_files:
        raise FileNotFoundError(f"Nenhum arquivo mensal de combustível foi encontrado em: {BRONZE_SENATRAN_PATH}")

    monthly_dataframes = [transform_one_file(raw_file_path) for raw_file_path in bronze_files]
    silver_dataframe = pd.concat(monthly_dataframes, ignore_index=True)
    silver_dataframe = silver_dataframe.sort_values(
        ["ano_referencia", "mes_referencia", "uf", "municipio"]
    ).reset_index(drop=True)

    # Salvo uma tabela única; ao adicionar outro mês, basta rodar a pipeline novamente.
    silver_file_path.parent.mkdir(parents=True, exist_ok=True)
    silver_dataframe.to_parquet(silver_file_path, index=False)

    LOGGER.info("Meses processados: %s", len(bronze_files))
    LOGGER.info("Registros eletrificados Silver: %s", len(silver_dataframe))
    LOGGER.info("Arquivo Silver criado: %s", silver_file_path)
    return silver_dataframe
