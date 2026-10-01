"""Extraio números nacionais de recarga da publicação primária, guardando a captura."""
import hashlib
import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
URL = "https://abve.org.br/recarga-rapida-dc-quase-triplica-em-12-meses-e-ja-responde-por-38-da-rede-brasileira/"

def extract(html):
    # Procuro rótulos específicos do artigo e paro se a estrutura publicada mudar.
    text = unescape(re.sub(r"<[^>]+>", " ", html))
    text = re.sub(r"\s+", " ", text)
    fields = {
        "pontos_total":r"Brasil conta com ([\d.]+) pontos públicos",
        "pontos_total_2025_08":r"agosto de 2025 \(([\d.]+)\)",
        "veiculos_plugin_acumulados_2022_2026_08":r"totaliza ([\d.]+) unidades",
        "bev_acumulados":r"49% \(([\d.]+) veículos\)",
        "phev_acumulados":r"51% \(([\d.]+) veículos\)",
        "pontos_ac":r"61,8% \(([\d.]+)\)",
        "pontos_dc":r"38,2% \(([\d.]+)\)",
        "pontos_dc_2025_08":r"de ([\d.]+) para 11\.397 pontos",
        "municipios_com_recarga_provisorio":r"identifica ([\d.]+) municípios com infraestrutura",
    }
    result = {}
    for key, pattern in fields.items():
        match = re.search(pattern,text)
        if not match:
            raise ValueError(f"A publicação mudou: preciso revisar o campo {key}.")
        result[key] = int(match[1].replace(".", ""))
    if result["pontos_ac"]+result["pontos_dc"] != result["pontos_total"]:
        raise ValueError("AC + DC não conciliam com o total.")
    if result["bev_acumulados"]+result["phev_acumulados"] != result["veiculos_plugin_acumulados_2022_2026_08"]:
        raise ValueError("BEV + PHEV não conciliam com a estimativa publicada.")
    return result

def main():
    response = requests.get(URL,timeout=40)
    response.raise_for_status()
    values = extract(response.text)
    digest = hashlib.sha256(response.content).hexdigest()
    directory = ROOT/"data/bronze/recarga_evidencias"
    directory.mkdir(parents=True,exist_ok=True)
    (directory/f"abve_{digest}.html").write_bytes(response.content)
    values.update(url_fonte=URL,data_referencia="2026-08-31",data_publicacao="2026-09-28",
                  data_captura=datetime.now(timezone.utc).isoformat(),sha256_html=digest,
                  limite="Frota plug-in publicada é contabilização acumulada desde 2022, não estoque RENAVAM nem utilização dos carregadores.")
    (directory/"evidencia_atual.json").write_text(json.dumps(values,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(values,ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
