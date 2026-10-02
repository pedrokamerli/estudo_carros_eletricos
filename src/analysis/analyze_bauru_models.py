"""Analiso modelos de Bauru e reconcilio o novo recorte com o agregado municipal."""
import pandas as pd
from src.ingestion.download_price_evidence import ROOT

DATA=ROOT/"data/portfolio"

def main():
    models=pd.read_csv(DATA/"abve_bauru_modelos.csv")
    models["data_referencia"]=pd.to_datetime(dict(year=models.ano_referencia,month=models.mes_referencia,day=1))
    plugin=models.loc[models.tecnologia.isin(["BEV","PHEV"]) & models.ano_referencia.ge(2024)].copy()
    if plugin.empty or plugin.emplacamentos.lt(0).any(): raise ValueError("Recorte Bauru inválido.")
    duplicate=plugin.duplicated(["ano_referencia","mes_referencia","marca","modelo","tecnologia"])
    if duplicate.any(): raise ValueError("Modelo duplicado no recorte Bauru.")
    monthly=plugin.groupby(["data_referencia","tecnologia"],as_index=False).emplacamentos.sum()
    monthly["cidade"]="Bauru"; monthly["escopo"]="ABVE modelo × município; BEV/PHEV; fluxo de emplacamentos"
    monthly.to_csv(DATA/"bauru_modelos_mensal.csv",index=False)
    ranking=plugin.groupby(["marca","modelo","tecnologia"],as_index=False).agg(emplacamentos=("emplacamentos","sum"),meses_com_dado=("data_referencia","nunique"))
    ranking["participacao_percentual"]=100*ranking.emplacamentos/ranking.emplacamentos.sum()
    ranking=ranking.sort_values("emplacamentos",ascending=False)
    ranking["limite"]="Ranking de emplacamentos ABVE para Bauru; não informa preço, comprador, local de recarga ou frota sobrevivente."
    ranking.to_csv(DATA/"bauru_modelos_ranking.csv",index=False)
    city=pd.read_csv(DATA/"abve_publico_municipio_gold.csv")
    city=city.loc[city.municipio.eq("Bauru") & city.tecnologia.isin(["BEV","PHEV"]) & city.ano_referencia.ge(2024)]
    a=plugin.groupby(["ano_referencia","mes_referencia","tecnologia"],as_index=False).emplacamentos.sum().rename(columns={"emplacamentos":"modelo_municipio"})
    b=city.groupby(["ano_referencia","mes_referencia","tecnologia"],as_index=False).emplacamentos.sum().rename(columns={"emplacamentos":"agregado_municipio"})
    recon=a.merge(b,on=["ano_referencia","mes_referencia","tecnologia"],how="outer").fillna(0); recon["diferenca"]=recon.modelo_municipio-recon.agregado_municipio
    if recon.diferenca.ne(0).any(): raise ValueError("Modelo e agregado municipal não reconciliam.")
    recon["limite"]="A reconciliação comprova consistência dos recortes ABVE desde 2024; não transforma a base em microdados individuais."
    recon.to_csv(DATA/"bauru_modelos_reconciliacao.csv",index=False)
    print(f"Bauru modelos: {len(plugin)} linhas; {ranking.modelo.nunique()} modelos; reconciliação sem diferenças.")

if __name__=="__main__": main()
