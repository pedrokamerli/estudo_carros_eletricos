# Métricas do projeto

Este documento define como responderemos às perguntas antes de coletar os dados. As fórmulas podem ser ajustadas somente se a estrutura real dos arquivos exigir, e toda alteração será registrada.

## Conceitos importantes

- **Emplacamentos:** veículos registrados em um período, normalmente medidos como fluxo mensal ou anual.
- **Frota:** quantidade de veículos registrados em uma localidade em uma data de referência; é um retrato (estoque), não um fluxo anual.
- **Veículos eletrificados:** classificação que será confirmada na documentação de cada fonte. O projeto exibirá separadamente as categorias disponíveis, como elétrico puro (BEV), híbrido (HEV) e híbrido plug-in (PHEV), sem inventar categorias ausentes.

## Indicadores principais

| Indicador | Definição | Fórmula | Fonte prioritária |
| --- | --- | --- | --- |
| Emplacamentos eletrificados ABVE | Veículos eletrificados emplacados no período conforme a classificação da ABVE | soma da série mensal; preservar a classificação de cada período | ABVE |
| Emplacamentos FENABRAVE | Contagens mensais publicadas nas categorias “híbridos” ou “elétricos” para autos e comerciais leves | valor mensal informado no boletim | FENABRAVE |
| Crescimento anual FENABRAVE | Variação em uma categoria FENABRAVE frente ao mesmo mês do ano anterior | `(valor atual - valor no mesmo mês do ano anterior) / valor no mesmo mês do ano anterior × 100` | FENABRAVE |
| Frota eletrificada | Veículos eletrificados registrados em uma área na data de referência | soma da quantidade por município ou UF | SENATRAN |
| Participação eletrificada na frota | Fração da frota total municipal classificada como eletrificada na mesma competência | `frota eletrificada / frota total municipal × 100` | SENATRAN |
| Crescimento da frota | Variação da frota entre duas datas equivalentes | `(frota atual - frota anterior) / frota anterior × 100` | SENATRAN |
| Penetração eletrificada | Participação dos eletrificados na frota total local | `frota eletrificada / frota total × 100` | SENATRAN |
| Market share de marca | Participação de uma marca no recorte analisado | Usar percentual publicado no ranking ou calcular sobre total da mesma categoria, mês, segmento e fonte | FENABRAVE (emplacamentos); SENATRAN/ABVE apenas após validação da classificação |
| Market share de modelo | Participação de um modelo no recorte analisado | `veículos do modelo / veículos eletrificados × 100` | SENATRAN ou ABVE |
| Eletrificados por 100 mil habitantes | Intensidade da adoção comparável entre municípios | `frota eletrificada / população × 100.000` | SENATRAN + IBGE |
| PIB per capita aproximado | Produção econômica por habitante usando PIB municipal de 2023 e população do Censo 2022 | `PIB em mil R$ × 1.000 / população` | IBGE |
| Renda domiciliar per capita média | Rendimento nominal mensal domiciliar per capita médio municipal | Valor publicado pelo IBGE, em reais, referência 2022 | IBGE/SIDRA tabela 10295, variável 13431 |
| Correlação socioeconômica e adoção | Associação entre cada indicador municipal e uma medida de adoção na competência SENATRAN mais recente | Coeficientes Pearson e Spearman em municípios com ambas as variáveis disponíveis | IBGE + SENATRAN |
| Erro de previsão no backtest | Diferença entre a previsão e os emplacamentos observados em meses não usados para ajustar a tendência | MAE, RMSE e MAPE reportados por método, categoria e janela de teste | FENABRAVE |
| Pontos públicos/semipúblicos de recarga | Quantidade publicada de pontos de recarga, sem inferir quantidade de estações únicas | Contagens AC, DC e total; conferir que AC + DC = total | ABVE/Tupi |
| Participação regional da rede de recarga | Percentual da rede nacional atribuído a cada região pela fonte | Percentual publicado; não estimar contagens regionais a partir desse percentual | ABVE/Tupi |
| Participação de município/UF na rede de recarga | Parcela nacional indicada para cada linha nos rankings publicados | Percentual publicado no ranking top 20; não interpretar como cobertura completa de municípios/UFs | ABVE/Tupi |

## Regras para responder às perguntas

### Evolução e crescimento

- Perguntas 1 e 2 poderão usar as séries ABVE e FENABRAVE em visões separadas. Não somar nem emendar as séries sem reconciliar escopo e classificação.
- A FENABRAVE publica neste recorte apenas as categorias amplas “híbridos” e “elétricos”; não inferir equivalência direta com BEV, HEV e PHEV da ABVE.
- O boletim de janeiro/2024 está no segmento “autos”; de fevereiro/2024 em diante, o recorte é “autos e comerciais leves”. Ao comparar meses/anos, filtrar por `segmento_veiculos` para manter o escopo comparável; janeiro/2025 não tem comparação anual compatível com janeiro/2024 nesta série.
- Em agosto/2026, o total FENABRAVE dessas duas categorias (64.055) coincide com o total ABVE de eletrificados (57.386) mais MHEV (6.669). Tratar isso como uma checagem de consistência agregada e uma hipótese de reconciliação, não como prova de equivalência das categorias individuais.
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
- Para recarga, o snapshot ABVE/Tupi permite descrever total, tipo AC/DC, participação regional e principais municípios/UFs. Como é um ranking top 20 sem coordenadas completas, não permite calcular cobertura de todos os municípios, distâncias ou necessidade local de expansão. Não inferir contagens regionais a partir das participações percentuais.

### Previsão

- O alvo será o total de emplacamentos eletrificados por mês ou por ano, conforme a granularidade da série disponível.
- Qualquer previsão será separada da análise histórica e mostrará claramente seu período de treino, período de teste e métricas de erro.
- O backtest atual é exploratório: 24 competências no treino e sete no teste, no modo walk-forward de um passo à frente. Ele compara persistência do último mês, média móvel de 3 meses, sazonal de 12 meses e tendência linear. O resultado do teste não é uma projeção futura e exige validação em novas janelas antes de uso operacional.

## Critério de qualidade inicial

Todo indicador deve informar: fonte, período de referência, unidade de análise e se representa emplacamentos ou frota.
