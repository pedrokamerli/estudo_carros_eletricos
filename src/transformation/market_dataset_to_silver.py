"""Transformo o dataset mensal fornecido sobre mercado EV em uma tabela Silver rastreável."""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

import pandas as pd

# Mapeio os meses do CSV para número, porque número ordena corretamente no tempo.
MONTH_BY_NAME = {
    "Janeiro": 1, "Fevereiro": 2, "Marco": 3, "Abril": 4,
    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12,
}
REQUIRED_COLUMNS = {
    "Ano", "Mes", "Municipio", "UF", "Regiao", "Populacao_Estimada",
    "PIB_Per_Capita", "Frota_Total_Estimada", "Tipo_Localidade", "Marca",
    "Modelo", "Tipo_Eletrificacao", "Quantidade_Emplacada",
}
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SILVER_FILE_PATH = PROJECT_ROOT / "data" / "silver" / "market" / "mercado_ev_fornecido.parquet"


def transform_market_dataset(source_file_path: Path) -> pd.DataFrame:
    """Padronizo o dataset fornecido e mantenho somente o período do projeto."""
    dataframe = pd.read_csv(source_file_path, encoding="utf-8-sig")
    missing_columns = REQUIRED_COLUMNS.difference(dataframe.columns)
    if missing_columns:
        raise ValueError(f"Colunas obrigatórias ausentes: {sorted(missing_columns)}")

    dataframe = dataframe.loc[:, sorted(REQUIRED_COLUMNS)].copy()
    dataframe["mes_referencia"] = dataframe["Mes"].map(MONTH_BY_NAME)
    if dataframe["mes_referencia"].isna().any():
        raise ValueError("Encontrei um mês que não reconheço no dataset de mercado.")

    # Este recorte vai de janeiro de 2024 até o último mês realmente recebido em 2026.
    dataframe = dataframe.query("2024 <= Ano <= 2026").copy()
    dataframe["fonte"] = "dataset_fornecido_pelo_usuario"
    dataframe["origem_oficial_confirmada"] = False

    dataframe = dataframe.rename(
        columns={
            "Ano": "ano_referencia", "Mes": "mes_nome", "Municipio": "municipio",
            "UF": "uf", "Regiao": "regiao", "Populacao_Estimada": "populacao_estimada",
            "PIB_Per_Capita": "pib_per_capita", "Frota_Total_Estimada": "frota_total_estimada",
            "Tipo_Localidade": "tipo_localidade", "Marca": "marca", "Modelo": "modelo",
            "Tipo_Eletrificacao": "categoria_eletrificacao",
            "Quantidade_Emplacada": "quantidade_emplacada",
        }
    )
    return dataframe.sort_values(
        ["ano_referencia", "mes_referencia", "uf", "municipio", "marca", "modelo"]
    ).reset_index(drop=True)


def main() -> None:
    """Recebo o caminho do CSV para não duplicar o arquivo original sem necessidade."""
    parser = ArgumentParser(description="Transforma o dataset mensal de mercado EV para a Silver.")
    parser.add_argument("--input", type=Path, required=True, help="Caminho do CSV original.")
    arguments = parser.parse_args()

    dataframe = transform_market_dataset(arguments.input)
    SILVER_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_parquet(SILVER_FILE_PATH, index=False)
    periods = dataframe[["ano_referencia", "mes_referencia"]].drop_duplicates()
    periods = periods.sort_values(["ano_referencia", "mes_referencia"]).reset_index(drop=True)
    first_period = periods.iloc[0]
    last_period = periods.iloc[-1]

    print(f"Linhas processadas: {len(dataframe)}")
    print(
        "Período disponível: "
        f"{first_period['ano_referencia']}-{first_period['mes_referencia']:02d} até "
        f"{last_period['ano_referencia']}-{last_period['mes_referencia']:02d}"
    )
    print(f"Arquivo Silver: {SILVER_FILE_PATH}")


if __name__ == "__main__":
    # Executo somente quando chamo este arquivo diretamente pelo terminal.
    main()
