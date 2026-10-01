"""Conto a história do mercado com perguntas, comparações e limites claros."""
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st
from src.dashboard.story import QUESTIONS, TECH, comparable_years, percent_change, ranked_share

DATA = Path(__file__).resolve().parent / "data/portfolio"
TEAL, ORANGE, BLUE = "#087F8C", "#DF823B", "#395C96"
st.set_page_config(page_title="A jornada dos elétricos no Brasil", page_icon="🚘", layout="wide")

@st.cache_data(show_spinner=False)
def read_export(name, modified):
    return pd.read_csv(DATA / name)

def load(name):
    path = DATA / name
    if not path.exists():
        st.error(f"Arquivo ainda indisponível: {name}. Atualize os dados do projeto.")
        st.stop()
    return read_export(name, path.stat().st_mtime_ns).copy()

def dates(frame):
    frame = frame.copy()
    frame["data_referencia"] = (pd.to_datetime(frame.data_referencia) if "data_referencia" in frame else
                               pd.to_datetime(dict(year=frame.ano_referencia,month=frame.mes_referencia,day=1)))
    return frame.sort_values("data_referencia")

def number(value):
    return f"{value:,.0f}".replace(",", ".")

def pct(value):
    return "Sem referência" if value is None or pd.isna(value) else f"{value:.1f}%".replace(".", ",")

def intro(chapter, title, description, questions):
    st.caption(f"CAPÍTULO {chapter} · PERGUNTAS {questions}")
    st.header(title)
    st.write(description)

def style(chart):
    return chart.configure(locale=alt.Locale(number=alt.NumberLocale(decimal=",",thousands=".",grouping=[3],currency=["R$ ",""],nan="Sem dado"))).configure_view(stroke=None).configure_axis(labelFontSize=12,titleFontSize=12,gridColor="#E8EDF1").configure_legend(title=None,labelFontSize=12,orient="bottom")

def bars(frame, category, value, title, unit="Veículos", hue=None):
    """Escolho barras horizontais para tornar nomes e diferenças legíveis."""
    st.subheader(title)
    if frame.empty:
        st.info("Não há dados comparáveis para este filtro.")
        return
    data = frame.copy()
    data["Valor legível"] = data[value].map(lambda v: pct(v) if unit == "%" else number(v))
    color = alt.Color(f"{hue}:N",scale=alt.Scale(range=[TEAL,ORANGE,BLUE])) if hue else alt.value(TEAL)
    if hue == "Ano" or category == "Ano":
        color = alt.Color("Ano:N",scale=alt.Scale(domain=["2024","2025","2026"],range=[BLUE,TEAL,ORANGE]))
    enc = dict(x=alt.X(f"{value}:Q",title=unit),y=alt.Y(f"{category}:N",sort="-x",title=None),color=color,
               tooltip=[alt.Tooltip(f"{category}:N"),alt.Tooltip("Valor legível:N",title=unit)])
    if hue:
        enc["yOffset"] = alt.YOffset(f"{hue}:N")
        enc["tooltip"].append(alt.Tooltip(f"{hue}:N"))
    chart = alt.Chart(data).mark_bar(cornerRadiusEnd=4).encode(**enc).properties(height=max(180,len(data[category].unique())*(40 if hue else 30)))
    st.altair_chart(style(chart),width="stretch")

def lines(frame, value, series, title):
    data = frame.copy()
    data["Quantidade legível"] = data[value].map(number)
    st.subheader(title)
    chart = alt.Chart(data).mark_line(point=True,strokeWidth=3).encode(
        x=alt.X("data_referencia:T",title="Mês",axis=alt.Axis(format="%m/%Y")),
        y=alt.Y(f"{value}:Q",title="Veículos",scale=alt.Scale(zero=False)),
        color=alt.Color(f"{series}:N",scale=alt.Scale(range=[TEAL,ORANGE,BLUE])),
        tooltip=[alt.Tooltip("data_referencia:T",title="Mês",format="%m/%Y"),alt.Tooltip(f"{series}:N",title="Série"),alt.Tooltip("Quantidade legível:N",title="Veículos")])
    st.altair_chart(style(chart.properties(height=320)),width="stretch")

MONTHS = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
MONTH_NAMES = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

def year_lines(frame, value, title, cumulative=False):
    """Sobreponho os anos; acumulo apenas fluxos, nunca estoques de frota."""
    data = frame.groupby("data_referencia")[value].sum().reset_index().sort_values("data_referencia")
    data["Ano"] = data.data_referencia.dt.year.astype(str)
    data["Mês"] = data.data_referencia.dt.month.map(lambda v:MONTHS[v-1])
    if cumulative:
        data[value] = data.groupby("Ano")[value].cumsum()
    data["Quantidade legível"] = data[value].map(number)
    st.subheader(title)
    chart = alt.Chart(data).mark_line(point=True,strokeWidth=3).encode(
        x=alt.X("Mês:N",sort=MONTHS,title="Meses do ano"),y=alt.Y(f"{value}:Q",title="Veículos",scale=alt.Scale(zero=True)),
        color=alt.Color("Ano:N",scale=alt.Scale(domain=["2024","2025","2026"],range=[BLUE,TEAL,ORANGE])),
        tooltip=["Ano:N","Mês:N",alt.Tooltip("Quantidade legível:N",title="Veículos")])
    st.altair_chart(style(chart.properties(height=320)),width="stretch")

