"""Produzo evidências de mercado e o estudo local, sem depender do dashboard."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.dashboard.story import identified_cities
from src.transformation.ibge_bronze_to_silver import normalize_municipality_name as norm
from src.utils.capitals import CAPITALS_BY_UF, UF_ABBREVIATION_BY_NAME

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/"data/portfolio"
REGIONS = {"Norte":"AC AP AM PA RO RR TO", "Nordeste":"AL BA CE MA PB PE PI RN SE",
           "Centro-Oeste":"DF GO MT MS", "Sudeste":"ES MG RJ SP", "Sul":"PR RS SC"}
REGION_BY_UF = {uf:region for region,states in REGIONS.items() for uf in states.split()}
CAPITAL_BY_SIGLA = {UF_ABBREVIATION_BY_NAME[uf]:name for uf,name in CAPITALS_BY_UF.items()}

def reconcile(tech, cities, models):
    # Os três recortes são independentes: nunca invento o modelo vendido em uma cidade.
    expected = pd.date_range("2024-01-01","2026-08-01",freq="MS")
    reference = None
    for frame,keys in ((tech,[]),(cities,["uf","municipio"]),(models,["marca","modelo"])):
        if frame.duplicated(["data_referencia","tecnologia"]+keys).any():
            raise ValueError("Chaves duplicadas na entrada.")
        if frame.emplacamentos.isna().any() or (frame.emplacamentos < 0).any() or (frame.emplacamentos % 1 != 0).any():
            raise ValueError("Contagens inválidas.")
        if not pd.DatetimeIndex(sorted(frame.data_referencia.unique())).equals(expected):
            raise ValueError("O protocolo exige 32 meses contínuos neste snapshot.")
        total = frame.groupby(["data_referencia","tecnologia"]).emplacamentos.sum().sort_index()
        if reference is None:
            reference = total
        elif not reference.equals(total):
            raise ValueError("Recortes municipais/modelos não conciliam por mês e tecnologia.")

def growth_table(frame, keys):
    selected = frame.loc[frame.data_referencia.dt.month.le(8)]
    pivot = selected.assign(ano=selected.data_referencia.dt.year).groupby(keys+["ano"]).emplacamentos.sum().unstack("ano")
    # Zero só significa nenhum registro no recorte completo conciliado, não fonte ausente.
    pivot = pivot.reindex(columns=[2024,2025,2026]).fillna(0)
    pivot.columns = ["jan_ago_2024","jan_ago_2025","jan_ago_2026"]
    pivot["acrescimo_2026_2025"] = pivot.jan_ago_2026-pivot.jan_ago_2025
    pivot["crescimento_percentual"] = np.where(pivot.jan_ago_2025.gt(0),100*pivot.acrescimo_2026_2025/pivot.jan_ago_2025,np.nan)
    total = pivot.acrescimo_2026_2025.sum()
    pivot["contribuicao_crescimento_percentual"] = 100*pivot.acrescimo_2026_2025/total if total else np.nan
    return pivot.reset_index().sort_values("acrescimo_2026_2025",ascending=False)

def partial_association(city):
    # Parcial de Spearman: retiro efeitos lineares das posições de população e UF.
    columns = ["rendimento_domiciliar_per_capita_medio_2022_reais","veiculos_eletrificados_por_100_mil_habitantes","populacao_censo_2022"]
    valid = city.dropna(subset=columns+["uf_ibge"])
    ranks = valid[columns].rank().to_numpy()
    controls = np.column_stack([np.ones(len(valid)),ranks[:,2],pd.get_dummies(valid.uf_ibge,drop_first=True,dtype=float).to_numpy()])
    residual = ranks[:,:2]-controls @ np.linalg.lstsq(controls,ranks[:,:2],rcond=None)[0]
    coefficient = np.corrcoef(residual.T)[0,1]
    return dict(n_municipios=len(valid),coeficiente_parcial_spearman=float(coefficient),
                controles="posição da população Censo 2022 e efeitos fixos de UF",
                interpretacao="Associação condicional, não causalidade; indicadores 2022 e adoção ago/2026.")

def main():
    paths = [DATA/f"abve_publico_{name}_gold.csv" for name in ("tecnologia","municipio","modelo")]
    tech,cities,models = [pd.read_csv(path,parse_dates=["data_referencia"]) for path in paths]
    reconcile(tech,cities,models)
    cities = cities.loc[cities.tecnologia.isin(["BEV","PHEV"])].copy()
    cities["municipio_chave"] = cities.municipio.fillna("").map(norm)
    cities["regiao"] = cities.uf.map(REGION_BY_UF).fillna("UF não identificada")
    cities["localidade"] = np.where(cities.municipio_chave.eq(cities.uf.map(CAPITAL_BY_SIGLA)),"Capital","Interior")
    cities.loc[~cities.uf.isin(REGION_BY_UF) | cities.municipio_chave.isin(["SEM INFORMACAO", ""]),"localidade"] = "Não identificada"
    outputs = {"inteligencia_crescimento_estados":growth_table(cities,["uf"]),
               "inteligencia_crescimento_regioes":growth_table(cities,["regiao"]),
               "inteligencia_crescimento_municipios":growth_table(cities,["uf","municipio_chave"]),
               "inteligencia_capitais_interior":growth_table(cities,["localidade"])}
    plugin_models = models.loc[models.tecnologia.isin(["BEV","PHEV"])]
    outputs["inteligencia_contribuicao_marcas"] = growth_table(plugin_models,["marca"])
    concentration = []
    for year,group in plugin_models.loc[plugin_models.data_referencia.dt.month.le(8)].groupby(plugin_models.data_referencia.dt.year):
        counts = group.groupby("marca").emplacamentos.sum().sort_values(ascending=False)
        shares = counts/counts.sum()
        concentration.append(dict(ano=year,emplacamentos=int(counts.sum()),marcas_com_registros=len(counts),
                                  participacao_top3_percentual=100*shares.head(3).sum(),hhi_0_10000=10000*(shares**2).sum()))
    outputs["inteligencia_concentracao_marcas"] = pd.DataFrame(concentration)
    region = cities.loc[cities.data_referencia.between("2026-01-01","2026-08-01")].groupby("regiao").emplacamentos.sum()
    charges = pd.read_csv(DATA/"infraestrutura_recarga_abve_gold.csv")
    pressure = charges.loc[charges.nivel_geografico.eq("regiao"),["regiao","participacao_nacional_percentual","url_fonte"]].copy()
    pressure["emplacamentos_plugin_jan_ago_2026"] = pressure.regiao.map(region)
    pressure["participacao_emplacamentos_percentual"] = 100*pressure.emplacamentos_plugin_jan_ago_2026/region.sum()
    pressure["indice_participacao_vendas_recarga"] = pressure.participacao_emplacamentos_percentual/pressure.participacao_nacional_percentual
    recent = cities.loc[cities.data_referencia.between("2026-06-01","2026-08-01")].groupby("regiao").emplacamentos.sum()
    pressure["indice_jun_ago"] = 100*pressure.regiao.map(recent)/recent.sum()/pressure.participacao_nacional_percentual
    pressure["limite"] = "Fluxo de novos BEV/PHEV versus participação dos pontos públicos/semipúblicos; não mede frota por ponto, déficit ou utilização. Regiões com UF desconhecida permanecem no denominador de vendas."
    outputs["inteligencia_recarga_regional"] = pressure.sort_values("indice_participacao_vendas_recarga",ascending=False)
    local_points = charges.loc[charges.nivel_geografico.eq("municipio")].copy()
    local_points["municipio_chave"] = local_points.municipio.map(norm)
    local_points = local_points.merge(outputs["inteligencia_crescimento_municipios"],on=["uf","municipio_chave"],how="left",validate="one_to_one")
    if local_points.jan_ago_2026.isna().any():
        raise ValueError("Um município com recarga não encontrou correspondência nas vendas.")
    local_points["novos_registros_jan_ago_por_ponto"] = local_points.jan_ago_2026/local_points.pontos_total
    local_points["limite"] = "Somente 20 cidades publicadas; fluxo de 8 meses por ponto no fim do período, não ocupação ou veículos em circulação por ponto."
    outputs["inteligencia_recarga_cidades_top20"] = local_points.sort_values("novos_registros_jan_ago_por_ponto",ascending=False)
    municipality = identified_cities(pd.read_csv(DATA/"penetracao_municipal_ibge.csv"))
    municipality["municipio_chave"] = municipality.municipio.map(norm)
    peers = ["BAURU","MARILIA","RIBEIRAO PRETO","SAO JOSE DO RIO PRETO","SOROCABA","CAMPINAS"]
    local = cities.loc[cities.uf.eq("SP") & cities.municipio_chave.isin(peers)]
    outputs["estudo_bauru_mensal"] = local.groupby(["municipio_chave","data_referencia"]).emplacamentos.sum().reset_index()
    outputs["estudo_bauru_comparadores"] = outputs["inteligencia_crescimento_municipios"].query("uf == 'SP' and municipio_chave in @peers").merge(municipality.loc[municipality.uf_ibge.eq("SP"),["municipio_chave","populacao_censo_2022","quantidade_veiculos","veiculos_eletrificados_por_100_mil_habitantes","rendimento_domiciliar_per_capita_medio_2022_reais"]],on="municipio_chave",validate="one_to_one")
    outputs["estudo_bauru_comparadores"]["criterio"] = "Comparadores ilustrativos do interior paulista; não amostra pareada por renda/população."
    # Acrescento uma seleção objetiva de pares: distância em log-população e log-renda.
    candidates = municipality.loc[municipality.uf_ibge.eq("SP") & municipality.municipio_chave.ne("SAO PAULO")].dropna(subset=["populacao_censo_2022","rendimento_domiciliar_per_capita_medio_2022_reais"]).copy()
    dimensions = ["populacao_censo_2022","rendimento_domiciliar_per_capita_medio_2022_reais"]
    candidates = candidates.loc[candidates[dimensions].gt(0).all(axis=1)]
    base = candidates.loc[candidates.municipio_chave.eq("BAURU")].iloc[0]
    logged = np.log(candidates[dimensions])
    distance = (logged-np.log(base[dimensions].astype(float)))/logged.std()
    candidates["distancia_padronizada"] = np.sqrt((distance**2).sum(axis=1))
    matched = candidates.nsmallest(11,"distancia_padronizada")
    matched = matched.merge(outputs["inteligencia_crescimento_municipios"].query("uf == 'SP'").drop(columns="uf"),on="municipio_chave",how="left",validate="one_to_one")
    matched["criterio"] = "Bauru + dez cidades não capitais de SP mais próximas em log-população e log-renda padronizados; referência 2022, sem seleção pelo crescimento observado."
    outputs["estudo_bauru_pares_socioeconomicos"] = matched
    evidence_path = ROOT/"data/bronze/recarga_evidencias/evidencia_atual.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    outputs["recarga_nacional_evidencias"] = pd.DataFrame([evidence])
    prices = pd.read_csv(DATA/"precos_anunciados_evidencias.csv")
    # Mapeio apenas quatro nomes explícitos; não uso semelhança textual para inventar versões.
    mapping = {("KING","GL"):"BYD KING GL DM",("KING","GS"):"BYD KING GS DM",
               ("SONG PRO","GL"):"BYD SONG PRO GL DM",("SONG PRO","GS"):"BYD SONG PRO GS DM"}
    comparison_rows = []
    for (family,version),label in mapping.items():
        quote = prices.loc[prices.modelo_familia.eq(family) & prices.versao_declarada.eq(version)].iloc[0]
        sales = models.loc[models.marca.eq("BYD") & models.modelo.eq(label) & models.data_referencia.between("2024-08-01","2024-09-01")]
        if set(sales.data_referencia.dt.month) != {8,9}:
            raise ValueError(f"Preciso conferir os dois meses para {label}.")
        comparison_rows.append(dict(modelo_abve=label,modelo_familia=family,versao=version,
            preco_anunciado_reais=quote.preco_anunciado_reais,data_anuncio=quote.data_anuncio,
            condicao=quote.condicao,emplacamentos_ago_set_2024=int(sales.emplacamentos.sum()),
            url_preco=quote.url_fonte,url_emplacamentos="https://abve.org.br/abve-data/bi-geral/",
            limite="Comparação nacional descritiva de quatro versões de uma marca. Preço anunciado em jun/jul não comprova preço pago em ago/set; sem inferência de elasticidade ou efeito causal."))
    outputs["preco_vs_emplacamentos_estudo_2024"] = pd.DataFrame(comparison_rows)
    association = partial_association(municipality)
    outputs["inteligencia_associacao_controlada"] = pd.DataFrame([association])
    lineage_paths = paths+[DATA/"penetracao_municipal_ibge.csv",DATA/"infraestrutura_recarga_abve_gold.csv",DATA/"precos_anunciados_evidencias.csv",evidence_path]
    manifest = {"sha256_entradas":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in lineage_paths},
                "recorte":"jan/2024–ago/2026; comparações anuais janeiro–agosto; BEV+PHEV",
                "associacao_renda_controlada":association,
                "estudo_bauru":"Recarga em shoppings e solar residencial são hipóteses motivadas pelo relato do autor, não variáveis observadas.",
                "recarga_evidencia":evidence}
    out = ROOT/"output/analysis"
    out.mkdir(parents=True,exist_ok=True)
    (out/"inteligencia_manifesto.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    for name,frame in outputs.items():
        frame["escopo"] = "Emplacamentos BEV/PHEV ABVE; frota ampla SENATRAN ago/2026 e indicadores IBGE 2022, quando presentes, são medidas separadas. Recarga ABVE/Tupi ago/2026."
        frame.to_csv(DATA/f"{name}.csv",index=False,float_format="%.6f")
        print(f"{name}: {len(frame)} linhas")
    print(outputs["estudo_bauru_comparadores"].to_string(index=False))
    print(pressure[["regiao","indice_participacao_vendas_recarga","indice_jun_ago"]].to_string(index=False))

if __name__ == "__main__":
    main()
