"""Concilio os recortes do painel antes de usá-los em análise."""

import hashlib
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data/portfolio"


def validate_frames(frames):
    """Exijo 32 meses, contagens válidas, chaves únicas e somas iguais por tecnologia."""
    expected = pd.date_range("2024-01-01", "2026-08-01", freq="MS")
    reference = None
    for name, frame in frames.items():
        keys = ["data_referencia", "Tipo_Tecnologia"] + (["Fabricante", "Modelo"] if name == "modelo" else
                                                       ["Estado", "Município"] if name == "municipio" else [])
        if frame.empty or frame.duplicated(keys).any():
            raise ValueError(f"Chave vazia/duplicada: {name}")
        if frame.emplacamentos.isna().any() or (frame.emplacamentos < 0).any() or (frame.emplacamentos % 1 != 0).any():
            raise ValueError("Quantidades devem ser inteiras e não negativas.")
        if not pd.DatetimeIndex(sorted(pd.to_datetime(frame.data_referencia).unique())).equals(expected):
            raise ValueError("Períodos incompletos ou fora do recorte.")
        totals = frame.groupby(["data_referencia", "Tipo_Tecnologia"]).emplacamentos.sum().sort_index()
        if reference is None:
            reference = totals
        elif not totals.equals(reference):
            raise ValueError(f"Totais por tecnologia não conciliam: {name}")


def main():
    frames = {name: pd.read_csv(ROOT / f"data/silver/abve_public/{name}_decodificado.csv") for name in ("tecnologia", "modelo", "municipio")}
    validate_frames(frames)
    for name, frame in frames.items():
        dimensions = [c for c in ("data_referencia", "Tipo_Tecnologia", "Fabricante", "Modelo", "Estado", "Município") if c in frame]
        frame["id_registro"] = [hashlib.sha256(json.dumps([None if pd.isna(v) else v for v in row], ensure_ascii=False).encode()).hexdigest()
                                for row in frame[dimensions].itertuples(index=False, name=None)]
        frame["escopo_tecnologia"] = "inclui_MHEV_filtrar_BEV_PHEV_para_comparabilidade"
        frame = frame.rename(columns={"Tipo_Tecnologia": "tecnologia", "Fabricante": "marca", "Modelo": "modelo", "Estado": "uf", "Município": "municipio"})
        path = ROOT / "data/silver/abve_public"
        path.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(path / f"{name}.parquet", index=False)
        frame.to_csv(OUTPUT / f"abve_publico_{name}_gold.csv", index=False)
    current = frames["tecnologia"].query("Tipo_Tecnologia in ['BEV', 'PHEV']")
    original = pd.read_csv(OUTPUT / "abve_plugin_mensais.csv")
    audit = current.merge(original, left_on=["data_referencia", "Tipo_Tecnologia"], right_on=["data_referencia", "tecnologia"], validate="one_to_one")
    if len(audit) != 64:
        raise ValueError("Não consegui conferir todos os meses plug-in.")
    audit["diferenca_painel_menos_serie_anterior"] = audit.emplacamentos - audit.emplacamentos_mes
    audit[["data_referencia", "tecnologia", "emplacamentos", "emplacamentos_mes", "diferenca_painel_menos_serie_anterior"]].to_csv(OUTPUT / "abve_publico_conciliacao_plugin.csv", index=False)
    print("ABVE: três recortes conciliados em 32 meses; divergências preservadas.")


if __name__ == "__main__":
    main()
