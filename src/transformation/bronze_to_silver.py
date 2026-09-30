"""Transformo a frota bruta da SENATRAN em uma tabela Silver reutilizável."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

# Reutilizo regras centralizadas para não classificar o mesmo combustível de formas diferentes.
from src.utils.capitals import CAPITALS_BY_UF
from src.utils.electrification import CATEGORY_BY_FUEL
from src.quality.senatran_quality import assess_bronze_dataframe, save_quality_report

# Uso logs para registrar as etapas executadas pela pipeline.
LOGGER = logging.getLogger(__name__)

# Encontro a raiz do projeto a partir deste próprio arquivo.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Aponto para o dado original; a pipeline só lê este arquivo, nunca o altera.
RAW_FILE_PATH = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "senatran"
    / "D_Frota_por_UF_Municipio_COMBUSTIVEL_Dezembro_2025.xlsx"
)
# Defino o destino do dado tratado que será usado pelas análises posteriores.
SILVER_FILE_PATH = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "senatran"
    / "frota_eletrificada_2025_12.parquet"
)
QUALITY_REPORT_PATH = (
    PROJECT_ROOT
    / "data"
    / "quality"
    / "senatran"
    / "quality_report_2025_12.json"
)


def transform_bronze_to_silver(
    raw_file_path: Path = RAW_FILE_PATH,
    silver_file_path: Path = SILVER_FILE_PATH,
) -> pd.DataFrame:
    """Leio a Bronze, classifico veículos eletrificados e gravo a Silver em Parquet."""
    if not raw_file_path.exists():
        # Paro cedo se a fonte ainda não foi colocada na camada Bronze.
        raise FileNotFoundError(f"Arquivo Bronze não encontrado: {raw_file_path}")

    LOGGER.info("Lendo arquivo Bronze: %s", raw_file_path.name)
    # Leio o Excel e avalio sua qualidade antes de criar qualquer dado tratado.
    bronze_dataframe = pd.read_excel(raw_file_path)
    quality_report = assess_bronze_dataframe(bronze_dataframe)
    save_quality_report(quality_report, QUALITY_REPORT_PATH)

    # Paro apenas em problemas críticos, como valores nulos ou quantidades inválidas.
    if not quality_report["aprovado"]:
        raise ValueError("O arquivo Bronze não passou nas verificações de qualidade.")

    LOGGER.info("Relatório de qualidade criado: %s", QUALITY_REPORT_PATH)
    LOGGER.info("Veículos sem UF: %s", quality_report["veiculos_sem_uf"])

    # Filtro somente os combustíveis que fazem parte da definição de frota eletrificada.
    silver_dataframe = bronze_dataframe.loc[
        bronze_dataframe["Combustível Veículo"].isin(CATEGORY_BY_FUEL.keys())
    ].copy()

    # Traduzo o combustível original para uma categoria mais útil nas análises.
    silver_dataframe["Categoria eletrificacao"] = silver_dataframe[
        "Combustível Veículo"
    ].map(CATEGORY_BY_FUEL)
    # Registro se a UF está disponível em vez de descartar registros com localização ausente.
    silver_dataframe["UF informada"] = silver_dataframe["UF"].ne("Sem Informação")
    # Busco a capital de cada UF para criar a classificação geográfica.
    silver_dataframe["Capital da UF"] = silver_dataframe["UF"].map(CAPITALS_BY_UF)

    # Começo sem classificar a localidade; depois preencho interior e capital quando possível.
    silver_dataframe["Tipo localidade"] = "nao_informado"
    known_location_mask = silver_dataframe["UF informada"]
    silver_dataframe.loc[known_location_mask, "Tipo localidade"] = "interior"

    # Quando o município coincide com a capital daquela UF, corrijo a classificação para capital.
    capital_mask = known_location_mask & silver_dataframe["Município"].eq(
        silver_dataframe["Capital da UF"]
    )
    silver_dataframe.loc[capital_mask, "Tipo localidade"] = "capital"

    # Registro período e fonte para que seja possível rastrear cada linha no futuro.
    silver_dataframe["Ano referencia"] = 2025
    silver_dataframe["Mes referencia"] = 12
    silver_dataframe["Fonte"] = "SENATRAN"

    # Padronizo os nomes das colunas para o formato usado nas próximas camadas.
    silver_dataframe = silver_dataframe.rename(
        columns={
            "Município": "municipio",
            "Combustível Veículo": "combustivel_veiculo",
            "Qtd. Veículos": "quantidade_veiculos",
            "Categoria eletrificacao": "categoria_eletrificacao",
            "UF informada": "uf_informada",
            "Capital da UF": "capital_da_uf",
            "Tipo localidade": "tipo_localidade",
            "Ano referencia": "ano_referencia",
            "Mes referencia": "mes_referencia",
            "Fonte": "fonte",
            "UF": "uf",
        }
    )

    # Crio a pasta se necessário e salvo em Parquet, um formato eficiente para dados analíticos.
    silver_file_path.parent.mkdir(parents=True, exist_ok=True)
    silver_dataframe.to_parquet(silver_file_path, index=False)

    LOGGER.info("Registros Bronze: %s", len(bronze_dataframe))
    LOGGER.info("Registros eletrificados Silver: %s", len(silver_dataframe))
    LOGGER.info("Arquivo Silver criado: %s", silver_file_path)

    # Retorno a tabela para que outros scripts possam reutilizá-la sem ler o Parquet de novo.
    return silver_dataframe
