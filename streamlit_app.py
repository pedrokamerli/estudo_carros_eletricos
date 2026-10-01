"""Exploro meu projeto em uma prévia local, sem senha de banco ou dados inventados."""

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data/portfolio"
st.set_page_config(page_title="Mercado elétrico BR", page_icon="🚘", layout="wide")


@st.cache_data(show_spinner=False)
def read_export(name, modified):
    """Uso a data de modificação na chave do cache para refletir novos exports."""
    return pd.read_csv(DATA / name)


def load(name):
    """Leio apenas exports públicos. Não acesso .env, banco ou arquivos do computador."""
    path = DATA / name
    if not path.exists():
        st.error(f"Export ausente: {name}. Execute python -m src.run_project na raiz do projeto.")
        st.stop()
    return read_export(name, path.stat().st_mtime_ns).copy()


def dates(frame):
    """Monto uma competência mensal usando as colunas do próprio dado."""
    frame = frame.copy()
    if "data_referencia" in frame:
        frame["data_referencia"] = pd.to_datetime(frame.data_referencia)
    else:
        frame["data_referencia"] = pd.to_datetime(dict(year=frame.ano_referencia, month=frame.mes_referencia, day=1))
    return frame.sort_values("data_referencia")


def number(value):
    return f"{value:,.0f}".replace(",", ".")


def table_download(frame, name):
    """Deixo baixar somente o recorte mostrado, sem disparar coleta ou alterar o banco."""
    st.dataframe(frame, hide_index=True, width="stretch")
    st.download_button("Baixar este recorte em CSV", frame.to_csv(index=False).encode("utf-8-sig"), name, "text/csv", key=name)


def overview():
    national = dates(load("evolucao_frota_nacional.csv"))
    period = st.selectbox("Competência da frota", national.data_referencia.dt.strftime("%Y-%m").tolist(), index=len(national) - 1)
    latest = national.loc[national.data_referencia.eq(pd.Timestamp(period + "-01"))].iloc[0]
    a, b, c = st.columns(3)
    a.metric("Frota eletrificada nacional", number(latest.total_veiculos_eletrificados))
    b.metric("Com UF conhecida", number(latest.total_veiculos_uf_informada))
    c.metric("Sem UF informada", number(latest.total_veiculos_sem_uf))
    st.caption("SENATRAN • estoque no mês • definição ampla de combustíveis eletrificados. Nunca somo estoques de meses diferentes como veículos únicos.")
    st.subheader("Evolução da frota nacional")
    st.line_chart(national.set_index("data_referencia")[["total_veiculos_eletrificados", "total_veiculos_sem_uf"]])
    regions = dates(load("frota_regional_mensal.csv"))
    st.subheader("Frota observada por região")
    st.line_chart(regions.loc[regions.regiao.ne("UF não informada")].pivot(index="data_referencia", columns="regiao", values="total_veiculos_eletrificados"))
    table_download(regions.loc[regions.data_referencia.eq(latest.data_referencia)], "regioes_competencia.csv")


def geography():
    states = dates(load("frota_por_estado.csv"))
    period = st.selectbox("Competência dos estados", sorted(states.data_referencia.dt.strftime("%Y-%m").unique()), index=len(states.data_referencia.unique()) - 1)
    state_month = states.loc[states.data_referencia.eq(pd.Timestamp(period + "-01"))]
    st.bar_chart(state_month.sort_values("total_veiculos_eletrificados", ascending=False).set_index("uf")["total_veiculos_eletrificados"])
    st.caption("Somente UFs conhecidas. A parcela sem UF permanece no total nacional da Visão geral.")
    municipal = load("penetracao_municipal_ibge.csv")
    ref = municipal.iloc[0]
    st.subheader(f"Municípios • fotografia {int(ref.ano_referencia_frota):04d}-{int(ref.mes_referencia_frota):02d}")
    st.info("O filtro mensal acima vale apenas para estados. A tabela municipal abaixo é da última competência exportada.")
    uf = st.selectbox("Estado dos municípios", ["Todos"] + sorted(municipal.uf.unique()))
    if uf != "Todos":
        municipal = municipal.loc[municipal.uf.eq(uf)]
    minimum = st.number_input("Frota total mínima no município", min_value=0, value=10000, step=1000)
    metric = st.selectbox("Ordenar municípios por", ["quantidade_veiculos", "participacao_eletrificada_na_frota_percentual", "veiculos_eletrificados_por_100_mil_habitantes"])
    selected = municipal.loc[municipal.frota_total_veiculos.ge(minimum)].sort_values(metric, ascending=False)
    st.caption("População/renda: Censo 2022. PIB: 2023. Quantidade é frota, não vendas. Municípios sem associação IBGE não recebem valores inventados.")
    table_download(selected.head(50), "municipios_top50_filtrado.csv")
    st.caption("O mínimo de frota é um filtro de exploração, não uma regra que altera a base original.")


