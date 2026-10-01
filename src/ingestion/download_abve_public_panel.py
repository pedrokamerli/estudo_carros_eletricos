"""Consulto apenas o painel publicado anonimamente pela ABVE, sem login."""

import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests

ROOT = Path(__file__).resolve().parents[2]
BRONZE = ROOT / "data/bronze/abve_public"
PAGE = "https://abve.org.br/abve-data/bi-geral/"


def fetch_metadata():
    page = requests.get(PAGE, timeout=40)
    page.raise_for_status()
    match = re.search(r'https://app\.powerbi\.com/view\?r=([^"\s<>]+)', page.text)
    if not match:
        raise ValueError("O painel público não está mais incorporado na página.")
    embed_url = match.group(0)
    descriptor = json.loads(base64.b64decode(match.group(1) + "=" * (-len(match.group(1)) % 4)))
    embed = requests.get(embed_url, timeout=40)
    embed.raise_for_status()
    cluster = re.search(r"var resolvedClusterUri = '([^']+)'", embed.text)
    if not cluster:
        raise ValueError("Não encontrei o endpoint anônimo utilizado pela página.")
    host = urlparse(cluster.group(1)).hostname
    if not host.endswith(".analysis.windows.net"):
        raise ValueError("Domínio do painel inesperado.")
    pieces = host.split(".")
    pieces[0] = pieces[0].replace("-redirect", "").replace("global-", "") + "-api"
    api = "https://" + ".".join(pieces)
    headers = {"X-PowerBI-ResourceKey": descriptor["k"], "Accept": "application/json"}
    url = api + f'/public/reports/{descriptor["k"]}/modelsAndExploration?preferReadOnlySession=true'
    response = requests.get(url, headers=headers, timeout=45)
    response.raise_for_status()
    metadata = response.json()
    return metadata, api, headers, embed_url


def main():
    metadata, api, headers, embed_url = fetch_metadata()
    BRONZE.mkdir(parents=True, exist_ok=True)
    envelope = {"pagina_fonte": PAGE, "embed_publico": embed_url, "api_publica": api,
                "data_captura": datetime.now(timezone.utc).isoformat(), "dados": metadata}
    serialized = json.dumps(envelope, ensure_ascii=False)
    digest = hashlib.sha256(serialized.encode()).hexdigest()
    (BRONZE / f"metadata_{digest}.json").write_text(serialized, encoding="utf-8")
    (BRONZE / "metadata_atual.json").write_text(serialized, encoding="utf-8")
    print(f"ABVE: metadados públicos capturados, {len(serialized)} caracteres.")


def query_public(metadata, api, headers, fields):
    """Peço somente agregados de campos já exibidos no painel público."""
    entities = list(dict.fromkeys(entity for entity, prop, kind in fields))
    aliases = {entity: f"s{i}" for i, entity in enumerate(entities)}
    select = [{kind: {"Expression": {"SourceRef": {"Source": aliases[entity]}}, "Property": prop},
               "Name": prop} for entity, prop, kind in fields]
    semantic = {"Version": 2, "From": [{"Name": aliases[e], "Entity": e, "Type": 0} for e in entities], "Select": select}
    command = {"SemanticQueryDataShapeCommand": {"Query": semantic, "Binding": {
        "Primary": {"Groupings": [{"Projections": list(range(len(fields)))}]},
        "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": 10000}}}, "Version": 1},
        "ExecutionMetricsKind": 1}}
    body = {"version": "1.0.0", "queries": [{"Query": {"Commands": [command]},
        "ApplicationContext": {"DatasetId": metadata["models"][0]["dbName"],
                               "Sources": [{"ReportId": metadata["exploration"]["reportId"]}]}}],
        "cancelQueries": [], "modelId": metadata["models"][0]["id"]}
    response = requests.post(api + "/public/reports/querydata?synchronous=true", headers=headers, json=body, timeout=60)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    main()