def details(frame, filename):
    """Mantenho tabelas técnicas em segundo plano para preservar a narrativa."""
    with st.expander("Conferir os números e baixar os dados"):
        st.dataframe(frame,hide_index=True,width="stretch")
        st.download_button("Baixar este recorte",frame.to_csv(index=False).encode("utf-8-sig"),filename,"text/csv",key=filename)

def guide():
    with st.expander("Antes de começar: o que significa cada termo?"):
        st.markdown("""**Frota** é o conjunto de veículos existentes em uma data. **Emplacamentos** são novos registros no mês: aqui aproximam vendas, não a demanda não atendida.

**BEV** é elétrico puro. **PHEV** combina combustível e eletricidade e pode carregar na tomada. **HEV** é híbrido sem recarga externa. **MHEV** é híbrido leve: não equivale a um elétrico puro.

**Participação** é uma parte do total. **Crescimento** compara dois momentos. Uma cidade pode crescer muito em percentual e ainda ter poucos veículos.

**Como ler:** passe o mouse nos gráficos para ver os números. As legendas identificam as séries. Cada capítulo tem seus próprios filtros. Fontes, períodos e limites ficam abaixo dos gráficos.""")

def market():
    intro(1,"A mobilidade elétrica ganhou espaço. Mas quanto?","Começamos pelos carros que já circulam e depois olhamos os novos emplacamentos. Para medir crescimento, comparamos períodos iguais.","1 e 2")
    national = dates(load("evolucao_frota_nacional.csv"))
    period = st.selectbox("Mês da fotografia da frota",national.data_referencia.dt.strftime("%Y-%m").tolist(),index=len(national)-1)
    latest = national.loc[national.data_referencia.eq(pd.Timestamp(period+"-01"))].iloc[0]
    a,b,c = st.columns(3)
    a.metric("Veículos eletrificados em circulação",number(latest.total_veiculos_eletrificados))
    b.metric("Com estado identificado",number(latest.total_veiculos_uf_informada))
    c.metric("Sem estado identificado",number(latest.total_veiculos_sem_uf))
    st.caption("SENATRAN · estoque no mês escolhido · definição ampla de eletrificação. A parcela sem estado não é distribuída artificialmente pelo mapa.")
    lines(national.assign(Série="Frota existente"),"total_veiculos_eletrificados","Série","A frota aumentou ao longo do período")
    st.caption("Cada ponto é uma fotografia mensal. Não somamos fotografias como carros diferentes. O eixo vertical não começa em zero: ele destaca a evolução.")
    sales = dates(load("abve_publico_tecnologia_gold.csv"))
    st.subheader("Filtros da comparação de emplacamentos")
    st.caption("Os controles abaixo alteram apenas as vendas e suas comparações anuais. Não mudam a fotografia da frota acima.")
    left,right = st.columns(2)
    years = left.multiselect("Anos para comparar",[2024,2025,2026],default=[2024,2025,2026],key="market_years")
    technologies = right.multiselect("Tecnologias dos emplacamentos",["BEV","PHEV"],default=["BEV","PHEV"],format_func=lambda v:TECH[v],key="market_tech")
    if not years or not technologies:
        st.info("Escolha ao menos um ano e uma tecnologia para ver a comparação.")
        return
    limit = 8 if 2026 in years else 12
    through = st.selectbox("Comparar janeiro até qual mês?",list(range(1,limit+1)),index=min(8,limit)-1,format_func=lambda v:MONTH_NAMES[v-1],help="Com 2026 selecionado, comparo até agosto. Sem 2026, posso comparar os anos completos.")
    plugin = sales.loc[sales.tecnologia.isin(technologies) & sales.data_referencia.dt.year.isin(years)].copy()
    plugin["Tecnologia"] = plugin.tecnologia.map(TECH)
    lines(plugin,"emplacamentos","Tecnologia","Novos emplacamentos: elétrico puro versus híbrido com tomada")
    st.caption("ABVE · veículos leves BEV/PHEV · jan/2024–ago/2026. MHEV fica fora. O filtro da frota acima não altera este histórico de emplacamentos.")
    mode = st.radio("Como acompanhar a evolução anual?",["Emplacamentos de cada mês","Acumulado desde janeiro"],horizontal=True)
    annual = plugin.loc[plugin.data_referencia.dt.month.le(through)]
    year_lines(annual,"emplacamentos",f"Evolução por ano: janeiro a {MONTHS[through-1].lower()}",cumulative=mode == "Acumulado desde janeiro")
    st.caption("Cores fixas: 2024 azul, 2025 verde e 2026 laranja. A comparação anual e as barras abaixo seguem o limite de mês escolhido. A linha contínua acima mostra o histórico disponível dos anos/tecnologias selecionados. Acumulado soma novos emplacamentos desde janeiro, não a frota.")
    comp = comparable_years(sales.loc[sales.data_referencia.dt.year.isin(years)],technologies,through)
    bars(comp,"Ano","Emplacamentos",f"Comparação justa: janeiro a {MONTHS[through-1].lower()} de cada ano","Emplacamentos")
    if len(comp) >= 2:
        before,after = comp.iloc[-2],comp.iloc[-1]
        st.success(f"1 e 2 · No mesmo intervalo de {through} meses, o recorte passou de {number(before.Emplacamentos)} em {before.Ano} para {number(after.Emplacamentos)} em {after.Ano}: crescimento de {pct(percent_change(after.Emplacamentos,before.Emplacamentos))} entre esses anos.")
    else:
        st.info("Selecione dois ou três anos para calcular a variação entre períodos.")
    full = comparable_years(sales.loc[sales.data_referencia.dt.year.le(2025)],technologies,through_month=12)
    st.write(f"**Referência adicional, independente dos anos escolhidos:** nos anos completos, 2025 versus 2024 cresceu **{pct(percent_change(full.iloc[1].Emplacamentos,full.iloc[0].Emplacamentos))}** para as tecnologias selecionadas. Já 2026 é parcial: não comparo oito meses com doze.")
    details(comp,"comparacao_jan_agosto.csv")

