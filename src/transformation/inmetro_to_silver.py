"""Extraio versões eletrificadas do PBEV sem inventar vendas ou autonomia real."""

import hashlib
import json
import re
import unicodedata
import pandas as pd
import pymupdf

from src.ingestion.download_inmetro_pbev import BRONZE, ROOT, FILES


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize(value):
    return unicodedata.normalize("NFKD", clean(value)).encode("ascii", "ignore").decode().upper()


def numeric(value):
    text = clean(value)
    if text in ("", "\\", "-", "ND", "N.A."):
        return None
    number = float(text.replace(",", "."))
    if not 0 < number < 10000:
        raise ValueError(f"Valor PBEV precisa de revisão: {text}")
    return number


def expand_merged_rows(row):
    """Separo linhas físicas fundidas, somente quando marca/modelo se repetem por linha."""
    brands = str(row[1] or "").splitlines()
    models = str(row[2] or "").splitlines()
    if len(brands) <= 1 or len(models) != len(brands) or len(set(brands)) != 1 or len(set(models)) != 1:
        return [row]
    count = len(brands)
    columns = [str(value or "").splitlines() or [""] for value in row]
    if any(len(values) not in (1, count) for values in columns):
        raise ValueError("Linhas fundidas ambíguas; preciso de revisão visual.")
    return [[values[index] if len(values) == count else values[0] for values in columns] for index in range(count)]


def parse_row(row, year, page, metadata):
    layout = {28: (23, 24), 33: (28, 29)}
    if normalize(row[1]) in ("MARCA", "") or normalize(row[2]) == "MODELO":
        return None  # Cabeçalhos repetidos e linhas de títulos não são veículos.
    propulsion = normalize(row[5])
    if "COMBUSTAO" in propulsion and ("HIBRIDO" in propulsion or "PLUG" in propulsion):
        raise ValueError("Propulsões sobrepostas na mesma célula; não interpreto como uma versão.")
    if "PLUG" in propulsion:
        technology = "PHEV_rotulo_inmetro"
    elif "HIBRIDO" in propulsion:
        technology = "HIBRIDO_rotulo_inmetro"
    elif propulsion == "ELETRICO":
        technology = "BEV_rotulo_inmetro"
    else:
        return None
    if len(row) not in layout:
        raise ValueError("Layout PBEV não revisado.")
    if not all(clean(row[i]) for i in (1, 2)):
        raise ValueError(f"Versão eletrificada sem marca/modelo: {row[:6]}.")
    consumption, autonomy = layout[len(row)]
    return dict(ano_ciclo=year, categoria=clean(row[0]), marca=clean(row[1]), modelo=clean(row[2]),
                versao=clean(row[3]) or None, motor=clean(row[4]), propulsao_original=clean(row[5]),
                tecnologia_rotulo=technology, combustivel_original=clean(row[9]),
                consumo_energetico_mj_km=numeric(row[consumption]), autonomia_eletrica_ensaio_km=numeric(row[autonomy]),
                pagina_pdf=page, url_fonte=metadata["url_fonte"], sha256_pdf=metadata["sha256"],
                data_captura=metadata["data_captura"], unidade_autonomia="km_ensaio_padronizado",
                limite_uso="catalogo_de_versoes_nao_vendas_nem_telemetria")


def main():
    rows = []
    quarantine = []
    for year in FILES:
        path = BRONZE / f"pbev_{year}.pdf"
        metadata = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
        if hashlib.sha256(path.read_bytes()).hexdigest() != metadata["sha256"]:
            raise ValueError("PDF alterado sem manifesto.")
        count = 0
        with pymupdf.open(path) as document:
            for pageno, page in enumerate(document, 1):
                for table in page.find_tables().tables:
                    if table.col_count < 20:
                        continue
                    if table.col_count not in (28, 33):
                        raise ValueError(f"Layout não revisado: {year}, página {pageno}, {table.col_count} colunas.")
                    physical_rows = [r for row in table.extract() for r in expand_merged_rows(row)]
                    for row in physical_rows:
                        try:
                            parsed = parse_row(row, year, pageno, metadata)
                        except ValueError as error:
                            quarantine.append(dict(ano_ciclo=year, pagina_pdf=pageno, linha_bruta=json.dumps(row, ensure_ascii=False),
                                                   motivo=str(error), sha256_pdf=metadata["sha256"], url_fonte=metadata["url_fonte"]))
                            continue  # Preservo o erro em relatório; não corrijo conteúdo sobreposto por adivinhação.
                        if parsed:
                            rows.append(parsed)
                            count += 1
        if not count:
            raise ValueError(f"Nenhuma versão extraída em {year}.")
        print(f"PBEV {year}: {count} linhas de versões eletrificadas.")
    frame = pd.DataFrame(rows)
    if len(quarantine) > 5:
        raise ValueError("Mais de cinco linhas problemáticas: interrompo para revisar o extrator.")
    frame["status_cobertura_ciclo"] = frame.ano_ciclo.map({year: "parcial_com_quarentena" if any(r["ano_ciclo"] == year for r in quarantine)
                                                          else "linhas_extraidas_sem_erro_detectado" for year in FILES})
    # Alguns catálogos repetem versões em categorias distintas. Não elimino sem examinar.
    frame["id_registro"] = [hashlib.sha256(json.dumps([r.ano_ciclo, r.pagina_pdf, r.categoria, r.marca, r.modelo, r.versao, i]).encode()).hexdigest() for i, r in enumerate(frame.itertuples())]
    (ROOT / "data/silver/inmetro").mkdir(parents=True, exist_ok=True)
    frame.to_parquet(ROOT / "data/silver/inmetro/pbev_eletrificados.parquet", index=False)
    frame.to_csv(ROOT / "data/portfolio/inmetro_versoes_eletrificadas.csv", index=False)
    pd.DataFrame(quarantine, columns=["ano_ciclo", "pagina_pdf", "linha_bruta", "motivo", "sha256_pdf", "url_fonte"]).to_csv(ROOT / "data/portfolio/inmetro_quarentena.csv", index=False)
    print(f"Inmetro: {len(frame)} linhas publicadas e {len(quarantine)} linhas em quarentena.")


if __name__ == "__main__":
    main()
