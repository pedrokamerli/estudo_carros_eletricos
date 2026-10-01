"""Transformo a observação local em comparações reproduzíveis, não em causalidade."""
import hashlib
import json
from datetime import datetime, timezone
import pandas as pd
from src.ingestion.download_price_evidence import ROOT

DATA = ROOT/"data/portfolio"


def summarize(peers):
    if peers.municipio_chave.duplicated().any() or peers.municipio_chave.eq("BAURU").sum() != 1:
        raise ValueError("Pares devem ser cidades únicas, com Bauru uma vez.")
    bauru = peers.loc[peers.municipio_chave.eq("BAURU")].iloc[0]
    others = peers.loc[peers.municipio_chave.ne("BAURU")]
    if others.empty or others[["jan_ago_2025","jan_ago_2026"]].isna().any().any():
        raise ValueError("Não comparo pares sem histórico completo.")
    previous, current = others.jan_ago_2025.sum(), others.jan_ago_2026.sum()
    if previous <= 0:
        raise ValueError("Preciso de base positiva para medir crescimento dos pares.")
    growth = 100*(current/previous-1)
    return dict(municipio="BAURU",jan_ago_2024=int(bauru.jan_ago_2024),jan_ago_2025=int(bauru.jan_ago_2025),
        jan_ago_2026=int(bauru.jan_ago_2026),acrescimo_2026_2025=int(bauru.acrescimo_2026_2025),
        crescimento_bauru_percentual=float(bauru.crescimento_percentual),crescimento_pares_agregado_percentual=growth,
        diferenca_crescimento_pontos_percentuais=float(bauru.crescimento_percentual)-growth,n_pares=len(others),
        posicao_volume_2026=int(peers.jan_ago_2026.rank(method="min",ascending=False).loc[bauru.name]),
        escopo="BEV/PHEV, jan–ago de cada ano; dez pares de SP selecionados por renda/população 2022, não pelo crescimento.",
        limite="Comparação descritiva, não controle causal. Uber, energia solar e recarga em shoppings são hipóteses não medidas; não sei quais modelos foram emplacados em Bauru.")


def freeze_future(projections, path, now):
    """Congelo apenas alvos em meses futuros; uma nova execução não reescreve a aposta."""
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    frame = projections.copy()
    frame["data_referencia"] = pd.to_datetime(frame.data_referencia)
    cutoff = pd.Timestamp(now.date()).replace(day=1)
    frame = frame.loc[frame.data_referencia.gt(cutoff)]
    if frame.empty:
        raise ValueError("Não há alvo mensal futuro para registrar.")
    payload = dict(registrado_em_utc=now.isoformat(),
        status="aguardando_observacoes_publicadas_sem_resultado_prospectivo",
        limite="Alvos posteriores ao mês de registro, treino encerrado em agosto/2026. Registro não aprova o modelo; observações futuras ainda precisam ser coletadas e conciliadas.",
        previsoes=json.loads(frame.to_json(orient="records",date_format="iso")))
    path.parent.mkdir(parents=True,exist_ok=True)
    # Criação exclusiva protege um registro já existente contra sobrescrita acidental.
    with path.open("x",encoding="utf-8") as file:
        json.dump(payload,file,ensure_ascii=False,indent=2)
    return payload


def main():
    peers = pd.read_csv(DATA/"estudo_bauru_pares_socioeconomicos.csv")
    result = summarize(peers)
    result["sha256_pares"] = hashlib.sha256((DATA/"estudo_bauru_pares_socioeconomicos.csv").read_bytes()).hexdigest()
    pd.DataFrame([result]).to_csv(DATA/"bauru_estudo_sintese.csv",index=False)
    registry = freeze_future(pd.read_csv(DATA/"ml_desafio_projecoes_experimentais.csv"),
        ROOT/"data/registry/previsoes_congeladas_2026_10.json",datetime.now(timezone.utc))
    future = pd.DataFrame(registry["previsoes"])
    future["registrado_em_utc"] = registry["registrado_em_utc"]
    future["status_validacao_prospectiva"] = registry["status"]
    future.to_csv(DATA/"ml_registro_prospectivo.csv",index=False)
    print(f"Bauru vs {result['n_pares']} pares: {result['diferenca_crescimento_pontos_percentuais']:.2f} pontos percentuais. Registro futuro preservado, sem resultado de teste inventado.")


if __name__ == "__main__":
    main()
