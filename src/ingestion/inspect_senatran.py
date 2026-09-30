from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_SENATRAN_PATH = PROJECT_ROOT / "data" / "bronze" / "senatran"

FILE_NAME = "D_Frota_por_UF_Municipio_COMBUSTIVEL_Dezembro_2025.xlsx"
FILE_PATH = BRONZE_SENATRAN_PATH / FILE_NAME


def inspect_file() -> None:
    excel_file = pd.ExcelFile(FILE_PATH)

    print("Abas encontradas no arquivo:")
    print(excel_file.sheet_names)

    sheet_name = excel_file.sheet_names[0]

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
    fuel_summary = (
        dataframe.groupby("Combustível Veículo", as_index=False)["Qtd. Veículos"]
        .sum()
        .sort_values("Qtd. Veículos", ascending=False)
    )

    print("\nQuantidade de veículos por tipo de combustível:")
    print(fuel_summary.to_string(index=False))

    electric_mask = dataframe["Combustível Veículo"].str.contains(
        "ELETRICO",
        case=False,
        na=False,
    )

    electric_dataframe = dataframe.loc[electric_mask].copy()

    print("\nTipos de combustível que possuem a palavra ELETRICO:")
    print(
        electric_dataframe["Combustível Veículo"]
        .drop_duplicates()
        .sort_values()
        .to_string(index=False)
    )

    electric_total = electric_dataframe["Qtd. Veículos"].sum()

    print(f"\nTotal de veículos eletrificados encontrados: {electric_total:,}")


if __name__ == "__main__":
    inspect_file()