def sales():
    plugins = dates(load("abve_plugin_mensais.csv"))
    st.subheader("Emplacamentos nacionais mensais • ABVE")
    st.caption("Fluxo de veículos leves BEV/PHEV. Não é soma de toda eletrificação nem medida de demanda não atendida.")
    st.line_chart(plugins.pivot(index="data_referencia", columns="tecnologia", values="emplacamentos_mes"))
    year = st.selectbox("Ano para os emplacamentos plug-in", [2024, 2025, 2026], index=2)
    selected = plugins.loc[plugins.data_referencia.dt.year.eq(year)]
    st.metric(f"BEV + PHEV nos {selected.data_referencia.nunique()} meses disponíveis de {year}", number(selected.emplacamentos_mes.sum()))
    table_download(selected, "emplacamentos_plugin_filtrados.csv")
    st.warning("2026 termina em agosto. Não compare seu acumulado com 12 meses de 2024/2025. A série ABVE total mudou de classificação em janeiro/2025; uso aqui BEV e PHEV separadamente.")
    brands = dates(load("ranking_marcas_fenabrave_mensal.csv"))
    # Retiro janeiro/2024 deste comparativo, pois cobre apenas autos.
    brands = brands.loc[brands.segmento_veiculos.eq("autos_e_comerciais_leves")]
    st.subheader("Ranking mensal de fabricantes • FENABRAVE")
    period = st.selectbox("Mês do ranking", sorted(brands.data_referencia.dt.strftime("%Y-%m").unique()), index=brands.data_referencia.nunique() - 1)
    category = st.selectbox("Categoria publicada pela FENABRAVE", sorted(brands.categoria_fenabrave.unique()))
    selected = brands.loc[brands.data_referencia.eq(pd.Timestamp(period + "-01")) & brands.categoria_fenabrave.eq(category)].sort_values("posicao")
    st.bar_chart(selected.set_index("marca")["quantidade_emplacada"])
    st.caption("Ranking parcial. Quantidade não listada não significa zero; categorias FENABRAVE não equivalem automaticamente a BEV/PHEV/HEV ABVE.")
    table_download(selected, "marcas_mensais_filtradas.csv")
    models = load("ranking_modelos_noticias_gold.csv")
    with st.expander("Modelos: sete listas documentais, não uma série completa"):
        source = st.selectbox("Lista publicada", sorted(models.fonte_id.unique()))
        table_download(models.loc[models.fonte_id.eq(source)].sort_values("posicao"), "modelos_lista_publicada.csv")


