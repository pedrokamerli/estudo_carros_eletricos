"""Preservo os três ciclos oficiais PBEV, sem tratá-los como série mensal de vendas."""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
BRONZE = ROOT / "data/bronze/inmetro"
BASE = "https://www.gov.br/inmetro/pt-br/assuntos/regulamentacao/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica/veiculos-automotivos-pbe-veicular/"
FILES = {2024: "pbe-veicular-2024-1.pdf", 2025: "mascara-pbev-2025-mar-11.pdf", 2026: "mascara-pbev-2026_19_jan-rev01.pdf"}


def main():
    BRONZE.mkdir(parents=True, exist_ok=True)
    for year, filename in FILES.items():
        path = BRONZE / f"pbev_{year}.pdf"
        if path.exists():
            print(f"Inmetro {year}: reutilizando original local.")
            continue
        url = BASE + filename + "/@@download/file"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        if not response.content.startswith(b"%PDF"):
            raise ValueError("O portal não retornou PDF. Não salvo HTML como tabela.")
        path.write_bytes(response.content)
        path.with_suffix(".json").write_text(json.dumps({"ano_ciclo": year, "url_fonte": response.url,
            "data_captura": datetime.now(timezone.utc).isoformat(),
            "sha256": hashlib.sha256(response.content).hexdigest()}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Inmetro {year}: {len(response.content)} bytes.")


if __name__ == "__main__":
    main()
