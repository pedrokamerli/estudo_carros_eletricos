# Resumo executivo — Mercado de veículos eletrificados no Brasil

## A pergunta de negócio

Onde a mobilidade elétrica está avançando, quais sinais justificam uma investigação comercial e quais conclusões ainda não podem ser tratadas como decisão?

## O que os dados mostram

- O projeto separa estoque de frota (SENATRAN) de fluxo de novos emplacamentos (ABVE/FENABRAVE). O recorte mensal observado é janeiro/2024 a agosto/2026.
- **SP** foi o maior contribuinte absoluto para o crescimento estadual no recorte publicado, com **35,183** registros adicionais na comparação analisada.
- Em Bauru, os registros BEV/PHEV passaram de **256** em jan–ago/2024 para **859** em jan–ago/2026. O crescimento foi **163.5%**, contra **136.2%** nos dez pares socioeconômicos.
- O modelo mais frequente entre os registros de Bauru desde 2024 foi **BYD DOLPHIN MINI GS5EV**, com **360** registros de modelo publicados pelo painel ABVE.
- A ANEEL registra **9,934** empreendimentos fotovoltaicos em Bauru, somando **79,600.59 kW**. Isso é contexto de oferta solar municipal, não prova de recarga residencial dos veículos.

## Como usar a análise

1. Priorizar localidades com crescimento observado e tamanho de mercado suficiente para uma investigação de recarga, sem transformar ranking em recomendação automática.
2. Usar os modelos por cidade para orientar pesquisa de produto e infraestrutura, preservando a diferença entre emplacamento e frota em circulação.
3. Tratar preço, recarga e geração solar como sinais complementares. Eles não têm a mesma chave, periodicidade ou população observada.

## Previsão e risco

- **BEV:** tendencia_log_6m; WAPE de teste 23.6%, contra 26.9% da referência persistente.
- **PHEV:** ridge; WAPE de teste 32.1%, contra 23.1% da referência persistente.

As previsões são experimentais. O teste histórico serve para escolher métodos dentro do protocolo, mas a validação prospectiva só existe quando meses novos forem observados. Não há evidência suficiente para afirmar depreciação, probabilidade individual de compra, falha de bateria ou efeito causal de políticas.

## Próxima decisão de dados

Ampliar preços comparáveis por versão, validar presencialmente os pontos de recarga de Bauru e coletar respostas anônimas sobre uso profissional, recarga doméstica e energia solar. Essas três ações fecham as principais lacunas entre hipótese local e evidência mensurada.

_Gerado por `python -m src.analysis.build_executive_summary`; números vêm dos CSVs publicados e podem ser auditados no `data/portfolio/auditoria_exports.csv`._
