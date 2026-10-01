"""Uno séries nacionais BEV/PHEV, sem misturar MHEV nem totais de frota."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HISTORY = ROOT / "data/portfolio/abve_plugin_2024_fontes.csv"
SNAPSHOT = ROOT / "data/portfolio/emplacamentos_abve_mensais.csv"
OUTPUT = ROOT / "data/silver/abve/plugin_mensais.parquet"


def build_series(history, snapshot):
    historical = history.copy()
    historical["data_referencia"] = pd.to_datetime(historical["data_referencia"], errors="raise")
    if not pd.DatetimeIndex(historical["data_referencia"]).equals(pd.date_range("2024-01-01", periods=12, freq="MS")):
        raise ValueError("Espero os 12 meses de 2024 ordenados e únicos.")
    historical["data_publicacao"] = pd.to_datetime(historical["data_publicacao"], errors="raise")
    if historical[["url_fonte", "data_revisao", "data_publicacao"]].isna().any().any():
        raise ValueError("Proveniência de 2024 incompleta.")
    if not historical["url_fonte"].str.startswith("https://abve.org.br/").all():
        raise ValueError("Espero fonte primária ABVE para o histórico.")
    if (historical["data_publicacao"] <= historical["data_referencia"] + pd.offsets.MonthEnd(0)).any():
        raise ValueError("Publicação anterior ao fechamento do mês.")
    latest = snapshot.loc[snapshot["ano_referencia"].ge(2025)].copy()
    latest["data_referencia"] = pd.to_datetime(dict(year=latest["ano_referencia"], month=latest["mes_referencia"], day=1))
    if latest.empty or latest[["url_fonte", "data_captura", "regra_classificacao"]].isna().any().any():
        raise ValueError("Snapshot recente sem proveniência obrigatória.")
    if not latest["url_fonte"].str.startswith("https://abve.org.br/").all():
        raise ValueError("Snapshot recente fora da fonte primária ABVE.")
    if not latest["regra_classificacao"].eq("BEV_PHEV_HEV_HEV_FLEX_sem_MHEV").all():
        raise ValueError("Regra do snapshot mudou; preciso revisar a comparabilidade.")
    captures = pd.to_datetime(latest["data_captura"], errors="raise")
    if (latest["data_referencia"] + pd.offsets.MonthEnd(0) > captures).any():
        raise ValueError("Encontrei mês ainda não fechado na data da captura.")
    rows = []
    for technology in ("BEV", "PHEV"):
        column = "emplacamentos_" + technology.lower()
        for frame, method in ((historical, "transcricao_publicacao_mensal_revisada"),
                              (latest, "snapshot_painel_revisado")):
            counts = pd.to_numeric(frame[column], errors="raise")
            if counts.isna().any() or (counts < 0).any() or (counts % 1 != 0).any():
                raise ValueError("Contagens mensais precisam ser inteiras e não negativas.")
            for (_, record), count in zip(frame.iterrows(), counts):
                rows.append(dict(data_referencia=record["data_referencia"], tecnologia=technology,
                                 emplacamentos_mes=int(count), fonte="ABVE",
                                 segmento_veiculos="veiculos_leves_plugin",
                                 url_fonte=record["url_fonte"], metodo_extracao=method,
                                 data_revisao=str(record.get("data_revisao", record.get("data_captura"))),
                                 data_publicacao=(record["data_publicacao"].date().isoformat() if method.startswith("transcricao") else None),
                                 observacao=record.get("observacao", "Snapshot atual; sem histórico de versões do painel")))
        # Uso o fechamento anual como conferência independente, nunca como ajuste artificial.
        expected = 61615 if technology == "BEV" else 64009
        if int(historical[column].sum()) != expected:
            raise ValueError(f"Soma de 2024 não confere com fechamento ABVE para {technology}.")
    result = pd.DataFrame(rows).sort_values(["tecnologia", "data_referencia"])
    for _, group in result.groupby("tecnologia"):
        expected = pd.date_range("2024-01-01", latest["data_referencia"].max(), freq="MS")
        if not pd.DatetimeIndex(group["data_referencia"]).equals(expected):
            raise ValueError("Lacunas ou duplicações na série plug-in.")
    return result


def main():
    frame = build_series(pd.read_csv(HISTORY), pd.read_csv(SNAPSHOT))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(OUTPUT, index=False)
    frame.to_csv(ROOT / "data/portfolio/abve_plugin_mensais.csv", index=False)
    print(f"Silver ABVE plug-in: {len(frame)} registros; {frame.groupby('tecnologia').size().to_dict()}")


if __name__ == "__main__":
    main()
