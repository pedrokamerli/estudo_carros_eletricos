"""Inicio um histórico documental de preços anunciados, sem confundi-los com FIPE."""
import hashlib
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://www.byd.com/br/noticias-byd-brasil/"
# Registro versão e condição comercial de cada anúncio, não o preço pago pelo comprador.
SOURCES = [
    ("DOLPHIN MINI","BEV","4 lugares","preco_publico_lancamento","2024-02-26","BYD-Dolphin-Mini-chega-para-revolucionar-o-mercado-de-carros-no-Brasil",[("4 lugares",r"preço público \(PPS\).*?R[＄$]\s*([\d.,]+)")]),
    ("DOLPHIN MINI","BEV","5 lugares","preco_publicado_lancamento","2024-07-20","chega-ao-Brasil-o-BYD-Dolphin-Mini-de-5-lugares",[("5 lugares",r"preço competitivo, de R\$\s*([\d.,]+)")]),
    ("KING","PHEV","GL/GS","preco_publico_lancamento","2024-06-18","chega-ao-brasil-o-byd-king-o-sedan-plugin-feito-para-reinar.html",[("GL",r"preço público \(PPS\).*?R\$\s*([\d.,]+) na versão GL"),("GS",r"versão GL e de R\$\s*([\d.,]+) na versão GS")]),
    ("SONG PRO","PHEV","GL/GS","promocao_primeiras_3000_unidades","2024-07-10","a-familia-cresceu-BYD-Song-Pro-chega-ao-Brasil",[("GL",r"valor de R\$\s*([\d.,]+) na versão GL"),("GS",r"versão GL e de R\$\s*([\d.,]+) na versão GS")]),
]

def parse_price(value):
    return float(value.rstrip(".,").replace(".", "").replace(",", "."))

def main():
    rows = []
    directory = ROOT/"data/bronze/precos_publicados"
    directory.mkdir(parents=True,exist_ok=True)
    for model,technology,versions,condition,date,slug,patterns in SOURCES:
        url = BASE+slug
        response = requests.get(url,timeout=40)
        response.raise_for_status()
        digest = hashlib.sha256(response.content).hexdigest()
        (directory/f"{digest}.html").write_bytes(response.content)
        text = re.sub(r"\s+"," ",unescape(re.sub(r"<[^>]+>"," ",response.text)))
        for version,pattern in patterns:
            match = re.search(pattern,text,re.I)
            if not match:
                raise ValueError(f"Anúncio mudou: preciso revisar {model} {version}.")
            price = parse_price(match[1])
            if price <= 0:
                raise ValueError("Preço inválido.")
            rows.append(dict(marca="BYD",modelo_familia=model,versao_declarada=version,tecnologia=technology,
                             preco_anunciado_reais=price,data_anuncio=date,condicao=condition,
                             url_fonte=url,sha256_html=digest,data_captura=datetime.now(timezone.utc).isoformat(),
                             limite="Amostra documental de uma marca em 2024, não painel mensal de preços, preço atual, transação ou FIPE. Sem associação automática a versões ABVE/Inmetro."))
    pd.DataFrame(rows).to_csv(ROOT/"data/portfolio/precos_anunciados_evidencias.csv",index=False)
    print(f"Preços de anúncios primários: {len(rows)} observações; sem interpolação mensal.")

if __name__ == "__main__":
    main()
