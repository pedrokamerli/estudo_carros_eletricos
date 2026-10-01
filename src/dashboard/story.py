"""Calculo comparações sem confundir estoque com vendas."""
import pandas as pd

QUESTIONS = ["Como os emplacamentos evoluíram no Brasil?", "Qual foi a taxa de crescimento anual?", "Quais estados possuem mais veículos eletrificados?", "Quais estados mais cresceram proporcionalmente?", "Quais municípios possuem mais veículos eletrificados?", "Quais municípios têm maior participação na frota total?", "O crescimento está nas capitais ou também no interior?", "Quais marcas lideram o mercado?", "Quais modelos são mais emplacados?", "Quais tipos de eletrificação mais crescem?", "PIB, renda e população têm relação com a adoção?", "Onde há boas condições econômicas e baixa adoção?", "Quais municípios têm potencial de crescimento?", "Onde investigar a expansão de recarga?", "É possível prever os próximos emplacamentos?"]
TECH = {"BEV":"Elétrico puro (BEV)", "PHEV":"Híbrido com tomada (PHEV)", "HEV":"Híbrido sem tomada (HEV)", "HEV FLEX":"Híbrido flex"}

def percent_change(current, previous):
    if pd.isna(previous) or previous <= 0:
        return None
    return 100 * (current / previous - 1)

def identified_cities(frame):
    """Não apresento registros sem localização como se fossem cidades reais."""
    unknown = {"", "SEM INFORMACAO", "NAO IDENTIFICADO", "NAN", "NONE"}
    def known(series):
        normalized = series.fillna("").astype(str).str.normalize("NFKD").str.encode("ascii", errors="ignore").str.decode("ascii").str.strip().str.upper()
        return ~normalized.isin(unknown)
    return frame.loc[known(frame.municipio) & known(frame.uf)].copy()

def comparable_years(frame, technologies=("BEV", "PHEV"), through_month=8):
    """Exijo meses iguais em todos os anos antes de comparar acumulados."""
    selected = frame.loc[frame.tecnologia.isin(technologies)].copy()
    selected["data_referencia"] = pd.to_datetime(selected.data_referencia)
    selected = selected.loc[selected.data_referencia.dt.month.le(through_month)]
    monthly = selected.groupby("data_referencia").emplacamentos.sum()
    rows = []
    for year in sorted(monthly.index.year.unique()):
        months = monthly.loc[monthly.index.year == year]
        if set(months.index.month) != set(range(1, through_month + 1)):
            raise ValueError("Meses incompletos: não comparo períodos diferentes.")
        for technology in technologies:
            rows_tech = selected.loc[selected.data_referencia.dt.year.eq(year) & selected.tecnologia.eq(technology)]
            if set(rows_tech.data_referencia.dt.month) != set(range(1, through_month + 1)):
                raise ValueError("Tecnologia com meses incompletos: não trato ausência como zero.")
        rows.append({"Ano":str(year), "Emplacamentos":int(months.sum()), "Meses comparados":through_month})
    return pd.DataFrame(rows)

def ranked_share(frame, keys):
    """Uso todas as marcas do filtro como denominador, não só o top 10."""
    result = frame.groupby(keys, dropna=False).emplacamentos.sum().reset_index()
    total = result.emplacamentos.sum()
    result["Participação (%)"] = 100 * result.emplacamentos / total if total else 0
    return result.sort_values("emplacamentos", ascending=False)
