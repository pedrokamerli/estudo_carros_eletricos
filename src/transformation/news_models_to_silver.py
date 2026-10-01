"""Valido rankings de notícias sem transformar recortes parciais numa série completa."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "data/portfolio/fontes_rankings_modelos_noticias.csv"
SNAPSHOT = ROOT / "data/portfolio/rankings_modelos_noticias_snapshot.csv"
OUTPUT = ROOT / "data/silver/market/rankings_modelos_noticias.parquet"


def validate_and_join(records, sources):
    """Confiro datas, contagens, chaves e escopo antes de preparar os dados."""
    required = {"fonte_id", "posicao", "marca", "modelo_original", "tecnologia_fonte",
                "quantidade_emplacada", "observacao_registro"}
    source_required = {"fonte_id", "publicador", "origem_declarada", "tipo_fonte", "url_fonte",
                       "data_publicacao", "inicio_periodo", "fim_periodo", "tipo_periodo",
                       "escopo_tecnologias", "granularidade", "posicoes_publicadas",
                       "total_mercado_publicado", "observacao_fonte"}
    if not required.issubset(records) or not source_required.issubset(sources):
        raise ValueError("Faltam colunas no snapshot ou no catálogo de fontes.")
    records, sources = records.copy(), sources.copy()
    if sources["fonte_id"].duplicated().any() or records.duplicated(["fonte_id", "posicao"]).any():
        raise ValueError("Fonte ou posição duplicada.")
    source_metadata = sorted(source_required - {"total_mercado_publicado", "observacao_fonte"})
    if sources[source_metadata].isna().any().any():
        raise ValueError("Metadados obrigatórios da fonte ausentes.")
    if not sources["url_fonte"].str.startswith("https://").all():
        raise ValueError("Fonte sem URL HTTPS verificável.")
    for column in ("posicao", "quantidade_emplacada"):
        records[column] = pd.to_numeric(records[column], errors="raise").astype("Int64")
    for column in ("posicoes_publicadas", "total_mercado_publicado"):
        sources[column] = pd.to_numeric(sources[column], errors="raise").astype("Int64")
    if records[["fonte_id", "posicao", "marca", "modelo_original", "tecnologia_fonte"]].isna().any().any():
        raise ValueError("Chave, modelo, tecnologia ou posição vazia.")
    if records["quantidade_emplacada"].dropna().lt(0).any():
        raise ValueError("Quantidade negativa.")
    if sources["total_mercado_publicado"].dropna().lt(0).any():
        raise ValueError("Total do segmento negativo.")
    if not sources["tipo_periodo"].isin(["mensal", "acumulado"]).all():
        raise ValueError("Tipo de período desconhecido.")
    for column in ("data_publicacao", "inicio_periodo", "fim_periodo"):
        sources[column] = pd.to_datetime(sources[column], errors="raise")
    if sources[["data_publicacao", "inicio_periodo", "fim_periodo"]].isna().any().any():
        raise ValueError("Data da fonte ausente.")
    if (sources["inicio_periodo"] > sources["fim_periodo"]).any() or (sources["data_publicacao"] < sources["fim_periodo"]).any():
        raise ValueError("Período inválido ou fechamento anterior ao fim do período.")
    monthly = sources.loc[sources["tipo_periodo"].eq("mensal")]
    if (monthly["inicio_periodo"].dt.to_period("M") != monthly["fim_periodo"].dt.to_period("M")).any():
        raise ValueError("Uma fonte mensal abrange mais de um mês.")
    if not set(records["fonte_id"]) == set(sources["fonte_id"]):
        raise ValueError("Registro sem fonte ou fonte sem registros.")
    for source_id, group in records.groupby("fonte_id"):
        count = int(sources.loc[sources["fonte_id"].eq(source_id), "posicoes_publicadas"].iloc[0])
        if set(group["posicao"].astype(int)) != set(range(1, count + 1)):
            raise ValueError(f"Ranking incompleto ou posição inválida: {source_id}")
    result = records.merge(sources, on="fonte_id", validate="many_to_one")
    # Padronizo caixa/espaços, preservando versões; não uno nomes parecidos automaticamente.
    result["modelo_padronizado"] = result["modelo_original"].str.upper().str.replace(r"\s+", " ", regex=True).str.strip()
    result["quantidade_informada"] = result["quantidade_emplacada"].notna()
    result["data_captura"] = pd.Timestamp("2026-09-30")
    result["metodo_extracao"] = "transcricao_revisada_da_publicacao"
    result["cobertura"] = "ranking_parcial_nao_censo"
    return result


def main():
    """Gero Silver e resumo a disponibilidade sem preencher quantidades ausentes."""
    result = validate_and_join(pd.read_csv(SNAPSHOT, dtype="string"), pd.read_csv(SOURCES, dtype="string"))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(OUTPUT, index=False)
    print(f"Notícias validadas: {len(result)} registros em {result['fonte_id'].nunique()} rankings; "
          f"{result['quantidade_informada'].sum()} quantidades informadas.")


if __name__ == "__main__":
    main()
