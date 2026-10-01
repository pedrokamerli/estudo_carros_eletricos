# Meu modelo dimensional para o Power BI

Preparei um schema `bi` no PostgreSQL para conectar o dashboard sem depender de relações improvisadas entre exports agregados. A estrutura segue a [orientação de esquema estrela da Microsoft](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema): dimensões filtram e fatos guardam medidas em uma granularidade definida. As tabelas anteriores da Gold continuam disponíveis para exploração, rankings, ML e conferências.

## Tabelas e unidade de cada linha

| Tabela | Chave e granularidade | Conteúdo atual |
| --- | --- | --- |
| `bi.dim_data` | Uma linha por dia; chave `data` | 1.096 dias, anos completos 2024–2026 |
| `bi.dim_municipio` | Uma linha por par UF/nome original observado; chave técnica `municipio_id` | 5.576 localidades do histórico, 5.528 associadas ao IBGE |
| `bi.fato_frota_municipal` | Competência mensal + localidade | 178.357 linhas; frota total e eletrificada na mesma competência |
| `bi.fato_emplacamentos_plugin_abve` | Mês + tecnologia BEV/PHEV | 64 linhas, 32 meses por tecnologia |
| `bi.fato_emplacamentos_fenabrave` | Mês + categoria + segmento | 64 linhas; janeiro/2024 cobre apenas autos |

5.576 é o número de rótulos de localidade do histórico, **não** a contagem de municípios oficiais brasileiros. Há dois rótulos históricos além das 5.574 localidades da competência mais recente. Não invento códigos IBGE para as 48 localidades sem associação. A chave técnica é MD5 de um array JSON com UF/nome original, nunca um código IBGE fictício ou a posição da linha. A unicidade dos pares e chaves é imposta pelo banco.

A dimensão usa o cruzamento municipal já revisado na última competência: população/renda do Censo 2022, PIB per capita aproximado a partir do PIB 2023 e população 2022, e filtro exploratório de oportunidade com frota ago/2026. A referência da frota dos indicadores fica em `data_referencia_indicadores_frota`. São atributos de referência/snapshot, não uma dimensão SCD tipo 2 nem um histórico anual de renda ou oportunidade. Não treino modelos temporais tratando esses atributos como se fossem observações mensais publicadas na época.

## Relações que configuro no Desktop

| Lado 1 | Lado muitos | Direção |
| --- | --- | --- |
| `dim_data[data]` | `fato_frota_municipal[data_referencia]` | Única: dimensão → fato |
| `dim_municipio[municipio_id]` | `fato_frota_municipal[municipio_id]` | Única: dimensão → fato |
| `dim_data[data]` | `fato_emplacamentos_plugin_abve[data_referencia]` | Única: dimensão → fato |
| `dim_data[data]` | `fato_emplacamentos_fenabrave[data_referencia]` | Única: dimensão → fato |

Não relaciono fato com fato, não habilito muitos-para-muitos e não uso filtro bidirecional. A dimensão municipal só filtra a frota; ABVE/FENABRAVE destas tabelas são totais nacionais e não permitem um filtro verdadeiro por UF. Deixo filtros de localidade nas páginas de frota, sem anunciar um gráfico nacional como se fosse estadual.

No Power Query, verifico `data`/`data_referencia` como **Data**, chaves como **Texto**, códigos IBGE como **Texto**, quantidades como inteiros e booleanos como lógico. Ordeno `ano_mes` por `ano_mes_ordem`. Marco `dim_data` como tabela de datas pela coluna `data`, conforme a [orientação de calendário da Microsoft](https://learn.microsoft.com/en-us/power-bi/guidance/model-date-tables). O calendário é diário para inteligência temporal; fatos só têm o primeiro dia do mês. Mostro eixo mensal e não um gráfico que sugira vendas diárias.

## Como uso as medidas

O arquivo `power_bi/medidas_base.dax` contém medidas iniciais para copiar **uma por vez**, com tabelas renomeadas aos nomes usados no código. São instruções de implementação; não foram executadas em um PBIX neste ambiente. Confiro os resultados no Desktop antes de publicar.

- Frota total/eletrificada: seleciono a última competência disponível dentro do contexto de datas, sem somar estoques mensais. Todas as localidades do visual usam a mesma competência. O mês futuro sem observação fica em branco.
- Participação eletrificada: divido somas do numerador e denominador na mesma competência. Não somo percentuais municipais nem faço média simples de percentuais.
- Indicador por habitante: excluo do numerador localidades sem população conhecida e uso a mesma amostra no denominador. A população 2022 entra uma vez por localidade, não por linha mensal.
- Emplacamentos: somo meses dentro da mesma fonte/categoria/segmento. O fato ABVE contém **somente plug-in BEV/PHEV**. FENABRAVE tem suas próprias categorias e diferenças de segmento. Não somo as fontes.
- Crescimento anual: comparo a seleção com o período equivalente usando a tabela de datas. Não comparo jan–ago/2026 com todo o ano de 2025. Período sem base anterior ou sem fechamento fica em branco.

Em um cartão nacional sem filtros geográficos, ago/2026 deve mostrar frota eletrificada **1.266.671**, total de todas as motorizações **135.907.590** e parcela eletrificada sem UF **148.204**. Um filtro apenas para UF conhecida deve mostrar **1.118.467** eletrificados. Esses são estoques SENATRAN na definição de combustíveis do projeto, não veículos BEV nem vendas mensais de leves.

## Reproduzo e valido

```powershell
.\.venv\Scripts\python.exe -m src.database.build_bi_model
.\.venv\Scripts\python.exe -m src.database.export_portfolio_data
```

Preciso das tabelas Silver/Gold já atualizadas. O SQL está em `sql/modelo_dimensional_bi.sql`; executo pelo módulo Python, que prepara o mapa temporário de capitais/siglas antes do SQL. A atualização inteira usa uma transação: uma falha de chave, carga ou auditoria preserva o modelo anterior. Chaves primárias, estrangeiras e restrições impedem referências órfãs, duplicidade na granularidade e quantidades inválidas.

O módulo também confere oito invariantes no banco real: conservação da frota total/eletrificada por mês, preservação das duas fontes de emplacamentos por chave, universo municipal, calendário diário contínuo, primeiro dia nas fatos mensais e frota sem UF. A execução passou nas oito verificações; o relatório local fica em `data/quality/modelo_bi.json`. A etapa faz parte de `src.run_project`. Os cinco exports `bi_*.csv` permitem reproduzir as relações sem acesso ao meu banco local; ao importá-los no Desktop removo o prefixo `bi_` dos nomes das tabelas.