def geography():
    intro(2,"O mercado é grande em alguns lugares e avança em outros","Quantidade, velocidade de crescimento e participação na frota respondem perguntas diferentes. Depois, vamos comparar capitais e interior.","3 a 7")
    states = dates(load("evolucao_frota_por_estado.csv"))
    period = st.selectbox("Mês dos estados e capitais/interior",sorted(states.data_referencia.dt.strftime("%Y-%m").unique()),index=31)
    date = pd.Timestamp(period+"-01")
    selected = states.loc[states.data_referencia.eq(date) & states.uf.ne("Sem Informação")]
    top = selected.nlargest(10,"total_veiculos_eletrificados")
    bars(top,"uf","total_veiculos_eletrificados","3 · Os dez estados com a maior frota eletrificada")
    st.success(f"{top.iloc[0].uf} lidera em quantidade: {number(top.iloc[0].total_veiculos_eletrificados)} veículos no mês escolhido.")
    growth = selected.dropna(subset=["crescimento_percentual_anual"]).nlargest(10,"crescimento_percentual_anual")
    bars(growth,"uf","crescimento_percentual_anual","4 · Quem mais cresceu em relação ao mesmo mês do ano anterior?","%")
    if len(growth):
        lead = growth.iloc[0]
        st.info(f"{lead.uf} lidera a taxa: {pct(lead.crescimento_percentual_anual)}, partindo de {number(lead.total_ano_anterior)} e chegando a {number(lead.total_veiculos_eletrificados)}. Liderar crescimento não é liderar tamanho.")
    st.caption("SENATRAN · crescimento da frota em 12 meses, não vendas. Meses de 2024 não têm o ano anterior na base. Bases pequenas podem gerar taxas altas; UFs desconhecidas não entram.")
    state = st.selectbox("Acompanhar a evolução anual de qual estado?",sorted(states.loc[states.uf.ne("Sem Informação"),"uf"].unique()),index=sorted(states.loc[states.uf.ne("Sem Informação"),"uf"].unique()).index("SAO PAULO"))
    year_lines(states.loc[states.uf.eq(state)],"total_veiculos_eletrificados",f"Frota de {state}: evolução mês a mês em cada ano")
    st.caption("SENATRAN · estoque de veículos. Não acumulo a frota: cada ponto já é o total existente no mês. 2026 termina em agosto; cores identificam os anos.")
    city = load("penetracao_municipal_ibge.csv")
    st.subheader("5 e 6 · Cidades: tamanho versus participação")
    st.caption("Fotografia municipal fixa: agosto/2026. O filtro mensal acima não altera estas cidades. Fonte: SENATRAN + associação municipal IBGE.")
    state_city = st.selectbox("Estado dos rankings municipais",["Todos os estados"]+sorted(city.uf.unique()))
    minimum = st.number_input("Evitar taxas enganosas: frota total mínima da cidade",min_value=0,value=10000,step=1000)
    eligible = city.loc[city.frota_total_veiculos.ge(minimum) & (city.uf.eq(state_city) if state_city != "Todos os estados" else True)].copy()
    eligible["Cidade / UF"] = eligible.municipio+" / "+eligible.uf_ibge.fillna(eligible.uf)
    bars(eligible.nlargest(10,"quantidade_veiculos"),"Cidade / UF","quantidade_veiculos","Onde há mais eletrificados?")
    bars(eligible.nlargest(10,"participacao_eletrificada_na_frota_percentual"),"Cidade / UF","participacao_eletrificada_na_frota_percentual","Onde os eletrificados têm maior peso na frota local?","%")
    st.caption("Participação = eletrificados ÷ frota total local × 100. Frota total inclui todos os tipos de veículos da fonte, não só automóveis. O filtro mínimo vale para os dois rankings.")
    cap = dates(load("frota_capital_vs_interior.csv"))
    cap["Localidade"] = cap.tipo_localidade.map({"capital":"Capitais","interior":"Interior"})
    lines(cap,"total_veiculos_eletrificados","Localidade","7 · O interior também participa dessa expansão")
    current = cap.loc[cap.data_referencia.eq(date)]
    prior = cap.loc[cap.data_referencia.eq(date-pd.DateOffset(years=1))]
    for _,row in current.iterrows():
        old = prior.loc[prior.tipo_localidade.eq(row.tipo_localidade)]
        rate = percent_change(row.total_veiculos_eletrificados,old.iloc[0].total_veiculos_eletrificados) if len(old) else None
        st.write(f"**{row.Localidade}:** {pct(row.participacao_percentual)} da frota classificada; crescimento em 12 meses: **{pct(rate)}**.")
    st.caption("SENATRAN · localidades classificadas; Brasília como capital. Exclui registros não classificados. Mostra expansão da frota, não migração de clientes. Eixo vertical não começa em zero.")
    details(eligible[["Cidade / UF","quantidade_veiculos","frota_total_veiculos","participacao_eletrificada_na_frota_percentual"]].rename(columns={"quantidade_veiculos":"Eletrificados","frota_total_veiculos":"Frota total","participacao_eletrificada_na_frota_percentual":"Participação (%)"}),"cidades_comparacao.csv")

