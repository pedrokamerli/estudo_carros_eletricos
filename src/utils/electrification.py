"""Aqui concentro as regras para identificar veículos eletrificados."""

# Estes combustíveis têm algum componente elétrico no nome registrado pela SENATRAN.
ELECTRIC_COMPONENT_FUELS = [
    "DIESEL/ELETRICO",
    "ELETRICO",
    "ELETRICO/FONTE EXTERNA",
    "ELETRICO/FONTE INTERNA",
    "ETANOL/ELETRICO",
    "GASOLINA/ALCOOL/ELETRICO",
    "GASOLINA/ELETRICO",
]

# Mantenho estas categorias separadas porque não possuem a palavra ELETRICO no nome.
HYBRID_FUELS = ["HIBRIDO"]
PLUG_IN_HYBRID_FUELS = ["HIBRIDO PLUG-IN"]

# Crio uma tabela de tradução: nome bruto da fonte -> categoria usada nas análises.
CATEGORY_BY_FUEL = {
    **{fuel: "com_componente_eletrico" for fuel in ELECTRIC_COMPONENT_FUELS},
    **{fuel: "hibrido" for fuel in HYBRID_FUELS},
    **{fuel: "hibrido_plug_in" for fuel in PLUG_IN_HYBRID_FUELS},
}
