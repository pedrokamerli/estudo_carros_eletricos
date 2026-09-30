"""Transformo o histórico anual de vendas de veículos elétricos em uma tabela Silver."""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

import pandas as pd

# Encontro a raiz do projeto para salvar a tabela tratada sempre no mesmo lugar.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SILVER_FILE_PATH = PROJECT_ROOT / "data" / "silver" / "market" / "historico_vendas_ev_brasil.parquet"
REQUIRED_COLUMNS = {"Ano", "Modelo", "Marca", "Categoria", "Unidades_Emplacadas"}


def transform_sales_history(source_file_path: Path) -> pd.DataFrame:
    """Leio o CSV, valido suas colunas e deixo os nomes prontos para as análises."""
    # utf-8-sig remove o marcador invisível que alguns CSVs colocam no início da primeira coluna.
    sales_dataframe = pd.read_csv(source_file_path, encoding="utf-8-sig")
    missing_columns = REQUIRED_COLUMNS.difference(sales_dataframe.columns)
    if missing_columns:
        raise ValueError(f"Colunas obrigatórias ausentes: {sorted(missing_columns)}")

    sales_dataframe = sales_dataframe.loc[:, sorted(REQUIRED_COLUMNS)].copy()
    sales_dataframe["Ano"] = pd.to_numeric(sales_dataframe["Ano"], errors="raise")
    sales_dataframe["Unidades_Emplacadas"] = pd.to_numeric(sales_dataframe["Unidades_Emplacadas"], errors="raise")

    # Mantenho só o recorte do projeto e registro que esta fonte é anual, não mensal.
    sales_dataframe = sales_dataframe.query("2024 <= Ano <= 2026").copy()
    sales_dataframe["mes_referencia"] = pd.NA
    sales_dataframe["fonte"] = "historico_vendas_ev_brasil"

    sales_dataframe = sales_dataframe.rename(
        columns={
            "Ano": "ano_referencia", "Modelo": "modelo", "Marca": "marca",
            "Categoria": "categoria_eletrificacao", "Unidades_Emplacadas": "unidades_emplacadas",
        }
    )
    return sales_dataframe.sort_values(["ano_referencia", "marca", "modelo"]).reset_index(drop=True)


def main() -> None:
    """Permito informar o CSV original sem copiar arquivos grandes ou duplicados."""
    parser = ArgumentParser(description="Transforma o histórico anual de vendas EV para a Silver.")
    parser.add_argument("--input", type=Path, required=True, help="Caminho do CSV original.")
    arguments = parser.parse_args()

    sales_dataframe = transform_sales_history(arguments.input)
    SILVER_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    sales_dataframe.to_parquet(SILVER_FILE_PATH, index=False)

    print("Histórico de vendas transformado com sucesso.")
    print(f"Linhas processadas: {len(sales_dataframe)}")
    print(f"Arquivo Silver: {SILVER_FILE_PATH}")


if __name__ == "__main__":
    # Executo somente quando chamo este arquivo diretamente pelo terminal.
    main()