def technology_comparison(sales):
    """Comparo categorias da mesma publicação e do mesmo intervalo temporal."""
    rows,changes = [],[]
    for technology in ["BEV","PHEV","HEV","HEV FLEX"]:
        comp = comparable_years(sales.loc[sales.data_referencia.dt.year.ge(2025)],[technology])
        for _,row in comp.iterrows():
            rows.append({"Tecnologia":TECH[technology],"Ano":row.Ano,"Emplacamentos":row.Emplacamentos})
        changes.append((TECH[technology],percent_change(comp.iloc[1].Emplacamentos,comp.iloc[0].Emplacamentos)))
    return pd.DataFrame(rows),changes

def leaders():
    intro(3,"Quem transforma esse crescimento em emplacamentos?","Voltamos aos novos registros. Marca líder e modelo líder dependem do período e da tecnologia escolhidos — não de um ranking único para todo o mercado.","8, 9 e 10")
    models = dates(load("abve_publico_modelo_gold.csv"))
    year = st.selectbox("Ano do ranking (período comparável até agosto)",[2024,2025,2026],index=2)
    window = st.select_slider("Período do ranking",options=list(range(1,9)),value=(1,8),format_func=lambda v:MONTH_NAMES[v-1],help="Uso até agosto em todos os anos para manter a comparação consistente.")
    choice = st.selectbox("Que tipo de veículo comparar?",["Elétricos puros + híbridos com tomada","Só elétricos puros","Só híbridos com tomada"])
    tech = {"Elétricos puros + híbridos com tomada":["BEV","PHEV"],"Só elétricos puros":["BEV"],"Só híbridos com tomada":["PHEV"]}[choice]
    selected = models.loc[models.data_referencia.dt.year.eq(year) & models.data_referencia.dt.month.between(*window) & models.tecnologia.isin(tech)]
    brands,ranking = ranked_share(selected,["marca"]),ranked_share(selected,["marca","modelo"])
    a,b,c = st.columns(3)
    a.metric("Emplacamentos no recorte",number(selected.emplacamentos.sum()))
    b.metric("Marca líder",brands.iloc[0].marca)
    c.metric("Participação da líder",pct(brands.iloc[0]["Participação (%)"]))
    st.success(f"8 · {brands.iloc[0].marca} lidera com {number(brands.iloc[0].emplacamentos)} registros. A participação usa todas as marcas do filtro, não apenas o top 10.")
    bars(brands.head(10),"marca","emplacamentos","8 · Marcas líderes no recorte","Emplacamentos")
    ranking["Modelo / marca"] = ranking.modelo+" / "+ranking.marca
    bars(ranking.head(10),"Modelo / marca","emplacamentos","9 · Modelos mais emplacados no recorte","Emplacamentos")
    st.write(f"**Modelo líder:** {ranking.iloc[0].modelo} ({ranking.iloc[0].marca}), com {number(ranking.iloc[0].emplacamentos)} registros e {pct(ranking.iloc[0]['Participação (%)'])} do recorte.")
    st.caption(f"ABVE · {MONTHS[window[0]-1]}–{MONTHS[window[1]-1]}/{year} · nomes conforme publicação. Modelo não é versão. Cidade e modelo são agregados independentes: não identificam o modelo vendido em cada cidade.")
    shares = []
    for compared_year in [2024,2025,2026]:
        scope = models.loc[models.data_referencia.dt.year.eq(compared_year) & models.data_referencia.dt.month.between(*window) & models.tecnologia.isin(tech)]
        share = ranked_share(scope,["marca"])
        shares.append(share.loc[share.marca.isin(brands.head(5).marca)].assign(Ano=str(compared_year)))
    bars(pd.concat(shares),"marca","Participação (%)","As cinco marcas líderes do filtro ganharam ou perderam participação?","%","Ano")
    st.caption(f"Comparo {MONTH_NAMES[window[0]-1].lower()} a {MONTH_NAMES[window[1]-1].lower()} em todos os anos. Participação usa o total de cada ano/tecnologia; não só estas cinco marcas. Ausência de registro não é preenchida com zero.")
    comparison,changes = technology_comparison(dates(load("abve_publico_tecnologia_gold.csv")))
    bars(comparison,"Tecnologia","Emplacamentos","10 · Qual tecnologia avançou mais? Janeiro–agosto de 2025 versus 2026","Emplacamentos","Ano")
    fastest = max(changes,key=lambda x:x[1])
    st.info(f"{fastest[0]} apresentou o maior crescimento percentual entre as quatro categorias: {pct(fastest[1])}. Maior taxa não significa necessariamente maior aumento em quantidade.")
    st.caption("ABVE · o filtro do ranking acima não altera este comparativo. Cores representam os anos; ambos têm oito meses. MHEV fica fora para não misturar mudanças de classificação.")
    details(brands.rename(columns={"marca":"Marca","emplacamentos":"Emplacamentos"}),"participacao_marcas.csv")
    with st.expander("Curiosidade: autonomia e consumo por versão"):
        cat = load("inmetro_versoes_eletrificadas.csv")
        brand = st.selectbox("Marca no catálogo Inmetro 2026",sorted(cat.loc[cat.ano_ciclo.eq(2026)].marca.unique()))
        cat = cat.loc[cat.ano_ciclo.eq(2026) & cat.marca.eq(brand)]
        st.caption("PBEV/Inmetro · ciclo 2026 parcial, com duas linhas ambíguas separadas. Autonomia de ensaio não é uso real. Não associo versões automaticamente às vendas ABVE.")
        st.dataframe(cat[["modelo","versao","propulsao_original","consumo_energetico_mj_km","autonomia_eletrica_ensaio_km"]].rename(columns={"modelo":"Modelo","versao":"Versão","propulsao_original":"Propulsão","consumo_energetico_mj_km":"Consumo (MJ/km)","autonomia_eletrica_ensaio_km":"Autonomia de ensaio (km)"}),hide_index=True,width="stretch")

