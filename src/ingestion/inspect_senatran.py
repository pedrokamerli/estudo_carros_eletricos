from pathlib import Path

import pandas as pd

# Descubro a raiz do projeto e monto o caminho até o arquivo Bronze que quero investigar.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_SENATRAN_PATH = PROJECT_ROOT / "data" / "bronze" / "senatran"

FILE_NAME = "D_Frota_por_UF_Municipio_COMBUSTIVEL_Dezembro_2025.xlsx"
FILE_PATH = BRONZE_SENATRAN_PATH / FILE_NAME


def inspect_file() -> None:
    # Abro o Excel primeiro para descobrir quais abas ele possui.
    excel_file = pd.ExcelFile(FILE_PATH)

    print("Abas encontradas no arquivo:")
    print(excel_file.sheet_names)

    # A fonte tem uma aba; escolho a primeira para fazer a inspeção inicial.
    sheet_name = excel_file.sheet_names[0]

    # Transformo a aba do Excel em um DataFrame, a tabela que vou analisar com Python.
    dataframe = pd.read_excel(FILE_PATH, sheet_name=sheet_name)

    print(f"\nAba analisada: {sheet_name}")
    print(f"Quantidade de linhas e colunas: {dataframe.shape}")

    print("\nColunas encontradas:")
    for column in dataframe.columns:
        print(f"- {column}")

    print("\nTipos de dados:")
    print(dataframe.dtypes)

    print("\nPrimeiras 5 linhas:")
    print(dataframe.head().to_string(index=False))
    # Somo os veículos por combustível para conhecer as categorias existentes na fonte.
    fuel_summary = (
        dataframe.groupby("Combustível Veículo", as_index=False)["Qtd. Veículos"]
        .sum()
        .sort_values("Qtd. Veículos", ascending=False)
    )

    print("\nQuantidade de veículos por tipo de combustível:")
    print(fuel_summary.to_string(index=False))

    # Procuro inicialmente os combustíveis que possuem a palavra ELETRICO no nome.
    electric_mask = dataframe["Combustível Veículo"].str.contains(
        "ELETRICO",
        case=False,
        na=False,
    )

    # Crio uma cópia das linhas encontradas para não modificar a tabela original.
    electric_dataframe = dataframe.loc[electric_mask].copy()

    print("\nTipos de combustível que possuem a palavra ELETRICO:")
    print(
        electric_dataframe["Combustível Veículo"]
        .drop_duplicates()
        .sort_values()
        .to_string(index=False)
    )

    # Somo o recorte exploratório; depois percebi que híbridos exigem uma regra adicional.
    electric_total = electric_dataframe["Qtd. Veículos"].sum()

    print(f"\nTotal de veículos eletrificados encontrados: {electric_total:,}")


if __name__ == "__main__":
    # Executo esta inspeção apenas quando rodo o arquivo diretamente.
    inspect_file()
