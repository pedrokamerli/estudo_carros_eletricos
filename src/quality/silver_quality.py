"""Valido se uma tabela Silver continua pronta para ser usada na camada Gold."""

from __future__ import annotations

import pandas as pd


SENATRAN_SILVER_COLUMNS = {
    "uf", "municipio", "combustivel_veiculo", "quantidade_veiculos",
    "categoria_eletrificacao", "uf_informada", "tipo_localidade",
    "ano_referencia", "mes_referencia", "fonte",
}


def assess_senatran_silver(dataframe: pd.DataFrame) -> dict[str, object]:
    """Confiro estrutura, nulos, valores negativos e total da tabela Silver da SENATRAN."""
    missing_columns = sorted(SENATRAN_SILVER_COLUMNS.difference(dataframe.columns))
    duplicate_rows = int(
        dataframe.duplicated(
            ["uf", "municipio", "combustivel_veiculo", "ano_referencia", "mes_referencia"]
        ).sum()
    ) if not missing_columns else None

    if missing_columns:
        return {"aprovado": False, "colunas_ausentes": missing_columns}

    null_counts = dataframe[list(SENATRAN_SILVER_COLUMNS)].isna().sum()
    null_counts = {column: int(count) for column, count in null_counts.items() if count > 0}
    negative_quantities = int((dataframe["quantidade_veiculos"] < 0).sum())
    total_processed = int(dataframe["quantidade_veiculos"].sum())

    # Aceito UF desconhecida como texto, mas não aceito município ou período vazios.
    critical_nulls = {
        column: count for column, count in null_counts.items()
        if column in {"municipio", "quantidade_veiculos", "ano_referencia", "mes_referencia"}
    }
    approved = not missing_columns and not critical_nulls and negative_quantities == 0 and duplicate_rows == 0

    return {
        "aprovado": approved,
        "colunas_ausentes": missing_columns,
        "nulos": null_counts,
        "quantidades_negativas": negative_quantities,
        "linhas_duplicadas_na_chave": duplicate_rows,
        "total_processado": total_processed,
        "linhas_processadas": int(len(dataframe)),
    }
