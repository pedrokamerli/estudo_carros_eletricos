# Métricas do projeto

Este documento define como responderemos às perguntas antes de coletar os dados. As fórmulas podem ser ajustadas somente se a estrutura real dos arquivos exigir, e toda alteração será registrada.

## Conceitos importantes

- **Emplacamentos:** veículos registrados em um período, normalmente medidos como fluxo mensal ou anual.
- **Frota:** quantidade de veículos registrados em uma localidade em uma data de referência; é um retrato (estoque), não um fluxo anual.
- **Veículos eletrificados:** classificação que será confirmada na documentação de cada fonte. O projeto exibirá separadamente as categorias disponíveis, como elétrico puro (BEV), híbrido (HEV) e híbrido plug-in (PHEV), sem inventar categorias ausentes.

## Indicadores principais

| Indicador | Definição | Fórmula | Fonte prioritária |
| --- | --- | --- | --- |
| Emplacamentos eletrificados | Veículos eletrificados emplacados no período | soma dos emplacamentos no período | ABVE |
| Crescimento anual | Variação dos emplacamentos entre dois anos | `(valor atual - valor anterior) / valor anterior × 100` | ABVE |
| Frota eletrificada | Veículos eletrificados registrados em uma área na data de referência | soma da quantidade por município ou UF | SENATRAN |
| Participação eletrificada na frota | Fração da frota total municipal classificada como eletrificada na mesma competência | `frota eletrificada / frota total municipal × 100` | SENATRAN |
| Crescimento da frota | Variação da frota entre duas datas equivalentes | `(frota atual - frota anterior) / frota anterior × 100` | SENATRAN |
| Penetração eletrificada | Participação dos eletrificados na frota total local | `frota eletrificada / frota total × 100` | SENATRAN |
| Market share de marca | Participação de uma marca no recorte analisado | `veículos da marca / veículos eletrificados × 100` | SENATRAN ou ABVE |
| Market share de modelo | Participação de um modelo no recorte analisado | `veículos do modelo / veículos eletrificados × 100` | SENATRAN ou ABVE |
| Eletrificados por 100 mil habitantes | Intensidade da adoção comparável entre municípios | `frota eletrificada / população × 100.000` | SENATRAN + IBGE |
| PIB per capita aproximado | Produção econômica por habitante usando PIB municipal de 2023 e população do Censo 2022 | `PIB em mil R$ × 1.000 / população` | IBGE |
| Renda domiciliar per capita média | Rendimento nominal mensal domiciliar per capita médio municipal | Valor publicado pelo IBGE, em reais, referência 2022 | IBGE/SIDRA tabela 10295, variável 13431 |

## Regras para responder às perguntas

### Evolução e crescimento

- Perguntas 1 e 2 usarão **emplacamentos**, quando a série da ABVE permitir comparação por período.
- Quando usarmos SENATRAN, o resultado será nomeado como **evolução da frota**, nunca como emplacamentos.
- Só calcularemos crescimento quando os dois períodos forem comparáveis. Se o valor anterior for zero, a taxa percentual será exibida como não calculável, e não como infinito.

### Estados e municípios

- Rankings de quantidade usarão a frota eletrificada.
- Rankings de adoção proporcional usarão penetração eletrificada e eletrificados por 100 mil habitantes.
- A participação na frota usa numerador e denominador do mesmo município e mês. A frota total inclui as categorias veiculares presentes na base SENATRAN de combustível; não deve ser descrita como participação apenas em automóveis de passeio.
- A comparação entre capitais e interior dependerá de uma tabela de referência de capitais, que será adicionada quando coletarmos os dados geográficos.

### Marcas, modelos e categorias

- Sempre indicaremos se o indicador representa **frota** ou **emplacamentos**.
- Marcas e modelos serão padronizados somente após inspecionar os valores originais da SENATRAN.
- Categorias de eletrificação serão mantidas conforme a classificação da fonte, com um dicionário de equivalências documentado posteriormente.

### Potencial de mercado e infraestrutura

- A análise de relação econômica começará com correlações e gráficos entre população, PIB per capita e indicadores de adoção; correlação não será tratada como causalidade.
- O filtro preliminar de oportunidade considera simultaneamente PIB per capita e renda domiciliar per capita no quartil superior da amostra municipal analisada, e veículos eletrificados por 100 mil habitantes no quartil inferior. É exploratório, sensível aos limites da amostra e não estima causalidade nem demanda futura.
- A pergunta sobre recarga será respondida somente após confirmarmos uma base confiável de eletropostos com localização geográfica.

### Previsão

- O alvo será o total de emplacamentos eletrificados por mês ou por ano, conforme a granularidade da série disponível.
- Qualquer previsão será separada da análise histórica e mostrará claramente seu período de treino, período de teste e métricas de erro.

## Critério de qualidade inicial

Todo indicador deve informar: fonte, período de referência, unidade de análise e se representa emplacamentos ou frota.
