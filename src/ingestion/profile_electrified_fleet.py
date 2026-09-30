from pathlib import Path

import pandas as pd

# Uso esta referência para classificar cada município como capital ou interior.
CAPITALS_BY_UF = {
    "ACRE": "RIO BRANCO",
    "ALAGOAS": "MACEIO",
    "AMAPA": "MACAPA",
    "AMAZONAS": "MANAUS",
    "BAHIA": "SALVADOR",
    "CEARA": "FORTALEZA",
    "DISTRITO FEDERAL": "BRASILIA",
    "ESPIRITO SANTO": "VITORIA",
    "GOIAS": "GOIANIA",
    "MARANHAO": "SAO LUIS",
    "MATO GROSSO": "CUIABA",
    "MATO GROSSO DO SUL": "CAMPO GRANDE",
    "MINAS GERAIS": "BELO HORIZONTE",
    "PARA": "BELEM",
    "PARAIBA": "JOAO PESSOA",
    "PARANA": "CURITIBA",
    "PERNAMBUCO": "RECIFE",
    "PIAUI": "TERESINA",
    "RIO DE JANEIRO": "RIO DE JANEIRO",
    "RIO GRANDE DO NORTE": "NATAL",
    "RIO GRANDE DO SUL": "PORTO ALEGRE",
    "RONDONIA": "PORTO VELHO",
    "RORAIMA": "BOA VISTA",
    "SANTA CATARINA": "FLORIANOPOLIS",
    "SAO PAULO": "SAO PAULO",
    "SERGIPE": "ARACAJU",
    "TOCANTINS": "PALMAS",
}

# Descubro a raiz do projeto e o caminho do dado Bronze que será analisado.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_SENATRAN_PATH = PROJECT_ROOT / "data" / "bronze" / "senatran"

FILE_NAME = "D_Frota_por_UF_Municipio_COMBUSTIVEL_Dezembro_2025.xlsx"
FILE_PATH = BRONZE_SENATRAN_PATH / FILE_NAME

ELECTRIC_COMPONENT_FUELS = [
    "DIESEL/ELETRICO",
    "ELETRICO",
    "ELETRICO/FONTE EXTERNA",
    "ELETRICO/FONTE INTERNA",
    "ETANOL/ELETRICO",
    "GASOLINA/ALCOOL/ELETRICO",
    "GASOLINA/ELETRICO",
]

# Guardo híbridos em listas próprias porque seus nomes não contêm ELETRICO.
HYBRID_FUELS = [
    "HIBRIDO",
]

PLUG_IN_HYBRID_FUELS = [
    "HIBRIDO PLUG-IN",
]


