"""Executo de ponta a ponta as etapas públicas e reproduzíveis do meu projeto."""

from __future__ import annotations

import subprocess
import sys


PIPELINE_MODULES = [
    "src.ingestion.download_senatran_fuel_history",
    "src.ingestion.download_ibge_municipal_indicators",
    "src.ingestion.download_fenabrave_monthly_reports",
    "src.transformation.ibge_bronze_to_silver",
    "src.transformation.fenabrave_reports_to_silver",
    "src.transformation.abve_snapshot_to_silver",
    "src.transformation.abve_charging_snapshot_to_silver",
    "src.analysis.backtest_fenabrave_forecast",
    "src.analysis.forecast_ml",
    "src.run_pipeline",
    "src.database.load_silver_to_postgres",
    "src.database.load_fenabrave_to_postgres",
    "src.database.load_abve_to_postgres",
    "src.database.load_abve_charging_to_postgres",
    "src.transformation.silver_to_gold",
    "src.database.build_gold_tables",
    "src.database.load_municipal_insights_to_postgres",
    "src.analysis.opportunity_sensitivity",
    "src.database.load_forecast_backtest_to_postgres",
    "src.database.load_ml_to_postgres",
    "src.database.export_portfolio_data",
]


def main() -> None:
    """Rodo cada etapa em ordem e paro no primeiro erro para evitar publicar dados incompletos."""
    for module_name in PIPELINE_MODULES:
        print(f"\n{'=' * 72}\nExecutando minha etapa: {module_name}\n{'=' * 72}", flush=True)
        subprocess.run([sys.executable, "-m", module_name], check=True)

    print("\nPipeline completa: Silver, Gold e exports do portfólio atualizados.")
    print("Os meses ainda não publicados pela SENATRAN ficam registrados no manifesto.")


if __name__ == "__main__":
    # Inicio a pipeline completa somente quando executo este módulo diretamente.
    main()
