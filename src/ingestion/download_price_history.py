"""Amplio os anúncios oficiais sem fabricar uma série mensal de preços."""
import hashlib
import re
from datetime import datetime, timezone
from html import unescape
import pandas as pd
import requests
import fitz
from src.ingestion.download_price_evidence import ROOT, parse_price

BYD_URL = "https://www.byd.com/br/noticias-byd-brasil/byd-lanca-dolphin-mini-azul-e-song-pro-com-adas-completo"
GWM_URL = "https://www.gwmmotors.com.br/pt/media-center/news/2025/gwm-lanca-edicao-limitada-do-ora-03-com-autonomia-de-ate-420-km-e-itens-exclusivos"
GWM_APRIL_URL = "https://www.gwmmotors.com.br/pt/media-center/news/2025/gwm-brasil-apresenta-linha-2026-do-ora-03-com-nova-identidade-visual-e-mais-tecnologia"
MERCEDES_URL = "https://imprensa.mercedes-benz.com.br/storage/files/90C3pndHyyP2sBABMJriW4IVeAHASelLi59pUAMO.pdf"


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

def extract_gwm_april(html):
    text = plain(html)
    if "28 de abril de 2025" not in text or "ORA 03 Skin BEV48" not in text:
        raise ValueError("Anúncio GWM de abril mudou.")
    matches = [("Skin BEV48",re.search(r"ORA 03 Skin BEV48 passa a custar R\$\s*([\d.,]+)",text,re.I)),
               ("GT BEV63",re.search(r"GT BEV63,?\s*R\$\s*([\d.,]+)",text,re.I))]
    if any(match is None for _,match in matches):
        raise ValueError("Preços GWM de abril não encontrados.")
    return [dict(marca="GWM",modelo_versao="ORA 03 "+name,ano_modelo="linha 2026",preco_anunciado_reais=parse_price(match[1]),data_anuncio="2025-04-28",condicao="preco_publicado_linha_2026") for name,match in matches]


def extract_mercedes(pdf_bytes):
    """Extraio apenas as linhas classificadas como elétricas na tabela oficial."""
    text = "\n".join(page.get_text() for page in fitz.open(stream=pdf_bytes, filetype="pdf"))
    matches = re.findall(r"(?m)^(.+?)\n(20\d\d)\n([\d.]+)\nEl.trico", text)
    if len(matches) != 8:
        raise ValueError(f"Tabela Mercedes mudou: esperava 8 modelos elétricos, encontrei {len(matches)}.")
    return [dict(marca="Mercedes-Benz", modelo_versao=model.strip(), ano_modelo=year,
                 preco_anunciado_reais=parse_price(price), data_anuncio="2024-02-01",
                 condicao="preco_publico_a_partir_tabela_fev_2024") for model, year, price in matches]


def main():
    rows = []
    directory = ROOT/"data/bronze/precos_publicados"
    directory.mkdir(parents=True,exist_ok=True)
    for url,extractor in ((BYD_URL,extract_byd),(GWM_URL,extract_gwm),(GWM_APRIL_URL,extract_gwm_april)):
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
    response = requests.get(MERCEDES_URL, timeout=40)
    response.raise_for_status()
    digest = hashlib.sha256(response.content).hexdigest()
    parsed = extract_mercedes(response.content)
    (directory/f"{digest}.pdf").write_bytes(response.content)
    for row in parsed:
        row.update(url_fonte=MERCEDES_URL, sha256_html=digest, data_captura=datetime.now(timezone.utc).isoformat(),
                   limite="Preço público a partir de tabela histórica Mercedes-Benz; não é preço atual, transação, FIPE ou série mensal.")
    rows.extend(parsed)
    old = pd.read_csv(ROOT/"data/portfolio/precos_anunciados_evidencias.csv")
    old["modelo_versao"] = old.modelo_familia+" "+old.versao_declarada
    old["ano_modelo"] = None
    frame = pd.concat([old,pd.DataFrame(rows)],ignore_index=True)
    frame.to_csv(ROOT/"data/portfolio/precos_historicos_documentais.csv",index=False)
    print(f"Histórico documental: {len(frame)} anúncios, {frame.marca.nunique()} marcas; sem preenchimento mensal.")


if __name__ == "__main__":
    main()
