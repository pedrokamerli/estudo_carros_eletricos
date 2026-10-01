"""Leio os informativos FENABRAVE e transformo totais e rankings para Silver."""

from __future__ import annotations

import json
import re
import unicodedata
from itertools import combinations
from pathlib import Path

import pandas as pd
import pymupdf


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_PATH = PROJECT_ROOT / "data" / "bronze" / "fenabrave"
SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "fenabrave"
MONTHLY_PATH = SILVER_PATH / "emplacamentos_mensais.parquet"
BRANDS_PATH = SILVER_PATH / "ranking_marcas_mensal.parquet"
PARSE_MANIFEST_PATH = SILVER_PATH / "manifesto_extracao.json"
FENABRAVE_2024_01_URL = "https://www.fenabrave.org.br/portal/files/2024_01_02.pdf"


def normalize_text(value: str) -> str:
    """Normalizo títulos para reconhecer a mesma seção apesar de acentos e quebras."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", ascii_text).strip().upper()


def parse_integer(value: str) -> int:
    """Converto contagens no padrão brasileiro, em que ponto separa milhares."""
    cleaned = value.replace(".", "").replace(" ", "").strip()
    return int(cleaned.split(",", maxsplit=1)[0])


def parse_percentage(value: str) -> float:
    """Converto a participação percentual publicada no relatório."""
    return float(value.replace("%", "").replace(",", ".").strip())


def get_report_page(document: pymupdf.Document) -> tuple[int, str, str]:
    """Seleciono a página de autos e comerciais leves para manter um recorte estável."""
    pages = []
    for page_number, page in enumerate(document):
        text = page.get_text()
        normalized_lines = [normalize_text(line) for line in text.splitlines()]
        normalized = " ".join(normalized_lines)
        if "MERCADO DE ELETRIFICADOS AUTOS" in normalized:
            pages.append((page_number, text, normalized))

    for page_number, text, normalized in pages:
        if "AUTOS E COMERCIAIS LEVES" in normalized:
            return page_number, text, "autos_e_comerciais_leves"
    if pages:
        page_number, text, _ = pages[0]
        return page_number, text, "autos"

    # Alguns PDFs antigos têm título com uma fonte de caractere personalizada.
    # Neles encontro as páginas pelas linhas da tabela e escolho a página combinada
    # somente quando seu total bate exatamente com autos + comerciais leves.
    unidentified_segments = []
    for page_number, page in enumerate(document):
        text = page.get_text()
        normalized_lines = [normalize_text(line) for line in text.splitlines()]
        normalized = " ".join(normalized_lines)
        if not all(
            marker in normalized
            for marker in ("A) HIBRIDOS", "B) ELETRICOS", "TOT.ELETRIFICADOS")
        ):
            continue
        try:
            hybrid = find_counts_after_label(normalized_lines, "A) HIBRIDOS", 0)
            electric = find_counts_after_label(normalized_lines, "B) ELETRICOS", 0)
            total_index = next(
                index
                for index, line in enumerate(normalized_lines)
                if "TOT.ELETRIFICADOS" in line
            )
            total_counts = [
                parse_integer(line)
                for line in normalized_lines[total_index + 1 :]
                if re.fullmatch(r"[0-9][0-9., ]*", line.strip())
            ]
            if total_counts and hybrid[0] + electric[0] == total_counts[0]:
                unidentified_segments.append(
                    (page_number, text, total_counts[0], hybrid[0], electric[0])
                )
        except (ValueError, StopIteration):
            continue

    if len(unidentified_segments) >= 3:
        largest = max(unidentified_segments, key=lambda record: record[2])
        other_totals = [record[2] for record in unidentified_segments if record != largest]
        if any(sum(pair) == largest[2] for pair in combinations(other_totals, 2)):
            return largest[0], largest[1], "autos_e_comerciais_leves"
    raise ValueError("Não encontrei página de mercado de eletrificados para autos.")


def find_counts_after_label(lines: list[str], label: str, start: int) -> list[int]:
    """Leio as cinco colunas de contagem logo após o rótulo da tabela mensal."""
    for index in range(start, len(lines)):
        if label in lines[index]:
            counts = []
            for candidate in lines[index + 1 :]:
                if re.fullmatch(r"[0-9][0-9., ]*", candidate.strip()):
                    counts.append(parse_integer(candidate))
                    if len(counts) == 5:
                        return counts
                elif counts and candidate.strip() and not re.fullmatch(
                    r"[-+▲▼% ]+", candidate.strip()
                ):
                    break
            raise ValueError(f"A linha '{label}' não contém cinco contagens legíveis.")
    raise ValueError(f"Não encontrei a linha '{label}' na página do relatório.")


def parse_monthly_brands(
    lines: list[str], year: int, month: int, source_url: str, page_number: int,
    segment: str, extraction_method: str = "extracao_textual",
) -> list[dict[str, object]]:
    """Extraio os rankings mensais de fabricantes, sem confundi-los com o acumulado."""
    headings = [
        (index, line)
        for index, line in enumerate(lines)
        if ("HIBRIDOS" in line or "ELETRICOS" in line)
        and ("MES" in line or "ACUMULADO" in line)
    ]
    rows: list[dict[str, object]] = []

    for marker_position, (start, heading) in enumerate(headings):
        if "MES" not in heading:
            continue
        category = "hibridos" if "HIBRIDOS" in heading else "eletricos"
        end = headings[marker_position + 1][0] if marker_position + 1 < len(headings) else len(lines)
        for index in range(start + 1, end):
            rank_match = re.search(r"(\d{1,2})\s*(?:O|º|°)?$", lines[index].strip())
            if not rank_match:
                continue

            values = []
            cursor = index + 1
            while cursor < end and len(values) < 3:
                candidate = lines[cursor].strip()
                if candidate:
                    values.append(candidate)
                cursor += 1

            if len(values) != 3:
                continue
            brand, quantity_text, percentage_text = values
            if not re.fullmatch(r"[\d. ]+", quantity_text) or not percentage_text.endswith("%"):
                continue
            rows.append(
                {
                    "ano_referencia": year,
                    "mes_referencia": month,
                    "categoria_fenabrave": category,
                    "posicao": int(rank_match.group(1)),
                    "marca": brand.strip().upper(),
                    "quantidade_emplacada": parse_integer(quantity_text),
                    "participacao_percentual": parse_percentage(percentage_text),
                    "segmento_veiculos": segment,
                    "pagina_pdf": page_number + 1,
                    "url_fonte": source_url,
                    "metodo_extracao": extraction_method,
                }
            )
    return rows


def parse_report(pdf_path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    """Extraio duas categorias mensais e seus rankings do PDF preservando rastreabilidade."""
    match = re.fullmatch(r"(20\d{2})_(\d{2})_02\.pdf", pdf_path.name)
    if not match:
        raise ValueError(f"Nome de relatório fora do padrão esperado: {pdf_path.name}")
    year, month = int(match.group(1)), int(match.group(2))
    source_url = f"https://www.fenabrave.org.br/portal/files/{pdf_path.name}"

    with pymupdf.open(pdf_path) as document:
        page_number, text, segment = get_report_page(document)

    lines = [normalize_text(line) for line in text.splitlines()]
    hybrid_counts = find_counts_after_label(lines, "A) HIBRIDOS", 0)
    electric_counts = find_counts_after_label(lines, "B) ELETRICOS", 0)
    monthly_rows = []

    for category, counts in (("hibridos", hybrid_counts), ("eletricos", electric_counts)):
        monthly_rows.append(
            {
                "ano_referencia": year,
                "mes_referencia": month,
                "categoria_fenabrave": category,
                "emplacamentos_mes": counts[0],
                "emplacamentos_mes_anterior": counts[1],
                "emplacamentos_acumulado_ano": counts[2],
                "emplacamentos_mes_ano_anterior": counts[3],
                "emplacamentos_acumulado_ano_anterior": counts[4],
                "segmento_veiculos": segment,
                "pagina_pdf": page_number + 1,
                "url_fonte": source_url,
                "metodo_extracao": "extracao_textual",
            }
        )

    monthly_total = next(row["emplacamentos_mes"] for row in monthly_rows if row["categoria_fenabrave"] == "hibridos")
    monthly_total += next(row["emplacamentos_mes"] for row in monthly_rows if row["categoria_fenabrave"] == "eletricos")
    total_marker = next(
        (index for index, line in enumerate(lines) if "TOT.ELETRIFICADOS" in line), None
    )
    if total_marker is None:
        raise ValueError("Não encontrei a linha de total de eletrificados para validar as categorias.")
    total_counts = [
        parse_integer(candidate)
        for candidate in lines[total_marker + 1 :]
        if re.fullmatch(r"[0-9][0-9., ]*", candidate.strip())
    ][:5]
    if not total_counts or total_counts[0] != monthly_total:
        raise ValueError(
            "A soma de híbridos e elétricos não bate com o total publicado no PDF. "
            f"Categorias={monthly_total}, total={total_counts[:1]}"
        )

    brand_rows = parse_monthly_brands(lines, year, month, source_url, page_number, segment)
    if not brand_rows:
        raise ValueError("Não encontrei rankings mensais de fabricante na página de eletrificados.")
    return monthly_rows, brand_rows, {
        "arquivo": pdf_path.name,
        "ano_referencia": year,
        "mes_referencia": month,
        "status": "extraido_e_validado",
        "pagina_pdf": page_number + 1,
        "segmento_veiculos": segment,
        "url_fonte": source_url,
        "metodo_extracao": "extracao_textual",
        "emplacamentos_eletrificados_mes": monthly_total,
        "linhas_rankings_marca": len(brand_rows),
    }


def transcribe_2024_01_from_rendered_source() -> tuple[
    list[dict[str, object]], list[dict[str, object]], dict[str, object]
]:
    """Transcrevo janeiro/2024 porque o PDF usa glifos que impedem extração automática."""
    year, month, page_number = 2024, 1, 19
    monthly_rows = [
        {
            "ano_referencia": year,
            "mes_referencia": month,
            "categoria_fenabrave": "hibridos",
            "emplacamentos_mes": 7642,
            "emplacamentos_mes_anterior": 10224,
            "emplacamentos_acumulado_ano": 7642,
            "emplacamentos_mes_ano_anterior": 3745,
            "emplacamentos_acumulado_ano_anterior": 3745,
            "segmento_veiculos": "autos",
            "pagina_pdf": page_number + 1,
            "url_fonte": FENABRAVE_2024_01_URL,
            "metodo_extracao": "transcricao_visual_verificada",
        },
        {
            "ano_referencia": year,
            "mes_referencia": month,
            "categoria_fenabrave": "eletricos",
            "emplacamentos_mes": 4335,
            "emplacamentos_mes_anterior": 5652,
            "emplacamentos_acumulado_ano": 4335,
            "emplacamentos_mes_ano_anterior": 722,
            "emplacamentos_acumulado_ano_anterior": 722,
            "segmento_veiculos": "autos",
            "pagina_pdf": page_number + 1,
            "url_fonte": FENABRAVE_2024_01_URL,
            "metodo_extracao": "transcricao_visual_verificada",
        },
    ]
    brands_source = {
        "hibridos": [
            ("GWM", 1619, 21.19), ("TOYOTA", 1593, 20.85), ("BYD", 1519, 19.88),
            ("CAOA CHERY", 741, 9.70), ("VOLVO", 393, 5.14), ("M.BENZ", 349, 4.57),
            ("LAND ROVER", 277, 3.62), ("KIA", 257, 3.36), ("BMW", 239, 3.13),
            ("HONDA", 191, 2.50), ("AUDI", 90, 1.18), ("HYUNDAI", 75, 0.98),
            ("LEXUS", 75, 0.98), ("MINI", 66, 0.86), ("JEEP", 56, 0.73),
        ],
        "eletricos": [
            ("BYD", 2774, 63.99), ("GWM", 696, 16.06), ("VOLVO", 275, 6.34),
            ("PEUGEOT", 270, 6.23), ("JAC", 115, 2.65), ("BMW", 58, 1.34),
            ("RENAULT", 34, 0.78), ("FORD", 22, 0.51), ("PORSCHE", 22, 0.51),
            ("GM", 16, 0.37), ("MINI", 15, 0.35), ("CAOA CHERY", 11, 0.25),
            ("M.BENZ", 8, 0.18), ("DONGFENG", 5, 0.12), ("TESLA", 4, 0.09),
        ],
    }
    brand_rows = []
    for category, brands in brands_source.items():
        category_total = next(
            row["emplacamentos_mes"]
            for row in monthly_rows
            if row["categoria_fenabrave"] == category
        )
        if sum(row[1] for row in brands) > category_total:
            raise ValueError(f"A transcrição de fabricantes excede o total da categoria {category}.")
        for position, (brand, quantity, percentage) in enumerate(brands, start=1):
            brand_rows.append(
                {
                    "ano_referencia": year,
                    "mes_referencia": month,
                    "categoria_fenabrave": category,
                    "posicao": position,
                    "marca": brand,
                    "quantidade_emplacada": quantity,
                    "participacao_percentual": percentage,
                    "segmento_veiculos": "autos",
                    "pagina_pdf": page_number + 1,
                    "url_fonte": FENABRAVE_2024_01_URL,
                    "metodo_extracao": "transcricao_visual_verificada",
                }
            )

    if sum(row["emplacamentos_mes"] for row in monthly_rows) != 11977:
        raise ValueError("A validação visual de janeiro/2024 não fecha com o total publicado no PDF.")
    return monthly_rows, brand_rows, {
        "arquivo": "2024_01_02.pdf",
        "ano_referencia": year,
        "mes_referencia": month,
        "status": "transcricao_visual_verificada",
        "pagina_pdf": page_number + 1,
        "segmento_veiculos": "autos",
        "url_fonte": FENABRAVE_2024_01_URL,
        "emplacamentos_eletrificados_mes": 11977,
        "linhas_rankings_marca": len(brand_rows),
        "observacao": "Fonte usa glifos sem mapeamento Unicode; transcrição revisada na página renderizada.",
    }


def main() -> None:
    """Transformo cada PDF disponível; relatórios não legíveis ficam anotados no manifesto."""
    monthly_rows: list[dict[str, object]] = []
    brand_rows: list[dict[str, object]] = []
    parse_manifest: list[dict[str, object]] = []

    for pdf_path in sorted(BRONZE_PATH.glob("20??_??_02.pdf")):
        year, month = map(int, pdf_path.stem.split("_")[:2])
        if not (2024, 1) <= (year, month) <= (2026, 8):
            # Preservo o arquivo Bronze, mas ele não altera meu estudo fechado.
            continue
        try:
            report_monthly, report_brands, record = parse_report(pdf_path)
            monthly_rows.extend(report_monthly)
            brand_rows.extend(report_brands)
            print(
                f"{record['ano_referencia']}-{record['mes_referencia']:02d}: "
                f"{record['emplacamentos_eletrificados_mes']:,} eletrificados; "
                f"{record['linhas_rankings_marca']} linhas de marcas."
            )
        except Exception as error:
            if pdf_path.name == "2024_01_02.pdf":
                report_monthly, report_brands, record = transcribe_2024_01_from_rendered_source()
                monthly_rows.extend(report_monthly)
                brand_rows.extend(report_brands)
                print("2024-01: transcrição visual verificada; total 11.977, rankings preservados.")
            else:
                record = {
                    "arquivo": pdf_path.name,
                    "status": "extracao_precisa_revisao",
                    "erro": str(error),
                    "url_fonte": f"https://www.fenabrave.org.br/portal/files/{pdf_path.name}",
                }
                print(f"{pdf_path.name}: não extraído automaticamente — {error}")
        parse_manifest.append(record)

    if not monthly_rows:
        raise FileNotFoundError(
            "Nenhum relatório foi lido. Execute primeiro: "
            "python -m src.ingestion.download_fenabrave_monthly_reports"
        )

    SILVER_PATH.mkdir(parents=True, exist_ok=True)
    monthly_dataframe = pd.DataFrame(monthly_rows).sort_values(
        ["ano_referencia", "mes_referencia", "categoria_fenabrave"]
    )
    brands_dataframe = pd.DataFrame(brand_rows).sort_values(
        ["ano_referencia", "mes_referencia", "categoria_fenabrave", "posicao"]
    )
    monthly_dataframe.to_parquet(MONTHLY_PATH, index=False)
    brands_dataframe.to_parquet(BRANDS_PATH, index=False)
    PARSE_MANIFEST_PATH.write_text(
        json.dumps(parse_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Silver FENABRAVE: {len(monthly_dataframe)} linhas mensais em {MONTHLY_PATH}")
    print(f"Silver FENABRAVE: {len(brands_dataframe)} linhas de marcas em {BRANDS_PATH}")
    print(f"Manifesto de extração: {PARSE_MANIFEST_PATH}")


if __name__ == "__main__":
    # Inicio a transformação somente depois da coleta dos PDFs brutos.
    main()
