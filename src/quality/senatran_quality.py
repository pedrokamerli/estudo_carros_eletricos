"""Aqui valido a qualidade do arquivo Bronze da SENATRAN."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# Estas são as colunas mínimas que preciso para continuar a transformação.
REQUIRED_COLUMNS = {"UF", "Município", "Combustível Veículo", "Qtd. Veículos"}


def assess_bronze_dataframe(dataframe: pd.DataFrame) -> dict[str, object]:
    """Avalio o DataFrame Bronze e retorno um relatório simples de qualidade."""
    # Se a fonte mudou de estrutura, interrompo a execução para não produzir uma Silver incorreta.
    missing_columns = sorted(REQUIRED_COLUMNS.difference(dataframe.columns))
    if missing_columns:
        columns_text = ", ".join(missing_columns)
        raise ValueError(f"Arquivo SENATRAN sem colunas obrigatórias: {columns_text}")

    # Conto valores ausentes apenas nas colunas essenciais para este projeto.
    null_values = {
        column: int(dataframe[column].isna().sum())
        for column in sorted(REQUIRED_COLUMNS)
    }

    # Procuro quantidades nulas, não numéricas ou menores/iguais a zero.
    vehicle_quantity = pd.to_numeric(
        dataframe["Qtd. Veículos"],
        errors="coerce",
    )
    invalid_quantity_rows = int(vehicle_quantity.isna().sum() + vehicle_quantity.le(0).sum())

    # Registro a ausência de UF como alerta; ela não invalida o dado nacional.
    unknown_uf_rows = int(dataframe["UF"].eq("Sem Informação").sum())
    unknown_uf_vehicles = int(
        dataframe.loc[
            dataframe["UF"].eq("Sem Informação"),
            "Qtd. Veículos",
        ].sum()
    )

    critical_issues = sum(null_values.values()) + invalid_quantity_rows

    return {
        "total_linhas": int(len(dataframe)),
        "valores_nulos": null_values,
        "linhas_com_quantidade_invalida": invalid_quantity_rows,
        "linhas_sem_uf": unknown_uf_rows,
        "veiculos_sem_uf": unknown_uf_vehicles,
        "aprovado": critical_issues == 0,
    }


def save_quality_report(report: dict[str, object], report_path: Path) -> None:
    """Salvo o relatório em JSON para consultar o resultado da execução depois."""
    # Crio a pasta de relatórios se ela ainda não existir.
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Uso UTF-8 e indentação para o arquivo ficar fácil de ler no PyCharm.
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