def opportunities():
    intro(4,"Onde vale investigar a próxima oportunidade?","Mais renda pode acompanhar maior adoção, mas não prova a causa. Aqui levantamos pistas para pesquisa comercial e de infraestrutura, não promessas de demanda futura.","11 a 14")
    city = load("penetracao_municipal_ibge.csv")
    corr = load("correlacao_municipal_socioeconomia_adocao.csv")
    corr = corr.loc[corr.metodo.eq("spearman") & corr.indicador_adocao.eq("Eletrificados por 100 mil habitantes")].copy()
    corr["Indicador"] = corr.variavel_socioeconomica.map({"PIB per capita aproximado (R$)":"PIB por habitante","População do Censo 2022 (pessoas)":"População","Renda domiciliar per capita média (R$)":"Renda domiciliar por pessoa"})
    # Uma correlação não é uma quantidade de veículos: preservo casas decimais na dica.
    st.subheader("11 · Renda, PIB e população acompanham a adoção?")
    chart = alt.Chart(corr).mark_bar(color=TEAL).encode(x=alt.X("coeficiente_correlacao:Q",title="Associação de posições (−1 a +1)",scale=alt.Scale(domain=[-1,1])),y=alt.Y("Indicador:N",sort="-x",title=None),tooltip=["Indicador:N",alt.Tooltip("coeficiente_correlacao:Q",title="Spearman",format=".3f")])
    st.altair_chart(style(chart.properties(height=200)),width="stretch")
    st.write("**Como ler:** perto de +1, cidades com indicador maior tendem a ocupar posições maiores em adoção. Perto de zero, a associação de posições é pequena. **Correlação não demonstra causa e efeito.**")
    st.caption("5.528 localidades cruzadas · frota ago/2026; renda/população do Censo 2022, PIB 2023. Anos diferentes limitam a interpretação.")
    columns = ["municipio","uf","rendimento_domiciliar_per_capita_medio_2022_reais","veiculos_eletrificados_por_100_mil_habitantes"]
    valid = city[columns].dropna()
    scatter = alt.Chart(alt.Data(values=valid.to_dict("records"))).mark_circle(size=24,opacity=.35,color=TEAL).encode(
        x=alt.X("rendimento_domiciliar_per_capita_medio_2022_reais:Q",title="Renda média por pessoa (R$/mês, 2022)"),
        y=alt.Y("veiculos_eletrificados_por_100_mil_habitantes:Q",title="Eletrificados por 100 mil habitantes"),
        tooltip=[alt.Tooltip("municipio:N",title="Município"),alt.Tooltip("uf:N",title="Estado"),alt.Tooltip("rendimento_domiciliar_per_capita_medio_2022_reais:Q",title="Renda (R$)",format=".2f"),alt.Tooltip("veiculos_eletrificados_por_100_mil_habitantes:Q",title="Eletrificados/100 mil",format=".1f")])
    st.subheader("Cada ponto é uma cidade: renda versus adoção")
    st.altair_chart(style(scatter.properties(height=330)),width="stretch")
    st.caption("Sem amostragem: todos os municípios com os indicadores válidos. Frota 2026 / população 2022. PIB por habitante mede produção econômica, não renda disponível do morador.")
    opportunity = load("oportunidade_municipal_preliminar.csv")
    candidates = opportunity.loc[opportunity.oportunidade_preliminar.astype(str).str.lower().isin(["t","true"])].copy()
    st.subheader("12 e 13 · Uma lista para investigar, não uma previsão de compra")
    st.metric("Municípios no filtro preliminar",number(len(candidates)))
    st.write("O filtro combina condições econômicas favoráveis e adoção relativamente baixa. São candidatas à pesquisa: precisamos verificar consumidores, concessionárias, preços e recarga antes de afirmar potencial de vendas.")
    shown = candidates[["municipio","uf","rendimento_domiciliar_per_capita_medio_2022_reais","pib_per_capita_aproximado","veiculos_eletrificados_por_100_mil_habitantes"]].rename(columns={"municipio":"Município","uf":"Estado","rendimento_domiciliar_per_capita_medio_2022_reais":"Renda por pessoa (R$/mês, 2022)","pib_per_capita_aproximado":"PIB por habitante (R$, 2023)","veiculos_eletrificados_por_100_mil_habitantes":"Eletrificados por 100 mil habitantes"})
    st.dataframe(shown,hide_index=True,width="stretch")
    st.caption("Triagem sensível aos cortes: nove cenários variaram de 7 a 30 cidades. Não é probabilidade de compra nem ranking validado de crescimento futuro.")
    fleet = dates(load("frota_regional_mensal.csv"))
    fleet = fleet.loc[fleet.data_referencia.eq(fleet.data_referencia.max()) & fleet.regiao.ne("UF não informada")].copy()
    fleet["Participação (%)"] = 100*fleet.total_veiculos_eletrificados/fleet.total_veiculos_eletrificados.sum()
    charge = load("infraestrutura_recarga_abve_gold.csv")
    charge = charge.loc[charge.nivel_geografico.eq("regiao")].rename(columns={"participacao_nacional_percentual":"Participação (%)"})
    compare = pd.concat([fleet[["regiao","Participação (%)"]].assign(Indicador="Frota eletrificada"),charge[["regiao","Participação (%)"]].assign(Indicador="Pontos de recarga")])
    bars(compare,"regiao","Participação (%)","14 · Distribuição da frota versus distribuição da recarga","%","Indicador")
    st.warning("É uma hipótese, não uma medida de déficit. A frota inclui híbridos sem tomada; pontos ABVE/Tupi são públicos/semipúblicos. Faltam capacidade, uso, demanda por hora e coordenadas completas para escolher locais ideais.")
    st.caption("Agosto/2026 · SENATRAN entre UFs conhecidas; recarga ABVE/Tupi nacional. Uma participação menor de recarga não comprova falta de carregadores.")
    with st.expander("Ver o mapa comunitário de recarga — cobertura parcial"):
        osm = load("recarga_osm.csv")
        access = st.multiselect("Acesso declarado",sorted(osm.acesso_classificado.unique()),default=["publico_declarado"])
        mapped = osm.loc[osm.acesso_classificado.isin(access)]
        st.metric("Objetos neste filtro do mapa",number(len(mapped)))
        if len(mapped):
            st.map(mapped.rename(columns={"latitude":"lat","longitude":"lon"})[["lat","lon"]].dropna())
        else:
            st.info("Nenhum objeto para o filtro escolhido.")
        st.caption("© OpenStreetMap contributors · ODbL-1.0 · https://www.openstreetmap.org/copyright. Um objeto não é necessariamente um carregador; ausência no mapa não comprova ausência de recarga.")

