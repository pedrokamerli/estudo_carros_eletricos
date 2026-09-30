"""Aqui valido a qualidade da fonte Bronze de marcas e modelos da SENATRAN."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# Estas são as colunas que a análise de marcas e modelos precisa encontrar no TXT.
REQUIRED_COLUMNS = {
    "UF",
    "Município",
    "Marca Modelo",
    "Ano Fabricação Veículo CRV",
    "Qtd. Veículos",
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "senatran"
    / "marca_modelo_2025_12"
    / "I_Frota_por_UF_Municipio_Marca_e_Modelo_Ano_Dezembro_2025.TXT"
)
REPORT_PATH = (
    PROJECT_ROOT
    / "data"
    / "quality"
    / "senatran"
    / "brand_model_quality_report_2025_12.json"
)


def validate_columns(columns: list[str]) -> None:
    """Confirmo se o TXT possui a estrutura mínima esperada."""
    # Comparo a estrutura publicada pela SENATRAN com a estrutura que preciso processar.
    missing_columns = sorted(REQUIRED_COLUMNS.difference(columns))
    if missing_columns:
        raise ValueError(
            "Arquivo de marca e modelo sem colunas obrigatórias: "
            + ", ".join(missing_columns)
        )


def assess_brand_model_file(source_path: Path = SOURCE_PATH) -> dict[str, object]:
    """Leio o TXT em partes para validar um arquivo grande sem estourar a memória."""
    if not source_path.exists():
        raise FileNotFoundError(f"Arquivo Bronze não encontrado: {source_path}")

    # Leio apenas o cabeçalho primeiro; assim descubro as colunas sem carregar os dados.
    header = pd.read_csv(source_path, sep=";", nrows=0, encoding="utf-8")
    validate_columns(header.columns.tolist())

    null_values = {column: 0 for column in sorted(REQUIRED_COLUMNS)}
    total_rows = 0
    invalid_quantity_rows = 0
    unknown_uf_rows = 0
    total_vehicles = 0.0

    # Processo 250 mil linhas por vez porque o arquivo inteiro tem mais de 1 GB.
    for chunk in pd.read_csv(
        source_path,
        sep=";",
        chunksize=250_000,
        dtype=str,
        encoding="utf-8",
    ):
        total_rows += len(chunk)

        # Somo nulos de cada parte para construir o resultado do arquivo inteiro.
        for column in null_values:
            null_values[column] += int(chunk[column].isna().sum())

        # Converto a quantidade para número; espaços e vírgulas não devem impedir a leitura.
        quantity = pd.to_numeric(
            chunk["Qtd. Veículos"].str.strip().str.replace(",", "."),
            errors="coerce",
        )
        invalid_quantity_rows += int(quantity.isna().sum() + quantity.le(0).sum())
        total_vehicles += float(quantity.dropna().sum())
        unknown_uf_rows += int(chunk["UF"].eq("Sem Informação").sum())

    critical_issues = sum(null_values.values()) + invalid_quantity_rows

    return {
        "total_linhas": total_rows,
        "valores_nulos": null_values,
        "linhas_com_quantidade_invalida": invalid_quantity_rows,
        "linhas_sem_uf": unknown_uf_rows,
        "total_veiculos": int(total_vehicles),
        "aprovado": critical_issues == 0,
    }


def save_quality_report(report: dict[str, object], report_path: Path = REPORT_PATH) -> None:
    """Salvo o relatório local para acompanhar a qualidade de cada fonte processada."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    # Executo a validação completa e guardo o resultado em JSON.
    report = assess_brand_model_file()
    save_quality_report(report)

    print("Qualidade da fonte de marcas e modelos:")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
