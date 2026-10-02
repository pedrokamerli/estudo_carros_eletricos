"""Gero uma auditoria leve e reproduzível dos exports publicados.

O objetivo é tornar explícitos grão, cobertura temporal e problemas de qualidade
antes de alguém consumir um CSV no Power BI ou no PostgreSQL.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "portfolio"
OUTPUT = DATA / "auditoria_exports.csv"


def _period(frame: pd.DataFrame) -> tuple[str, str]:
    candidates = [c for c in frame.columns if c.lower() in {"data_referencia", "data", "mes", "ano_mes", "periodo"} or "data" in c.lower()]
    values = []
    for col in candidates:
        parsed = pd.to_datetime(frame[col], errors="coerce", utc=True)
        values.extend(parsed.dropna().tolist())
    if not values:
        return "", ""
    return pd.Timestamp(min(values)).date().isoformat(), pd.Timestamp(max(values)).date().isoformat()


def main() -> None:
    rows = []
    for path in sorted(DATA.glob("*.csv")):
        if path.name == OUTPUT.name:
            continue
        try:
            frame = pd.read_csv(path, low_memory=False)
            numeric = frame.select_dtypes(include="number")
            negative = int((numeric < 0).sum().sum()) if not numeric.empty else 0
            null_cells = int(frame.isna().sum().sum())
            duplicate_rows = int(frame.duplicated().sum())
            start, end = _period(frame)
            source_cols = [c for c in frame.columns if "url" in c.lower() or "fonte" in c.lower()]
            source_cells = int(frame[source_cols].notna().sum().sum()) if source_cols else 0
            # Negativos são sinalizados, mas não reprovam automaticamente: erros,
            # variações e coordenadas podem ser negativos por definição.
            status = "OK" if duplicate_rows == 0 else "REVISAR"
            rows.append({
                "arquivo": path.name,
                "linhas": int(len(frame)),
                "colunas": int(len(frame.columns)),
                "celulas_nulas": null_cells,
                "linhas_duplicadas": duplicate_rows,
                "valores_numericos_negativos": negative,
                "fontes_preenchidas": source_cells,
                "periodo_inicio": start,
                "periodo_fim": end,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "status": status,
                "observacao": "Auditoria estrutural; nulos e negativos podem ser legítimos conforme a fonte e o grão.",
            })
        except Exception as exc:  # registro a falha sem esconder o arquivo problemático
            rows.append({"arquivo": path.name, "status": "ERRO", "observacao": f"Falha ao ler: {type(exc).__name__}: {exc}"})
    report = pd.DataFrame(rows)
    report.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"Auditoria publicada: {len(report)} exports; {int((report.status == 'OK').sum())} OK; {int((report.status != 'OK').sum())} para revisão.")


if __name__ == "__main__":
    main()
