"""Publico respostas rastreáveis às perguntas diretamente do motor, não da interface."""
import json
from pathlib import Path
import pandas as pd
from src.dashboard.story import identified_cities, comparable_years, percent_change, ranked_share
from src.dashboard.story import QUESTIONS

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/"data/portfolio"

def read(name):
    frame = pd.read_csv(DATA/f"{name}.csv")
    if "data_referencia" in frame:
        frame["data_referencia"] = pd.to_datetime(frame.data_referencia)
    elif {"ano_referencia","mes_referencia"}.issubset(frame.columns):
        frame["data_referencia"] = pd.to_datetime(dict(year=frame.ano_referencia,month=frame.mes_referencia,day=1))
    return frame

def main():
    sales = read("abve_publico_tecnologia_gold")
    periods = comparable_years(sales)
    state = read("evolucao_frota_por_estado")
    current = state.loc[state.data_referencia.eq(state.data_referencia.max()) & state.uf.ne("Sem Informação")]
    largest = current.nlargest(1,"total_veiculos_eletrificados").iloc[0]
    fastest = current.nlargest(1,"crescimento_percentual_anual").iloc[0]
    city = identified_cities(read("penetracao_municipal_ibge"))
    major = city.nlargest(1,"quantidade_veiculos").iloc[0]
    share = city.loc[city.frota_total_veiculos.ge(10000)].nlargest(1,"participacao_eletrificada_na_frota_percentual").iloc[0]
    models = read("abve_publico_modelo_gold")
    chosen = models.loc[models.ano_referencia.eq(2026) & models.tecnologia.isin(["BEV","PHEV"])]
    brand,model = ranked_share(chosen,["marca"]).iloc[0],ranked_share(chosen,["marca","modelo"]).iloc[0]
    interior = read("inteligencia_capitais_interior").query("localidade == 'Interior'").iloc[0]
    technology = []
    for t in ["BEV","PHEV","HEV","HEV FLEX"]:
        counts = comparable_years(sales.loc[sales.ano_referencia.ge(2025)],[t])
        technology.append((t,percent_change(counts.iloc[-1].Emplacamentos,counts.iloc[-2].Emplacamentos)))
    tech,rate = max(technology,key=lambda item:item[1])
    pressure = read("inteligencia_recarga_regional")
    areas = "; ".join(f"{r.regiao}: índice {r.indice_participacao_vendas_recarga:.2f}" for r in pressure.head(3).itertuples())
    bauru = read("estudo_bauru_comparadores").query("municipio_chave == 'BAURU'").iloc[0]
    ml = read("ml_desafio_selecao_modelos")
    evidence = json.loads((ROOT/"output/analysis/inteligencia_manifesto.json").read_text(encoding="utf-8"))
    n = read("oportunidade_municipal_preliminar").oportunidade_preliminar.astype(str).str.lower().isin(["t","true"]).sum()
    responses = [
      ("Observação",f"Jan–ago BEV/PHEV: {periods.iloc[0].Emplacamentos} (2024), {periods.iloc[1].Emplacamentos} (2025), {periods.iloc[2].Emplacamentos} (2026).","abve_publico_tecnologia_gold.csv","BEV/PHEV, veículos leves, meses iguais; não frota ou demanda não atendida."),
      ("Observação",f"2026/2025 jan–ago: {percent_change(periods.iloc[2].Emplacamentos,periods.iloc[1].Emplacamentos):.2f}%.","abve_publico_tecnologia_gold.csv","Ano parcial não equivale a crescimento do ano completo."),
      ("Observação",f"{largest.uf}: {largest.total_veiculos_eletrificados} veículos eletrificados em ago/2026.","evolucao_frota_por_estado.csv","Frota ampla, localização desconhecida fora do ranking."),
      ("Observação",f"{fastest.uf}: {fastest.crescimento_percentual_anual:.2f}% em 12 meses.","evolucao_frota_por_estado.csv","Taxas de bases pequenas não equivalem a maior contribuição absoluta."),
      ("Observação",f"{major.municipio}: {major.quantidade_veiculos} veículos.","penetracao_municipal_ibge.csv","Frota ampla em ago/2026; não emplacamentos."),
      ("Observação condicionada",f"{share.municipio}: {share.participacao_eletrificada_na_frota_percentual:.2f}%.","penetracao_municipal_ibge.csv","Cidades com pelo menos 10 mil veículos de frota total; todos os tipos veiculares."),
      ("Observação",f"Interior: crescimento de {interior.crescimento_percentual:.2f}% e contribuição de {interior.contribuicao_crescimento_percentual:.2f}% do acréscimo de BEV/PHEV.","inteligencia_capitais_interior.csv","Jan–ago/2026 vs 2025, registros por localidade, não migração de consumidores."),
      ("Observação",f"{brand.marca}: participação de {brand['Participação (%)']:.2f}% em jan–ago/2026; decomposição da contribuição disponível.","inteligencia_contribuicao_marcas.csv","BEV/PHEV, denominador todas as marcas; participação não prova poder de mercado."),
      ("Observação",f"{model.modelo}: {model.emplacamentos} emplacamentos em jan–ago/2026.","abve_publico_modelo_gold.csv","Recorte nacional; não sei quais modelos foram vendidos em cada município."),
      ("Observação",f"{tech}: maior taxa entre quatro tecnologias, {rate:.2f}%.","abve_publico_tecnologia_gold.csv","Jan–ago/2026 vs 2025, MHEV excluído, categorias originais."),
      ("Associação condicional",f"Renda e adoção: Spearman parcial {evidence['associacao_renda_controlada']['coeficiente_parcial_spearman']:.3f}, controlando posições de população e UF.","inteligencia_associacao_controlada.csv","Associação transversal, sem inferência causal ou intervalo; indicadores 2022, adoção 2026."),
      ("Triagem",f"{n} municípios no filtro econômico e de baixa adoção.","oportunidade_municipal_preliminar.csv","Regra exploratória sensível aos cortes; não probabilidade de compra."),
      ("Evidência de crescimento, futuro não comprovado",f"Bauru cresceu {bauru.crescimento_percentual:.2f}%, com {int(bauru.acrescimo_2026_2025)} registros adicionais. Comparei dez pares socioeconômicos sem selecioná-los pelo crescimento.","estudo_bauru_pares_socioeconomicos.csv","Crescimento passado não garante futuro; não modelo municipal prospectivamente validado."),
      ("Prioridade de investigação",f"{areas}. Priorizar estudo de capacidade e uso nessas regiões, pois sua participação nas novas vendas plug-in supera a da rede pública/semipública.","inteligencia_recarga_regional.csv","Índice = participação novos BEV/PHEV / participação pontos. Não mede déficit; faltam utilização, potência, recarga domiciliar e deslocamentos."),
      ("Experimento retrospectivo", "; ".join(f"{r.tecnologia}: {r.metodo}, WAPE {r.wape_teste_medio:.2f}% vs referência {r.wape_persistencia_teste:.2f}%" for r in ml.itertuples()),"ml_desafio_selecao_modelos.csv","Teste já conhecido; exige avaliação futura e intervalos próprios. Não aprovo previsões para anos ou cidades.")]
    rows = [dict(pergunta_id=i,pergunta=q,tipo_evidencia=s,resposta=a,arquivo_evidencia=f,limite=l,
                 corte_observado="2026-08",versao="motor_inteligencia_2026_10_01")
            for i,(q,(s,a,f,l)) in enumerate(zip(QUESTIONS,responses),1)]
    pd.DataFrame(rows).to_csv(DATA/"perguntas_evidencias_motor.csv",index=False)
    print("15 respostas produzidas com evidência e limite separados; sem alteração do dashboard.")

if __name__ == "__main__":
    main()
