"""Valido o snapshot ABVE versionado e preparo sua tabela Silver em Parquet."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "data" / "portfolio" / "emplacamentos_abve_mensais.csv"
SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "abve"
PARQUET_PATH = SILVER_PATH / "emplacamentos_mensais.parquet"
QUALITY_PATH = PROJECT_ROOT / "data" / "quality" / "abve_validacao.csv"
KEY_COLUMNS = ["ano_referencia", "mes_referencia"]
COUNT_COLUMNS = [
    "emplacamentos_total_painel", "emplacamentos_bev", "emplacamentos_phev",
    "emplacamentos_hev", "emplacamentos_hev_flex", "emplacamentos_mhev",
    "soma_tecnologias_publicadas", "divergencia_total_vs_tecnologias",
]
SOURCE_COLUMNS = ["regra_classificacao", "url_fonte", "data_captura", "metodo_extracao"]


def main() -> None:
    """Confiro chaves, período e somas antes de disponibilizar os dados no banco."""
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"Snapshot fonte ABVE não encontrado: {SOURCE_PATH}")
    dataframe = pd.read_csv(SOURCE_PATH, dtype={column: "string" for column in SOURCE_COLUMNS})
    required = KEY_COLUMNS + COUNT_COLUMNS + SOURCE_COLUMNS
    missing_columns = sorted(set(required) - set(dataframe.columns))
    if missing_columns:
        raise ValueError(f"Colunas ausentes no snapshot ABVE: {missing_columns}")

    dataframe[KEY_COLUMNS + COUNT_COLUMNS] = dataframe[KEY_COLUMNS + COUNT_COLUMNS].apply(
        pd.to_numeric, errors="raise"
    )
    # Contagens são inteiras; o tipo anulável preserva meses sem detalhamento sem
    # transformar, por exemplo, 3.700 em texto decimal "3700.0" no COPY do PostgreSQL.
    dataframe[COUNT_COLUMNS] = dataframe[COUNT_COLUMNS].astype("Int64")
    dataframe["data_captura"] = pd.to_datetime(
        dataframe["data_captura"], format="%Y-%m-%d", errors="raise"
    ).dt.date

    if dataframe[required].isna().any().any():
        # Só as colunas tecnológicas e os campos de conciliação podem estar vazios antes de 2025.
        permitted_nulls = {
            "emplacamentos_bev", "emplacamentos_phev", "emplacamentos_hev",
            "emplacamentos_hev_flex", "emplacamentos_mhev",
            "soma_tecnologias_publicadas", "divergencia_total_vs_tecnologias",
        }
        unexpected_nulls = [
            column for column in required
            if column not in permitted_nulls and dataframe[column].isna().any()
        ]
        if unexpected_nulls:
            raise ValueError(f"Campos obrigatórios ausentes no snapshot ABVE: {unexpected_nulls}")

    if dataframe.duplicated(KEY_COLUMNS).any():
        raise ValueError("O snapshot ABVE contém mais de uma linha para um mesmo mês.")
    if not dataframe["mes_referencia"].between(1, 12).all():
        raise ValueError("O snapshot ABVE contém um mês inválido.")
    if (dataframe["emplacamentos_total_painel"] < 0).any():
        raise ValueError("O snapshot ABVE contém total negativo.")
    numeric_counts = dataframe[COUNT_COLUMNS].stack()
    if (numeric_counts < 0).any():
        raise ValueError("O snapshot ABVE contém contagem negativa.")

    expected_periods = pd.period_range("2024-01", "2026-08", freq="M")
    period_dates = pd.to_datetime(
        {
            "year": dataframe["ano_referencia"].astype(int),
            "month": dataframe["mes_referencia"].astype(int),
            "day": 1,
        }
    )
    actual_periods = pd.PeriodIndex(period_dates, freq="M")
    if len(dataframe) != len(expected_periods) or not expected_periods.equals(
        actual_periods.sort_values()
    ):
        raise ValueError("A cobertura ABVE deve ser contínua de jan/2024 a ago/2026.")

    technology_columns = [
        "emplacamentos_bev", "emplacamentos_phev", "emplacamentos_hev",
        "emplacamentos_hev_flex",
    ]
    has_technology_breakdown = dataframe[technology_columns].notna().all(axis=1)
    if has_technology_breakdown.sum() != 20:
        raise ValueError("Esperava composição tecnológica em jan/2025–ago/2026 (20 meses).")
    if dataframe.loc[has_technology_breakdown, "ano_referencia"].min() != 2025:
        raise ValueError("A composição ABVE começa fora do mês/ano esperado.")
    recalculated_sum = dataframe.loc[has_technology_breakdown, technology_columns].sum(axis=1)
    recalculated_sum = recalculated_sum.astype("int64")
    if not recalculated_sum.equals(
        dataframe.loc[has_technology_breakdown, "soma_tecnologias_publicadas"].astype(int)
    ):
        raise ValueError("A soma recalculada das tecnologias diverge do campo publicado no CSV.")
    recalculated_difference = (
        dataframe.loc[has_technology_breakdown, "emplacamentos_total_painel"]
        - recalculated_sum
    ).astype("int64")
    if not recalculated_difference.equals(
        dataframe.loc[has_technology_breakdown, "divergencia_total_vs_tecnologias"].astype(int)
    ):
        raise ValueError("O campo de divergência não corresponde aos valores preservados.")

    discrepancy_rows = dataframe.loc[
        dataframe["divergencia_total_vs_tecnologias"].fillna(0).ne(0),
        KEY_COLUMNS + [
            "emplacamentos_total_painel", "soma_tecnologias_publicadas",
            "divergencia_total_vs_tecnologias", "url_fonte", "data_captura",
        ],
    ]
    SILVER_PATH.mkdir(parents=True, exist_ok=True)
    QUALITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataframe.sort_values(KEY_COLUMNS).to_parquet(PARQUET_PATH, index=False)
    discrepancy_rows.to_csv(QUALITY_PATH, index=False, encoding="utf-8-sig")
    print(f"Silver ABVE validada: {len(dataframe)} linhas em {PARQUET_PATH}")
    print(f"Meses com tecnologias detalhadas: {has_technology_breakdown.sum()}")
    print(f"Divergências painel versus soma tecnológica: {len(discrepancy_rows)}")
    print(f"Validação salva em: {QUALITY_PATH}")


if __name__ == "__main__":
    # Inicio a transformação somente quando executo este módulo diretamente.
    main()