def enrichment():
    st.subheader("Histórico automático ABVE e catálogo Inmetro")
    kind = st.selectbox("Base para explorar", ["Modelos ABVE", "Municípios ABVE", "Versões Inmetro"])
    if kind == "Versões Inmetro":
        frame = load("inmetro_versoes_eletrificadas.csv")
        cycle = st.selectbox("Ciclo do catálogo", sorted(frame.ano_ciclo.unique()), index=2)
        brand = st.selectbox("Marca no Inmetro", ["Todas"] + sorted(frame.marca.unique()))
        selected = frame.loc[frame.ano_ciclo.eq(cycle)]
        if brand != "Todas":
            selected = selected.loc[selected.marca.eq(brand)]
        st.warning("Catálogo de versões e ensaio padronizado. Autonomia não é uso real; linhas não são emplacamentos. Ciclo 2026 parcial: duas linhas ambíguas estão em quarentena. Ciclo anual não significa versão do catálogo conhecida naquele mês. Sem associação automática ao nome ABVE.")
        table_download(selected, "catalogo_inmetro_filtrado.csv")
        return
    filename = "abve_publico_modelo_gold.csv" if kind == "Modelos ABVE" else "abve_publico_municipio_gold.csv"
    frame = dates(load(filename))
    period = st.selectbox("Competência ABVE pública", sorted(frame.data_referencia.dt.strftime("%Y-%m").unique()), index=31)
    technologies = st.multiselect("Tecnologias do painel", sorted(frame.tecnologia.unique()), default=["BEV", "PHEV"])
    selected = frame.loc[frame.data_referencia.eq(pd.Timestamp(period + "-01")) & frame.tecnologia.isin(technologies)]
    st.metric("Emplacamentos neste recorte", number(selected.emplacamentos.sum()))
    st.caption("32 meses observados. MHEV foi mantido separado. A soma com MHEV difere do total ABVE que exclui essa categoria. Ausência de linha não é automaticamente zero; localidades desconhecidas permanecem na base.")
    table_download(selected.sort_values("emplacamentos", ascending=False), "abve_publico_recorte.csv")
    st.info("Modelo e município são agregados separados; esta base não informa o modelo vendido em cada município. BEV/PHEV são o recorte preferido para comparação temporal.")


def ml():
    st.warning("Previsões experimentais, sem aprovação operacional. Os intervalos de um mês foram calibrados em amostra pequena; quatro regiões ficaram abaixo da cobertura nominal. Snapshot atual: não possuo versões históricas completas de divulgação.")
    st.subheader("Incerteza: protocolo separado de um mês")
    table_download(load("ml_intervalos_cobertura.csv"), "cobertura_intervalos.csv")
    st.caption("Seleção: jul–set/2025; calibração: out/2025–jan/2026; teste: fev–ago/2026. Apenas quatro meses de calibração e sete de teste. 80% é nominal, não uma garantia. O método desta análise pode diferir da seleção de três horizontes abaixo.")
    st.subheader("Frota regional: desempenho fora do treino")
    selection = load("ml_frota_regional_selecao_modelos.csv")
    st.bar_chart(selection.set_index("regiao")[["wape_teste_medio", "wape_persistencia_teste"]])
    st.caption("WAPE em percentual, menor é melhor. Média dos horizontes 1–3 meses. Escolha congelada na validação, antes do teste.")
    table_download(selection, "comparacao_ml_regional.csv")
    history = dates(load("frota_regional_mensal.csv"))
    future = dates(load("ml_frota_regional_projecoes_experimentais.csv"))
    region = st.selectbox("Região da projeção", sorted(future.regiao.unique()))
    observed = history.loc[history.regiao.eq(region)].set_index("data_referencia").total_veiculos_eletrificados.rename("Frota observada")
    predicted = future.loc[future.regiao.eq(region)].set_index("data_referencia").frota_prevista.rename("Projeção experimental")
    st.line_chart(pd.concat([observed, predicted], axis=1))
    st.caption("Observações encerram em agosto/2026. Meses posteriores são projeções, não novos dados coletados. Cinco previsões independentes não formam automaticamente uma previsão nacional conciliada.")
    st.subheader("Vendas nacionais: o ML ainda não venceu a referência")
    table_download(load("ml_abve_selecao_modelos.csv"), "avaliacao_vendas_abve.csv")
    st.subheader("Teste adicional com indicadores econômicos")
    table_download(load("ml_macro_selecao.csv"), "avaliacao_contexto_economico.csv")
    st.caption("Neste experimento de um passo, o Ridge com macro não foi escolhido. Erros de um horizonte não se comparam diretamente com a média de três horizontes acima.")


