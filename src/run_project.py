"""Executo de ponta a ponta as etapas públicas e reproduzíveis do meu projeto."""

from __future__ import annotations

import subprocess
import sys


PIPELINE_MODULES = [
    "src.ingestion.download_inmetro_pbev",
    "src.transformation.inmetro_to_silver",
    "src.ingestion.capture_abve_aggregates",
    "src.transformation.abve_public_to_silver",
    "src.database.load_public_enrichment",
    "src.ingestion.download_senatran_fuel_history",
    "src.ingestion.download_ibge_municipal_indicators",
    "src.ingestion.download_fenabrave_monthly_reports",
    "src.ingestion.download_osm_charging",
    "src.ingestion.download_bcb_context",
    "src.ingestion.download_ons_load",
    "src.transformation.ibge_bronze_to_silver",
    "src.transformation.fenabrave_reports_to_silver",
    "src.transformation.abve_snapshot_to_silver",
    "src.transformation.abve_plugin_to_silver",
    "src.transformation.abve_charging_snapshot_to_silver",
    "src.transformation.news_models_to_silver",
    "src.transformation.osm_charging_to_silver",
    "src.analysis.backtest_fenabrave_forecast",
    "src.analysis.forecast_ml",
    "src.analysis.forecast_abve_plugin",
    "src.analysis.forecast_macro_abve",
    "src.run_pipeline",
    "src.database.load_silver_to_postgres",
    "src.database.load_fenabrave_to_postgres",
    "src.database.load_abve_to_postgres",
    "src.database.load_abve_charging_to_postgres",
    "src.database.load_news_models_to_postgres",
    "src.database.load_osm_charging_to_postgres",
    "src.database.load_bcb_to_postgres",
    "src.transformation.silver_to_gold",
    "src.database.build_gold_tables",
    "src.analysis.forecast_regional_fleet",
    "src.analysis.forecast_intervals",
    "src.database.load_municipal_insights_to_postgres",
    "src.analysis.opportunity_sensitivity",
    "src.database.load_forecast_backtest_to_postgres",
    "src.database.load_ml_to_postgres",
    "src.database.build_bi_model",
    "src.database.export_portfolio_data",
    # Produzo inteligência depois dos exports conciliados, fora da interface visual.
    "src.ingestion.download_charging_evidence",
    "src.ingestion.download_bauru_directory_evidence",
    "src.ingestion.download_aneel_solar_context",
    "src.ingestion.download_abve_bauru_models",
    "src.ingestion.download_price_evidence",
    "src.ingestion.download_price_history",
    "src.analysis.analyze_price_history",
    "src.analysis.market_intelligence",
    "src.analysis.forecast_challengers",
    "src.analysis.bauru_case",
    "src.analysis.analyze_bauru_models",
    "src.analysis.enrich_bauru_models",
    "src.analysis.evaluate_frozen_predictions",
    "src.analysis.question_evidence",
    "src.analysis.build_executive_summary",
    "src.analysis.analyze_inmetro_catalog",
    "src.analysis.build_project_audit",
    "src.database.load_market_intelligence",
]


def main() -> None:
    """Rodo cada etapa em ordem e paro no primeiro erro para evitar publicar dados incompletos."""
    for module_name in PIPELINE_MODULES:
        print(f"\n{'=' * 72}\nExecutando minha etapa: {module_name}\n{'=' * 72}", flush=True)
        subprocess.run([sys.executable, "-m", module_name], check=True)

    print("\nPipeline completa: Silver, Gold e exports do portfólio atualizados.")
    print("Meu recorte observado está fechado: janeiro/2024 a agosto/2026.")


if __name__ == "__main__":
    # Inicio a pipeline completa somente quando executo este módulo diretamente.
    main()