def future():
    intro(5,"Prever é possível. Confiar na previsão exige outro passo","Testamos o passado como se ainda não soubéssemos o resultado. Um modelo complexo só merece confiança se melhorar uma referência simples e representar bem seus erros.","15")
    st.warning("Temos experimentos, não uma previsão de vendas aprovada. Os modelos escolhidos para BEV/PHEV não superaram a referência simples no teste final.")
    performance = load("ml_abve_selecao_modelos.csv")
    comparison = performance.melt(id_vars="tecnologia",value_vars=["wape_teste_medio","wape_persistencia_teste"],var_name="Método",value_name="Erro (%)")
    comparison["Método"] = comparison["Método"].map({"wape_teste_medio":"Modelo escolhido","wape_persistencia_teste":"Repetir o último mês"})
    comparison["Tecnologia"] = comparison.tecnologia.map(TECH)
    bars(comparison,"Tecnologia","Erro (%)","O modelo errou menos que uma previsão simples?","%","Método")
    st.caption("Erro percentual ponderado (WAPE) = soma dos erros absolutos ÷ soma dos valores reais × 100. Menor é melhor. Média dos horizontes 1–3 meses no teste fev–ago/2026; não é chance de acerto.")
    coverage = load("ml_intervalos_cobertura.csv")
    coverage["Alvo"] = coverage.alvo.map(TECH).fillna(coverage.alvo)
    bars(coverage,"Alvo","cobertura_teste_percentual","As faixas de previsão incluíram o valor real?","%")
    st.write("Esperávamos cobertura nominal de **80%**. Quatro das cinco regiões ficaram abaixo. Usamos apenas quatro meses para calibrar e sete para testar cada alvo; poucos exemplos não garantem o próximo resultado. Este protocolo de um mês é separado do comparativo de três horizontes acima.")
    technology = st.selectbox("Explorar uma projeção de um mês",["BEV","PHEV"],format_func=lambda v:TECH[v])
    history = dates(load("abve_plugin_mensais.csv"))
    history = history.loc[history.tecnologia.eq(technology)].tail(12)
    projection = dates(load("ml_intervalos_projecoes.csv"))
    projection = projection.loc[projection.fonte_alvo.eq("ABVE_emplacamentos") & projection.alvo.eq(technology)]
    observed = history.rename(columns={"emplacamentos_mes":"Quantidade"}).assign(Leitura="Observado")
    predicted = projection.rename(columns={"previsto":"Quantidade"}).assign(Leitura="Projeção experimental")
    chartdata = pd.concat([observed[["data_referencia","Quantidade","Leitura"]],predicted[["data_referencia","Quantidade","Leitura"]]])
    base = alt.Chart(chartdata).encode(x=alt.X("data_referencia:T",title="Mês",axis=alt.Axis(format="%m/%Y")),y=alt.Y("Quantidade:Q",title="Emplacamentos",scale=alt.Scale(zero=False)))
    points = base.mark_point(filled=True,size=100).encode(color=alt.Color("Leitura:N",scale=alt.Scale(domain=["Observado","Projeção experimental"],range=[TEAL,ORANGE])),tooltip=[alt.Tooltip("data_referencia:T",format="%m/%Y",title="Mês"),"Leitura:N",alt.Tooltip("Quantidade:Q",format=",.0f")])
    obsline = base.transform_filter(alt.datum.Leitura == "Observado").mark_line(color=TEAL,strokeWidth=3)
    interval = alt.Chart(projection).mark_rule(color=ORANGE,strokeWidth=5).encode(x="data_referencia:T",y="limite_inferior:Q",y2="limite_superior:Q",tooltip=[alt.Tooltip("limite_inferior:Q",title="Limite inferior",format=",.0f"),alt.Tooltip("limite_superior:Q",title="Limite superior",format=",.0f")])
    st.subheader("O ponto laranja é a projeção; a barra é sua faixa experimental")
    st.altair_chart(style((obsline+interval+points).properties(height=350)),width="stretch")
    st.caption("Observado até ago/2026; setembro é projeção, não coleta. Eixo vertical não começa em zero. Uso a série realmente usada no treino: PHEV jul/2024 difere em uma unidade do painel atual.")
    st.info("Precisamos avaliar novos meses sem reajustar a escolha para favorecer o teste. Não estendemos estas faixas a cidades, marcas ou vários anos sem dados e validação adequados.")
    details(coverage[["Alvo","n_calibracao","n_teste","nivel_nominal_percentual","cobertura_teste_percentual"]].rename(columns={"n_calibracao":"Meses de calibração","n_teste":"Meses de teste","nivel_nominal_percentual":"Cobertura esperada (%)","cobertura_teste_percentual":"Cobertura observada (%)"}),"incerteza_explicada.csv")

