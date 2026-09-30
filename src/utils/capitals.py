"""Aqui mantenho as capitais no mesmo padrão de texto usado pela SENATRAN."""

# Uso este dicionário para decidir se cada município é capital ou interior.
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

# Reutilizo a mesma lista de estados para cruzar a UF por extenso da SENATRAN com a sigla do IBGE.
UF_ABBREVIATION_BY_NAME = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAPA": "AP", "AMAZONAS": "AM",
    "BAHIA": "BA", "CEARA": "CE", "DISTRITO FEDERAL": "DF", "ESPIRITO SANTO": "ES",
    "GOIAS": "GO", "MARANHAO": "MA", "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS",
    "MINAS GERAIS": "MG", "PARA": "PA", "PARAIBA": "PB", "PARANA": "PR",
    "PERNAMBUCO": "PE", "PIAUI": "PI", "RIO DE JANEIRO": "RJ", "RIO GRANDE DO NORTE": "RN",
    "RIO GRANDE DO SUL": "RS", "RONDONIA": "RO", "RORAIMA": "RR", "SANTA CATARINA": "SC",
    "SAO PAULO": "SP", "SERGIPE": "SE", "TOCANTINS": "TO",
}
