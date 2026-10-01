"""Amplio os anúncios oficiais sem fabricar uma série mensal de preços."""
import hashlib
import re
from datetime import datetime, timezone
from html import unescape
import pandas as pd
import requests
from src.ingestion.download_price_evidence import ROOT, parse_price

BYD_URL = "https://www.byd.com/br/noticias-byd-brasil/byd-lanca-dolphin-mini-azul-e-song-pro-com-adas-completo"
GWM_URL = "https://www.gwmmotors.com.br/pt/media-center/news/2025/gwm-lanca-edicao-limitada-do-ora-03-com-autonomia-de-ate-420-km-e-itens-exclusivos"


def plain(html):
    return re.sub(r"\s+"," ",unescape(re.sub(r"<[^>]+>"," ",html)))


def extract_byd(html):
    text = plain(html)
    if "07/07/2025" not in text:
        raise ValueError("Data do anúncio BYD mudou; preciso revisar a fonte.")
    table = text.split("Confira a atual tabela sugerida completa da BYD:",1)[-1]
    matches = re.findall(r"(DOLPHIN MINI [45]L|DOLPHIN GS|DOLPHIN PLUS|YUAN PRO|YUAN PLUS|KING GL|KING GS|SONG PRO GL|SONG PRO GS|SONG PLUS PREMIUM|SONG PLUS|SEAL|TAN|HAN|SHARK)\s+(202[45]/202[56])\s+R\$\s*([\d.,]+)",table)
    if len(matches) != 20 or len(set((m,y) for m,y,_ in matches)) != 20:
        raise ValueError("Tabela BYD diferente das vinte linhas documentadas.")
    return [dict(marca="BYD",modelo_versao=m,ano_modelo=y,preco_anunciado_reais=parse_price(p),
                 data_anuncio="2025-07-07",condicao="tabela_sugerida_em_artigo_com_ofertas_julho") for m,y,p in matches]


def extract_gwm(html):
    text = plain(html)
    if not re.search(r"07 de agosto de 2025",text,re.I):
        raise ValueError("Data do anúncio GWM mudou.")
    matches = re.findall(r"ORA 03 (Skin BEV48|BEV58 \(edição limitada\)|GT BEV63):\s*R\$\s*([\d.,]+)",text)
    if len(matches) != 3:
        raise ValueError("Preços da linha ORA não encontrados integralmente.")
    # O artigo só explicita linha 2026 para BEV58; não atribuo esse ano às outras versões.
    return [dict(marca="GWM",modelo_versao="ORA 03 "+m,ano_modelo="linha 2026" if m.startswith("BEV58") else None,
                 preco_anunciado_reais=parse_price(p),data_anuncio="2025-08-07",
                 condicao="promocional_com_bonus_por_tempo_limitado") for m,p in matches]


def main():
    rows = []
    directory = ROOT/"data/bronze/precos_publicados"
    directory.mkdir(parents=True,exist_ok=True)
    for url,extractor in ((BYD_URL,extract_byd),(GWM_URL,extract_gwm)):
        response = requests.get(url,timeout=40)
        response.raise_for_status()
        digest = hashlib.sha256(response.content).hexdigest()
        parsed = extractor(response.text)
        if any(row["preco_anunciado_reais"] <= 0 for row in parsed):
            raise ValueError("Preço não positivo na fonte.")
        (directory/f"{digest}.html").write_bytes(response.content)
        for row in parsed:
            row.update(url_fonte=url,sha256_html=digest,data_captura=datetime.now(timezone.utc).isoformat(),
                limite="Preço anunciado em data histórica, não preço atual, transação ou FIPE. Amostra não representa o mercado inteiro; não interpolada nem usada como variável mensal do ML.")
        rows.extend(parsed)
    old = pd.read_csv(ROOT/"data/portfolio/precos_anunciados_evidencias.csv")
    old["modelo_versao"] = old.modelo_familia+" "+old.versao_declarada
    old["ano_modelo"] = None
    frame = pd.concat([old,pd.DataFrame(rows)],ignore_index=True)
    frame.to_csv(ROOT/"data/portfolio/precos_historicos_documentais.csv",index=False)
    print(f"Histórico documental: {len(frame)} anúncios, {frame.marca.nunique()} marcas; sem preenchimento mensal.")


if __name__ == "__main__":
    main()