def infrastructure():
    st.subheader("Objetos de recarga mapeados • OpenStreetMap")
    osm = load("recarga_osm.csv")
    access = st.multiselect("Acesso declarado no mapa", sorted(osm.acesso_classificado.unique()), default=["publico_declarado"])
    shown = osm.loc[osm.acesso_classificado.isin(access)]
    st.metric("Objetos neste filtro", number(len(shown)))
    st.warning("Mapa comunitário parcial. Um objeto não equivale ao número de carregadores. Ausência no mapa não prova ausência de recarga; acesso desconhecido não é acesso público.")
    if not shown.empty:
        st.map(shown.rename(columns={"latitude": "lat", "longitude": "lon"})[["lat", "lon"]].dropna())
    else:
        st.info("Nenhum objeto corresponde ao filtro.")
    st.caption("© OpenStreetMap contributors • ODbL-1.0 • https://www.openstreetmap.org/copyright. Coordenadas de alguns objetos são aproximadas.")
    table_download(shown, "objetos_osm_filtrados.csv")
    st.subheader("Contexto da rede elétrica • ONS")
    load_profile = dates(load("perfil_carga_ons_mensal_hora.csv"))
    subsystem = st.selectbox("Subsistema elétrico", sorted(load_profile.nom_subsistema.unique()))
    periods = sorted(load_profile.data_referencia.dt.strftime("%Y-%m").unique())
    period = st.selectbox("Mês da carga horária", periods, index=len(periods) - 1)
    selected = load_profile.loc[load_profile.nom_subsistema.eq(subsystem) & load_profile.data_referencia.eq(pd.Timestamp(period + "-01"))]
    st.line_chart(selected.set_index("hora")[["carga_media_mw", "carga_maxima_mw"]])
    st.caption("MWmed • carga total do subsistema, não contribuição de veículos elétricos. Sudeste/Centro-Oeste é um subsistema conjunto. ONS: Creative Commons Atribuição — https://dados.ons.org.br/dataset/curva-carga.")


def status():
    st.subheader("O que já está pronto e o que ainda falta")
    st.markdown("""
    Já tenho coleta e validação SENATRAN, IBGE, FENABRAVE, OSM, BCB e ONS;
    snapshots ABVE integrados; PostgreSQL/Silver/Gold; esquema dimensional;
    experimentos de ML e exports. O estudo observado termina em agosto/2026.

    Também tenho captura automática ABVE de 32 meses por tecnologia, marca/modelo e
    município; catálogo Inmetro integrado com quarentena; auditoria da incerteza publicada.

    Ainda faltam:

    - Revisar associações entre nomes de modelos ABVE e versões Inmetro; não faço join automático ambíguo.
    - Monitorar mudanças de layout do painel público ABVE; recarga continua como snapshot manual.
    - Ampliar validação prospectiva da incerteza antes de recomendar previsões.
    - Construir e validar o dashboard Power BI e suas medidas DAX.

    Compra individual, falhas de bateria, autonomia real e depreciação com bateria/km
    exigem outros dados. Não são funcionalidades prontas deste projeto.
    """)
    st.info("Este aplicativo apenas lê exports. Abrir o painel não atualiza as fontes nem executa treinamento.")
    st.code("python -m src.run_project\npython -m streamlit run streamlit_app.py", language="powershell")
    st.markdown("Fontes: [SENATRAN](https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/estatisticas-frota-de-veiculos-senatran), [IBGE/SIDRA](https://sidra.ibge.gov.br/), [ABVE](https://abve.org.br/abve-data/), [FENABRAVE](https://www.fenabrave.org.br/portalv2/home/imprensa), [BCB](https://www.bcb.gov.br/acessoinformacao/dadosabertos), [ONS](https://dados.ons.org.br/dataset/curva-carga), [OSM](https://www.openstreetmap.org/copyright).")


st.title("Mercado de veículos eletrificados no Brasil")
st.caption("Meu laboratório de análise • observações jan/2024–ago/2026 • fontes e definições preservadas")
PAGES = {"Visão geral": overview, "Estados e municípios": geography,
         "Vendas, marcas e modelos": sales, "ML e previsões": ml,
         "Novas bases ABVE e Inmetro": enrichment,
         "Recarga e rede elétrica": infrastructure, "Status e fontes": status}
page = st.sidebar.radio("Explorar projeto", list(PAGES))
st.sidebar.caption("Estoque de frota ≠ fluxo de emplacamentos. Cada página possui seus próprios filtros.")
PAGES[page]()
