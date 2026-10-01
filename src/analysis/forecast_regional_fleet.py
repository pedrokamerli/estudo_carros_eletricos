"""Avalio crescimento do estoque regional, mantendo-o separado de vendas."""

import hashlib
import pandas as pd
import sklearn

from src.analysis.forecast_ml import OUTPUT, evaluate
from src.database.connection import get_connection

REGIONS = {
    "Norte": "ACRE|AMAPA|AMAZONAS|PARA|RONDONIA|RORAIMA|TOCANTINS",
    "Nordeste": "ALAGOAS|BAHIA|CEARA|MARANHAO|PARAIBA|PERNAMBUCO|PIAUI|RIO GRANDE DO NORTE|SERGIPE",
    "Sudeste": "ESPIRITO SANTO|MINAS GERAIS|RIO DE JANEIRO|SAO PAULO",
    "Sul": "PARANA|RIO GRANDE DO SUL|SANTA CATARINA",
    "Centro-Oeste": "DISTRITO FEDERAL|GOIAS|MATO GROSSO|MATO GROSSO DO SUL",
}
UF_REGION = {uf: region for region, states in REGIONS.items() for uf in states.split("|")}


def aggregate(frame):
    """Conservo toda a quantidade, inclusive a parcela que não posso localizar."""
    frame = frame.copy()
    normalized = frame.uf.str.strip().str.upper()
    unknown = ~normalized.isin(UF_REGION)
    if not normalized[unknown].isin(["SEM INFORMAÇÃO", "SEM INFORMACAO"]).all():
        raise ValueError("UF inesperada: preciso revisar o mapeamento regional.")
    frame["regiao"] = normalized.map(UF_REGION).fillna("UF não informada")
    result = frame.groupby(["ano_referencia", "mes_referencia", "regiao"], as_index=False).total_veiculos_eletrificados.sum()
    result["data_referencia"] = pd.to_datetime(dict(year=result.ano_referencia, month=result.mes_referencia, day=1))
    if result.total_veiculos_eletrificados.sum() != frame.total_veiculos_eletrificados.sum():
        raise ValueError("A agregação regional perdeu quantidade.")
    result = result.sort_values(["regiao", "data_referencia"])
    previous = result.groupby("regiao").total_veiculos_eletrificados.shift(12)
    result["crescimento_yoy_percentual"] = 100 * (result.total_veiculos_eletrificados / previous.where(previous.ne(0)) - 1)
    return result


def main():
    with get_connection() as connection:
        query = connection.execute("SELECT ano_referencia, mes_referencia, uf, SUM(quantidade_veiculos)::BIGINT AS total_veiculos_eletrificados FROM silver.frota_eletrificada GROUP BY ano_referencia, mes_referencia, uf ORDER BY ano_referencia, mes_referencia, uf")
        source = pd.DataFrame(query.fetchall(), columns=[col.name for col in query.description])
    series = aggregate(source)
    # Confiro 32 competências antes de treinar. Não uso períodos fora do estudo.
    expected = pd.date_range("2024-01-01", "2026-08-01", freq="MS")
    for _, group in series.groupby("regiao"):
        if not pd.DatetimeIndex(group.data_referencia).equals(expected):
            raise ValueError("A região não possui o recorte mensal completo.")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    series["fonte"] = "SENATRAN"
    series["url_fonte"] = "https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/estatisticas-frota-de-veiculos-senatran"
    series.to_csv(OUTPUT / "frota_regional_mensal.csv", index=False)
    known = series.loc[series.regiao.ne("UF não informada")].rename(columns={
        "regiao": "categoria_fenabrave", "total_veiculos_eletrificados": "emplacamentos_mes"})
    frames = evaluate(known)
    fingerprint = hashlib.sha256(source.to_json(orient="records").encode()).hexdigest()
    for name, frame in frames.items():
        frame.rename(columns={"categoria_fenabrave": "regiao", "emplacamentos_previstos": "frota_prevista"}, inplace=True)
        frame["fonte"] = "SENATRAN"
        frame.drop(columns=["segmento_veiculos"], errors="ignore", inplace=True)
        frame["alvo"] = "estoque_frota_eletrificada_definicao_combustiveis"
        frame["sha256_entrada"] = fingerprint
        frame["versao_sklearn"] = sklearn.__version__
        frame["tipo_backtest"] = "retrospectivo_snapshot_atual_sem_vintages"
        frame["status_uso"] = "experimental_nao_aprovado_sem_intervalo_calibrado"
        # As cinco projeções são independentes: não imponho soma nacional artificial.
        frame.to_csv(OUTPUT / (name.replace("ml_", "ml_frota_regional_", 1) + ".csv"), index=False)
    print(frames["ml_selecao_modelos"].to_string(index=False))


if __name__ == "__main__":
    main()
