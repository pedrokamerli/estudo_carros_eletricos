"""Coleto diretórios comunitários de Bauru como evidência de recarga, sem tratá-los como censo."""
import hashlib
import re
from datetime import datetime, timezone
from html import unescape
import pandas as pd
import requests
from src.ingestion.download_price_evidence import ROOT

SOURCES={"seguee":"https://seguee.com.br/recarga/sp/bauru","carregados_bauru_shopping":"https://carregados.com.br/estacoes/estacao-bauru-shopping-3632","mapavolt_bauru_shopping":"https://mapavolt.com.br/eletropostos/mapavolt-bauru-shopping-bauru-sp"}

def text(html): return re.sub(r"\s+"," ",unescape(re.sub(r"<[^>]+>"," ",html))).strip()
def fetch(url):
    response=requests.get(url,headers={"User-Agent":"Pedro-EV-Portfolio/1.0"},timeout=40); response.raise_for_status(); return response.content,text(response.text)
def extract(source, html):
    if source=="seguee":
        total=re.search(r"tem (\d+) estações de recarga.*?(\d+) com carga rápida",html,re.I); prices=re.search(r"Preço entre R\$ ([\d,]+) e R\$ ([\d,]+) por kWh.*?(\d+) estações",html,re.I)
        if not total or not prices: raise ValueError("Resumo Seguee mudou.")
        return {"fonte":"Seguee","escopo":"diretorio_comunitario","estacoes_reportadas":int(total[1]),"dc_reportadas":int(total[2]),"potencia_kw":None,"preco_min_reais_kwh":float(prices[1].replace(',','.')),"preco_max_reais_kwh":float(prices[2].replace(',','.')),"status_reportado":"não informado por estação no resumo","confianca":None,"limite":"Cobertura e funcionamento dependem do diretório; não é censo nem prova de disponibilidade."}
    if source.startswith("carregados"):
        match=re.search(r"Confiança\s+(\d+)\s*%.*?Potência Média\s+(\d+)\s*kW\s+Informada:\s+(\d+)\s*kW\s*–\s*(\d+)\s*kW.*?(\d+) estações",html,re.I)
        if not match: raise ValueError("Página Carregados mudou.")
        return {"fonte":"Carregados","escopo":"estacao_bauru_shopping","estacoes_reportadas":int(match[5]),"dc_reportadas":None,"potencia_kw":int(match[2]),"preco_min_reais_kwh":None,"preco_max_reais_kwh":None,"status_reportado":"Funcionando (status comunitário)","confianca":int(match[1]),"limite":"Status comunitário baseado em check-ins; não é monitoramento operacional."}
    power=re.search(r"Potência\s+([0-9]+) kW",html,re.I); confidence=re.search(r"([0-9]+)\s+indice de confian",html,re.I)
    if not power or not confidence: raise ValueError("Página MapaVolt mudou.")
    return {"fonte":"MapaVolt","escopo":"estacao_bauru_shopping","estacoes_reportadas":None,"dc_reportadas":None,"potencia_kw":int(power[1]),"preco_min_reais_kwh":None,"preco_max_reais_kwh":None,"status_reportado":"Revisar","confianca":int(confidence[1]),"limite":"Registro público com confirmação pendente; não contar junto de outros diretórios como local distinto sem deduplicação."}
def main():
    rows=[]; bronze=ROOT/"data/bronze/bauru_recarga_diretorios"; bronze.mkdir(parents=True,exist_ok=True)
    for source,url in SOURCES.items():
        content,clean=fetch(url); digest=hashlib.sha256(content).hexdigest(); (bronze/f"{source}_{digest}.html").write_bytes(content)
        row=extract(source,clean); row.update(url_fonte=url,sha256_html=digest,data_captura=datetime.now(timezone.utc).isoformat(),cidade="Bauru",uf="SP"); rows.append(row)
    pd.DataFrame(rows).to_csv(ROOT/"data/portfolio/bauru_recarga_evidencias.csv",index=False); print(f"Diretórios de Bauru: {len(rows)} fontes; não deduplico nem chamo de censo.")
if __name__=="__main__": main()
