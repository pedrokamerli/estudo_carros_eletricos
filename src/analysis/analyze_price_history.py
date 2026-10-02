"""Crio estatísticas descritivas da amostra documental de preços."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "portfolio"


def main() -> None:
    frame = pd.read_csv(DATA / "precos_historicos_documentais.csv")
    frame["data_anuncio"] = pd.to_datetime(frame["data_anuncio"], errors="coerce")
    summary = (frame.groupby("marca", as_index=False)
               .agg(anuncios=("preco_anunciado_reais", "size"),
                    preco_minimo_reais=("preco_anunciado_reais", "min"),
                    preco_mediano_reais=("preco_anunciado_reais", "median"),
                    preco_maximo_reais=("preco_anunciado_reais", "max"),
                    data_inicio=("data_anuncio", "min"),
                    data_fim=("data_anuncio", "max")))
    summary["limite_uso"] = "Amostra de preços anunciados; não é FIPE, transação, painel mensal ou depreciação."
    summary.to_csv(DATA / "precos_resumo_marca.csv", index=False)
    tech = frame.dropna(subset=["tecnologia"]).groupby(["marca", "tecnologia"], as_index=False).agg(
        anuncios=("preco_anunciado_reais", "size"), preco_mediano_reais=("preco_anunciado_reais", "median"),
        preco_minimo_reais=("preco_anunciado_reais", "min"), preco_maximo_reais=("preco_anunciado_reais", "max"))
    tech["limite_uso"] = "Tecnologia conforme fonte; condições comerciais e versões não são perfeitamente comparáveis."
    tech.to_csv(DATA / "precos_resumo_marca_tecnologia.csv", index=False)
    print(f"Preços: {len(summary)} marcas e {len(tech)} combinações marca/tecnologia resumidas.")


if __name__ == "__main__":
    main()
