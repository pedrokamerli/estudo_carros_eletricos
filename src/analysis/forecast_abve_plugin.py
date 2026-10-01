"""Avalio BEV e PHEV da ABVE como alvos distintos dos grupos FENABRAVE."""

from hashlib import sha256

import pandas as pd
import sklearn

from src.analysis.forecast_ml import OUTPUT, evaluate
from src.transformation.abve_plugin_to_silver import OUTPUT as INPUT


def main():
    source = pd.read_parquet(INPUT)
    # Adapto apenas o nome técnico da chave ao avaliador compartilhado; não mudo fonte/alvo.
    source = source.rename(columns={"tecnologia": "categoria_fenabrave"})
    frames = evaluate(source)
    for name, frame in frames.items():
        frame.rename(columns={"categoria_fenabrave": "tecnologia"}, inplace=True)
        frame["fonte"] = "ABVE"
        frame["segmento_veiculos"] = "veiculos_leves_plugin"
        frame["sha256_silver"] = sha256(INPUT.read_bytes()).hexdigest()
        frame["versao_sklearn"] = sklearn.__version__
        # Datas dos valores são históricas; a captura é atual, não um arquivo de versões passadas.
        frame["tipo_backtest"] = "retrospectivo_snapshot_atual_sem_vintages"
        OUTPUT.mkdir(parents=True, exist_ok=True)
        frame.to_csv(OUTPUT / (name.replace("ml_", "ml_abve_", 1) + ".csv"), index=False, float_format="%.4f")
        print(f"{name.replace('ml_', 'ml_abve_', 1)}: {len(frame)} linhas")
    print(frames["ml_selecao_modelos"].to_string(index=False))


if __name__ == "__main__":
    main()