def answers():
    intro(6,"As 15 perguntas: o que os dados permitem dizer","Uma hipótese exploratória não recebe o mesmo peso que uma contagem observada. Quando a evidência ainda não basta, isso fica explícito.","1 a 15")
    sales = dates(load("abve_publico_tecnologia_gold.csv"))
    comp = comparable_years(sales)
    states = dates(load("evolucao_frota_por_estado.csv"))
    latest = states.loc[states.data_referencia.eq(states.data_referencia.max()) & states.uf.ne("Sem Informação")]
    largest,fastest = latest.nlargest(1,"total_veiculos_eletrificados").iloc[0],latest.nlargest(1,"crescimento_percentual_anual").iloc[0]
    city = load("penetracao_municipal_ibge.csv")
    leadcity = city.nlargest(1,"quantidade_veiculos").iloc[0]
    penetration = city.loc[city.frota_total_veiculos.ge(10000)].nlargest(1,"participacao_eletrificada_na_frota_percentual").iloc[0]
    models = dates(load("abve_publico_modelo_gold.csv"))
    chosen = models.loc[models.data_referencia.dt.year.eq(2026) & models.tecnologia.isin(["BEV","PHEV"])]
    brand,model = ranked_share(chosen,["marca"]).iloc[0],ranked_share(chosen,["marca","modelo"]).iloc[0]
    cap = dates(load("frota_capital_vs_interior.csv"))
    interior = cap.loc[cap.data_referencia.eq(cap.data_referencia.max()) & cap.tipo_localidade.eq("interior")].iloc[0]
    _,changes = technology_comparison(sales)
    tech = max(changes,key=lambda x:x[1])
    quick = [
        ("Respondida no recorte",f"BEV + PHEV somaram {number(comp.iloc[0].Emplacamentos)}, {number(comp.iloc[1].Emplacamentos)} e {number(comp.iloc[2].Emplacamentos)} em jan–ago de 2024, 2025 e 2026.",1),
        ("Respondida no recorte",f"Jan–ago/2026 versus jan–ago/2025: {pct(percent_change(comp.iloc[2].Emplacamentos,comp.iloc[1].Emplacamentos))}. No capítulo 1 também comparo 2025 e 2024 completos.",1),
        ("Respondida",f"{largest.uf} lidera ago/2026 com {number(largest.total_veiculos_eletrificados)} eletrificados em frota, não vendas.",2),
        ("Respondida",f"{fastest.uf} lidera o crescimento da frota em 12 meses em ago/2026: {pct(fastest.crescimento_percentual_anual)}. Taxa não é tamanho.",2),
        ("Respondida",f"{leadcity.municipio} ({leadcity.uf}) lidera a base municipal cruzada: {number(leadcity.quantidade_veiculos)} eletrificados em ago/2026.",2),
        ("Respondida com filtro",f"Entre cidades com ao menos 10 mil veículos de frota total, {penetration.municipio} lidera com {pct(penetration.participacao_eletrificada_na_frota_percentual)}. O denominador inclui todos os tipos de veículos.",2),
        ("Respondida no recorte",f"O interior também está presente: {pct(interior.participacao_percentual)} da frota classificada em ago/2026. Trajetória e crescimento em 12 meses estão no capítulo 2.",2),
        ("Respondida no recorte",f"{brand.marca} lidera BEV + PHEV em jan–ago/2026, com {pct(brand['Participação (%)'])} dos emplacamentos do recorte.",3),
        ("Respondida no recorte",f"{model.modelo} ({model.marca}) lidera BEV + PHEV em jan–ago/2026, com {number(model.emplacamentos)} emplacamentos.",3),
        ("Respondida no recorte",f"Entre quatro categorias comparáveis, {tech[0]} cresceu mais em percentual: {pct(tech[1])} em jan–ago/2026 versus 2025. MHEV fica fora.",3),
        ("Associação, não causalidade","As três variáveis têm associação positiva com eletrificados por habitante: Spearman 0,690 para renda, 0,577 para PIB por habitante e 0,354 para população. Renda/população 2022, PIB 2023 e frota ago/2026.",4),
        ("Triagem exploratória","O filtro preliminar selecionou 17 municípios com condições favoráveis e adoção relativamente baixa. Veja a lista e os limites no capítulo 4.",4),
        ("Ainda não comprovada","As 17 cidades orientam pesquisa, mas não preveem qual crescerá mais. Faltam validação futura e fatores locais para afirmar potencial de crescimento.",4),
        ("Hipótese para investigação","Comparo a participação regional da frota e dos pontos públicos/semipúblicos. A diferença não prova déficit: faltam capacidade, uso, demanda horária e frota exclusivamente conectável.",4),
        ("Experimental, não aprovada","Podemos gerar projeções, mas os modelos de vendas escolhidos não venceram a referência no teste. As faixas têm poucos exemplos e cobertura insuficiente em quatro regiões.",5)]
    for i,(question,(status,answer,chapter)) in enumerate(zip(QUESTIONS,quick),1):
        with st.container(border=True):
            st.subheader(f"{i}. {question}")
            st.caption(f"{status.upper()} · VEJA O CAPÍTULO {chapter}")
            st.write(answer)
    st.caption("Este mapa usa ago/2026 para frota e jan–ago/2026 para rankings de vendas. Os filtros dos outros capítulos não alteram este resumo.")