def profile_electrified_fleet() -> None:
    # Leio o Excel original; todas as análises abaixo acontecem somente na memória.
    dataframe = pd.read_excel(FILE_PATH)

    # Relaciono cada combustível aceito a uma categoria analítica mais fácil de entender.
    category_by_fuel = {}

    for fuel in ELECTRIC_COMPONENT_FUELS:
        category_by_fuel[fuel] = "Com componente eletrico"

    for fuel in HYBRID_FUELS:
        category_by_fuel[fuel] = "Hibrido"

    for fuel in PLUG_IN_HYBRID_FUELS:
        category_by_fuel[fuel] = "Hibrido plug-in"

    # Mantenho somente as linhas que atendem à definição inicial de eletrificação.
    electrified_dataframe = dataframe[
        dataframe["Combustível Veículo"].isin(category_by_fuel.keys())
    ].copy()

    # Adiciono uma coluna com a categoria criada a partir do combustível original.
    electrified_dataframe["Categoria eletrificacao"] = (
        electrified_dataframe["Combustível Veículo"].map(category_by_fuel)
    )

    # Agrupo os registros para somar a frota de cada categoria de eletrificação.
    summary = (
        electrified_dataframe.groupby(
            "Categoria eletrificacao",
            as_index=False,
        )["Qtd. Veículos"]
        .sum()
        .sort_values("Qtd. Veículos", ascending=False)
    )

    # Somo todas as categorias para chegar ao total nacional da regra atual.
    total_electrified = summary["Qtd. Veículos"].sum()

    print("Frota eletrificada por categoria:")
    print(summary.to_string(index=False))

    print(f"\nTotal de veículos eletrificados: {total_electrified:,}")
    # Identifico veículos sem UF para não tratá-los como um estado real no ranking.
    unknown_uf_total = electrified_dataframe.loc[
        electrified_dataframe["UF"] == "Sem Informação",
        "Qtd. Veículos",
    ].sum()

    unknown_uf_percentage = unknown_uf_total / total_electrified * 100

    print("\nVeículos sem UF informada:")
    print(f"Quantidade: {unknown_uf_total:,}")
    print(f"Percentual do total: {unknown_uf_percentage:.2f}%")

    # Crio um recorte para geografia, mantendo fora somente os registros sem UF conhecida.
    geographic_dataframe = electrified_dataframe.loc[
        electrified_dataframe["UF"] != "Sem Informação"
    ].copy()

    # Agrupo os municípios de cada UF para criar o ranking estadual.
    state_ranking = (
        geographic_dataframe.groupby("UF", as_index=False)["Qtd. Veículos"]
        .sum()
        .sort_values("Qtd. Veículos", ascending=False)
        .head(10)
    )

    print("\nTop 10 estados por frota eletrificada:")
    print(state_ranking.to_string(index=False))

    # Verifico se ainda há municípios sem informação antes de montar o ranking municipal.
    missing_municipality_dataframe = geographic_dataframe.loc[
        geographic_dataframe["Município"].str.contains(
            "SEM INFORMA",
            case=False,
            na=False,
        )
    ]

    missing_municipality_total = (
        missing_municipality_dataframe["Qtd. Veículos"].sum()
    )

    print("\nVeículos sem município informado:")
    print(f"Quantidade: {missing_municipality_total:,}")
    # Agrupo UF e município juntos para não misturar cidades de mesmo nome em estados diferentes.
    municipality_totals = (
        geographic_dataframe.groupby(
            ["UF", "Município"],
            as_index=False,
        )["Qtd. Veículos"]
        .sum()
    )

    # Ordeno os municípios e mantenho apenas os dez maiores no ranking exibido.
    municipality_ranking = (
        municipality_totals.sort_values(
            "Qtd. Veículos",
            ascending=False,
        )
        .head(10)
    )

    print("\nTop 10 municípios por frota eletrificada:")
    print(municipality_ranking.to_string(index=False))

    # Busco a capital correspondente a cada UF usando o dicionário do início do arquivo.
    municipality_totals["Capital da UF"] = (
        municipality_totals["UF"].map(CAPITALS_BY_UF)
    )

    # Começo classificando todos como interior e depois marco as capitais.
    municipality_totals["Tipo localidade"] = "Interior"

    municipality_totals.loc[
        municipality_totals["Município"]
        == municipality_totals["Capital da UF"],
        "Tipo localidade",
    ] = "Capital"

    # Somo capitais e interior para responder à pergunta sobre concentração geográfica.
    capital_vs_interior = (
        municipality_totals.groupby(
            "Tipo localidade",
            as_index=False,
        )["Qtd. Veículos"]
        .sum()
        .sort_values("Qtd. Veículos", ascending=False)
    )

    # Transformo os totais em participação percentual no conjunto com UF informada.
    capital_vs_interior["Percentual"] = (
        capital_vs_interior["Qtd. Veículos"]
        / capital_vs_interior["Qtd. Veículos"].sum()
        * 100
    )

    print("\nFrota eletrificada: capitais versus interior:")
    print(capital_vs_interior.to_string(index=False))



if __name__ == "__main__":
    # Rodo o perfil apenas quando este arquivo é executado diretamente.
    profile_electrified_fleet()
