"""Gero um resumo executivo rastreável a partir dos exports Gold/portfolio."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "portfolio"
OUTPUT = ROOT / "docs" / "resumo_executivo.md"


def main() -> None:
    bauru = pd.read_csv(DATA / "bauru_estudo_sintese.csv").iloc[0]
    states = pd.read_csv(DATA / "inteligencia_crescimento_estados.csv")
    models = pd.read_csv(DATA / "bauru_modelos_ranking.csv")
    solar = pd.read_csv(DATA / "bauru_solar_context.csv").iloc[0]
    challenge = pd.read_csv(DATA / "ml_desafio_selecao_modelos.csv")
    top_state = states.sort_values("acrescimo_2026_2025").iloc[-1]
    top_model = models.iloc[0]
    model_label = str(top_model.modelo)
    if not model_label.upper().startswith(str(top_model.marca).upper()):
        model_label = f"{top_model.marca} {model_label}"
    ml_lines = "\n".join(
        f"- **{row.tecnologia}:** {row.metodo}; WAPE de teste {row.wape_teste_medio:.1f}%, contra {row.wape_persistencia_teste:.1f}% da referência persistente."
        for row in challenge.itertuples()
    )
    text = f"""# Resumo executivo — Mercado de veículos eletrificados no Brasil

## A pergunta de negócio

Onde a mobilidade elétrica está avançando, quais sinais justificam uma investigação comercial e quais conclusões ainda não podem ser tratadas como decisão?

## O que os dados mostram

- O projeto separa estoque de frota (SENATRAN) de fluxo de novos emplacamentos (ABVE/FENABRAVE). O recorte mensal observado é janeiro/2024 a agosto/2026.
- **{top_state.uf}** foi o maior contribuinte absoluto para o crescimento estadual no recorte publicado, com **{int(top_state.acrescimo_2026_2025):,}** registros adicionais na comparação analisada.
- Em Bauru, os registros BEV/PHEV passaram de **{int(bauru.jan_ago_2024):,}** em jan–ago/2024 para **{int(bauru.jan_ago_2026):,}** em jan–ago/2026. O crescimento foi **{bauru.crescimento_bauru_percentual:.1f}%**, contra **{bauru.crescimento_pares_agregado_percentual:.1f}%** nos dez pares socioeconômicos.
- O modelo mais frequente entre os registros de Bauru desde 2024 foi **{model_label}**, com **{int(top_model.emplacamentos):,}** registros de modelo publicados pelo painel ABVE.
- A ANEEL registra **{int(solar.empreendimentos_fotovoltaicos):,}** empreendimentos fotovoltaicos em Bauru, somando **{float(solar.potencia_fotovoltaica_kw):,.2f} kW**. Isso é contexto de oferta solar municipal, não prova de recarga residencial dos veículos.

## Como usar a análise

1. Priorizar localidades com crescimento observado e tamanho de mercado suficiente para uma investigação de recarga, sem transformar ranking em recomendação automática.
2. Usar os modelos por cidade para orientar pesquisa de produto e infraestrutura, preservando a diferença entre emplacamento e frota em circulação.
3. Tratar preço, recarga e geração solar como sinais complementares. Eles não têm a mesma chave, periodicidade ou população observada.

## Previsão e risco

{ml_lines}

As previsões são experimentais. O teste histórico serve para escolher métodos dentro do protocolo, mas a validação prospectiva só existe quando meses novos forem observados. Não há evidência suficiente para afirmar depreciação, probabilidade individual de compra, falha de bateria ou efeito causal de políticas.

## Próxima decisão de dados

Ampliar preços comparáveis por versão, validar presencialmente os pontos de recarga de Bauru e coletar respostas anônimas sobre uso profissional, recarga doméstica e energia solar. Essas três ações fecham as principais lacunas entre hipótese local e evidência mensurada.

_Gerado por `python -m src.analysis.build_executive_summary`; números vêm dos CSVs publicados e podem ser auditados no `data/portfolio/auditoria_exports.csv`._
"""
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"Resumo executivo publicado em {OUTPUT}")


if __name__ == "__main__":
    main()