def methodology():
    intro(7,"De onde vieram os números?","As fontes medem coisas diferentes. Não somamos dados de entidades distintas como se fossem o mesmo mercado, e mostramos onde os dados terminam.","fontes e critérios")
    st.markdown("""- **SENATRAN:** frota mensal por combustível/localidade; definição ampla de eletrificados.
- **ABVE:** emplacamentos de leves por tecnologia, marca/modelo ou município; fatos independentes.
- **IBGE:** população/renda 2022 e PIB 2023; não são indicadores atuais de 2026.
- **Inmetro:** catálogo e ensaios de consumo/autonomia; não vendas nem autonomia real.
- **ABVE/Tupi e OpenStreetMap:** infraestrutura agregada e mapa comunitário parcial; não são inventário completo.

O período observado é **jan/2024–ago/2026**. Meses posteriores são projeções identificadas. CSVs de pesquisa no Gemini sem referência verificável não entram como dados oficiais no treino principal.""")
    with st.expander("Limitações que afetam a leitura"):
        st.write("Preservo registros sem UF/localidade. Não completo modelos ou cidades ausentes com zero. A classificação MHEV mudou; comparo principalmente BEV/PHEV. PHEV jul/2024 difere em uma unidade entre a série antiga e o painel atual. Inmetro 2026 é parcial, com duas linhas em quarentena e sem associação automática às vendas.")
        st.write("O ML é retrospectivo, com poucos meses e sem versões históricas completas de divulgação. Não há aprovação operacional, probabilidade individual de compra, falhas de bateria ou depreciação neste painel.")
    with st.expander("Para conhecer a implementação"):
        st.write("Python coleta e valida, Parquet guarda as camadas, PostgreSQL organiza as tabelas e Streamlit lê os exports. Abrir o painel não executa coleta nem treino.")
        st.code("python -m src.run_project\npython -m streamlit run streamlit_app.py",language="powershell")
    st.markdown("Fontes: [SENATRAN](https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/estatisticas-frota-de-veiculos-senatran) · [ABVE](https://abve.org.br/abve-data/bi-geral/) · [IBGE](https://sidra.ibge.gov.br/) · [Inmetro](https://www.gov.br/inmetro/) · [OpenStreetMap](https://www.openstreetmap.org/copyright)")

st.title("A jornada dos veículos eletrificados no Brasil")
st.caption("Como o mercado cresceu, onde avançou e quais oportunidades merecem investigação · jan/2024–ago/2026")
PAGES = {"1 · A história do mercado":market,"2 · Onde a adoção avança":geography,"3 · Quem lidera as vendas":leaders,"4 · Onde investigar oportunidades":opportunities,"5 · O que esperar do futuro":future,"6 · Respostas às 15 perguntas":answers,"7 · Dados e critérios":methodology}
page = st.sidebar.radio("Siga a história",list(PAGES))
st.sidebar.caption("Comece no capítulo 1 ou consulte diretamente as 15 respostas no capítulo 6.")
guide()
PAGES[page]()
