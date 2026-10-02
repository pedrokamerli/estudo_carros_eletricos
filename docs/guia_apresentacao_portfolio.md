# Guia de apresentação do projeto

## Pitch de 60 segundos

> Construí uma plataforma de dados para entender a expansão dos veículos eletrificados no Brasil entre janeiro de 2024 e agosto de 2026. Separei estoque de frota e fluxo de emplacamentos, automatizei a ingestão de SENATRAN, ABVE, IBGE, Inmetro, FENABRAVE e ANEEL, tratei os dados em camadas Bronze, Silver e Gold e carreguei os resultados no PostgreSQL. O projeto responde onde o mercado cresce, quais municípios e modelos se destacam e quais oportunidades merecem investigação. Escolhi Bauru como estudo de caso, comparando crescimento, modelos, recarga e contexto solar. Também fiz backtests temporais de ML, mas não chamei as projeções de previsão aprovada: preservei as limitações e registrei como a validação futura será feita.

## Ordem sugerida para uma entrevista

1. Comece pelo problema de negócio: onde a mobilidade elétrica está avançando e onde vale investigar expansão.
2. Mostre a arquitetura: Bronze → Silver → Gold → PostgreSQL → Power BI/Streamlit.
3. Explique a decisão metodológica mais importante: frota é estoque; emplacamento é fluxo; não misturei as duas grandezas.
4. Apresente Bauru como hipótese local transformada em evidência: crescimento, comparadores, modelos e recarga.
5. Mostre o ML com honestidade: backtest separado de teste futuro e comparação contra referência persistente.
6. Termine com governança: hashes, auditoria de 89 exports, testes automatizados, CI e limitações documentadas.

## Perguntas técnicas que consigo responder

- **Por que não usar o modelo por município da SENATRAN?** A base de marca/modelo e a base de combustível não têm uma chave comum confiável. Para Bauru, usei a consulta direta do painel ABVE por município e modelo e reconciliei com o agregado.
- **Por que não somar pontos de recarga de fontes diferentes?** Diretórios podem representar o mesmo local e não têm a mesma definição de estação, ponto, conector ou disponibilidade.
- **Por que a geração solar não prova recarga em casa?** A ANEEL registra empreendimentos, não proprietários de veículos nem sessões de carregamento.
- **Por que o ML ainda é experimental?** A série é curta, há mudanças de escopo e a avaliação prospectiva depende de meses que ainda não estavam observados no congelamento.
- **Como você evita vazamento de informação?** O protocolo separa seleção, calibração e teste temporal; projeções prospectivas são congeladas antes do resultado.

## Evidências para mostrar ao recrutador

- [Resumo executivo](resumo_executivo.md)
- [Runbook operacional](runbook_operacional.md)
- [Auditoria dos exports](../data/portfolio/auditoria_exports.csv)
- [Estudo de Bauru e preços](entrega_bauru_precos.md)
- [Pipeline principal](../src/run_project.py)
- [Workflow de CI](../.github/workflows/ci.yml)

O objetivo não é parecer que todas as perguntas já têm uma resposta perfeita. É demonstrar que sei transformar uma pergunta aberta em um pipeline auditável, medir o que os dados realmente sustentam e deixar explícito o próximo experimento.
