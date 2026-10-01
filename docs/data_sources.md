# Plano de fontes de dados

Este documento define **onde procurar os dados** antes de iniciarmos qualquer download. A escolha prioriza fontes públicas e oficiais.

## Fonte principal — SENATRAN

- **Fonte:** [Estatísticas da frota de veículos](https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/estatisticas-frota-de-veiculos-senatran).
- **O que oferece:** arquivos históricos e arquivos por UF e município; os arquivos atuais incluem recortes por combustível, marca e modelo.
- **Uso no projeto:** medir o tamanho da frota eletrificada por localidade, tipo de combustível, marca e modelo.
- **Perguntas atendidas:** 1 a 10.
- **Atenção:** a primeira etapa de coleta validará quais anos têm o mesmo nível de detalhe e como os combustíveis são nomeados em cada arquivo.

### Marcas e modelos

- **Recurso:** arquivo por UF, município, marca e modelo do mesmo catálogo RENAVAM/SENATRAN.
- **Coleta automatizada:** `src/ingestion/download_senatran_brand_model.py` consulta a API CKAN do portal, localiza um mês escolhido, baixa o ZIP em blocos e valida o tamanho antes de substituir o arquivo local.
- **Uso no escopo 2024–2026:** esta é uma fonte **sob demanda**. Cada mês é grande; por isso não faremos 36 downloads. Usaremos apenas recortes de referência quando a pergunta de marca/modelo estiver pronta para análise.
- **Limitação conhecida:** o catálogo oferece uma API para metadados e recursos, mas não uma consulta pronta por marca ou modelo. Por isso, a análise será feita a partir do arquivo bruto baixado.
- **Limitação analítica:** este arquivo não tem a coluna de combustível. Ele não pode, sozinho, provar quais marcas e modelos são eletrificados. O cruzamento de “marca/modelo eletrificado” dependerá de uma tabela adicional de classificação de motorização.

## Contexto econômico e demográfico — IBGE

- **PIB municipal:** [PIB dos Municípios](https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produto-interno-bruto-dos-municipios.html) e [tabela 6784 do SIDRA](https://sidra.ibge.gov.br/tabela/6784).
- **População:** estimativas e tabelas municipais do IBGE/SIDRA.
- **Dados já coletados:** PIB municipal de 2023 (SIDRA 5938, variável 37), população do Censo 2022 (4709, variável 93) e rendimento domiciliar per capita médio do Censo 2022 (10295, variável 13431).
- **O que oferece:** população, PIB total e PIB per capita por município.
- **Uso no projeto:** calcular taxas por habitante e investigar a relação entre características econômicas e adoção de veículos eletrificados.
- **Perguntas atendidas:** 6, 11, 12 e 13.
- **Atenção:** PIB municipal possui defasagem de divulgação; o ano de referência será registrado em toda análise.

## Mercado e categorias de eletrificação — ABVE

- **Fonte:** [Associação Brasileira do Veículo Elétrico](https://abve.org.br/).
- **O que oferece:** boletins e divulgações mensais sobre emplacamentos de veículos eletrificados, participação de mercado e categorias como BEV, híbrido e híbrido plug-in.
- **Uso no projeto:** complementar a análise de emplacamentos e classificar os tipos de eletrificação.
- **Perguntas atendidas:** 1, 2 e 10.
- **Atenção:** antes de automatizar, verificaremos se a série histórica está disponível em formato reaproveitável e se a licença permite o uso pretendido.

## Emplacamentos e fabricantes — FENABRAVE

- **Fonte:** [Informativos mensais e área de imprensa](https://www.fenabrave.org.br/portalv2/home/imprensa).
- **Dados estruturados neste projeto:** categorias mensais “híbridos” e “elétricos”, acumulados publicados no relatório e rankings de 15 fabricantes por categoria. O relatório de janeiro/2024 é somente de autos; fevereiro/2024 a agosto/2026 é autos e comerciais leves, e o campo `segmento_veiculos` mantém essa diferença explícita.
- **Período coletado:** janeiro/2024 a agosto/2026 (32 relatórios públicos). Setembro/2026 ainda não estava disponível no portal consultado em 30/09/2026.
- **Processamento:** `src/ingestion/download_fenabrave_monthly_reports.py` coleta PDFs; `src/transformation/fenabrave_reports_to_silver.py` valida os totais e transforma o texto em Parquet; `src/database/load_fenabrave_to_postgres.py` carrega tabelas Silver dedicadas.
- **Rastreabilidade:** cada registro conserva URL, página e método. Janeiro/2024 usa transcrição visual manual conferida na [página 20 do PDF original](https://www.fenabrave.org.br/portal/files/2024_01_02.pdf), pois a fonte do arquivo impede extração Unicode confiável.
- **Limites:** estas categorias são as do boletim FENABRAVE e não equivalem necessariamente a BEV/HEV/PHEV da ABVE. Não combinar as séries sem uma reconciliação documentada. Rankings gerais de modelos dos boletins não trazem classificação de motorização suficiente para identificar todos os eletrificados; este fluxo ainda não produz ranking validado de modelos eletrificados.

### Painel oficial da ABVE

- **Fontes:** [ABVE Data](https://abve.org.br/abve-data/), painel [Geral](https://abve.org.br/abve-data/bi-geral/) e painel de [Geografia da Eletromobilidade](https://abve.org.br/abve-data/bi-geografia-da-eletromobilidade/).
- **Formato atual:** relatórios Power BI públicos incorporados ao site. Não encontrei link de exportação tabular direta. Li as tabelas acessíveis do painel e registrei um snapshot agregado verificável em [`data/portfolio/emplacamentos_abve_mensais.csv`](../data/portfolio/emplacamentos_abve_mensais.csv); essa captura inicial foi transcrita do visual e não é uma coleta automática recorrente.
- **Uso:** validar separadamente a série de emplacamentos e categorias divulgadas pela associação; não misturar com a frota registrada pela SENATRAN ou com as categorias da FENABRAVE.
- **Quebra metodológica:** a ABVE declara uma classificação revisada a partir de janeiro/2025. Na definição vigente, eletrificados leves incluem BEV, PHEV, HEV e HEV Flex, mas não MHEV. Em alguns informes de 2024, MHEV aparece incluído em totais; é preciso reconstruir um recorte comparável antes de calcular crescimento entre períodos.
- **Cobertura verificada:** o snapshot contém totais mensais de janeiro/2024 a agosto/2026 e tecnologias de janeiro/2025 a agosto/2026. Setembro ainda não tinha fechamento mensal publicado em 30/09/2026. A soma dos totais mensais do painel para jan–ago excede em 16 unidades o acumulado citado em notícia ABVE de 2025 e em 6 unidades o acumulado publicado para 2026; em ago/2025, a soma das quatro tecnologias fica 16 abaixo do total mensal do painel. Preservei esses números separados para conferência. A atualização recorrente continua pendente de um método estável para extrair o painel.

## Modelos em notícias e publicações

Os rankings documentais de modelos são descritos em [`docs/modelos_por_noticias.md`](modelos_por_noticias.md): quatro publicações primárias ABVE e três reportagens Webmotors, sete recortes/períodos e 65 registros. O catálogo `data/portfolio/fontes_rankings_modelos_noticias.csv` conserva URL, publicador, fornecedor atribuído, data, escopo, granularidade e tipo de período. A Silver/Gold valida a transcrição e mantém quantidades ausentes; isso não confirma uma série mensal completa nem autoriza classificar outras versões a partir do nome geral de um modelo.

## Infraestrutura de recarga — ABVE/Tupi

- **Fonte:** [painel público de eletropostos da ABVE](https://abve.org.br/abve-data/bi-eletropostos/) e [publicação ABVE/Tupi sobre a rede](https://abve.org.br/recarga-rapida-dc-quase-triplica-em-12-meses-e-ja-responde-por-38-da-rede-brasileira/).
- **Referência:** agosto/2026; publicação de 28/09/2026 e captura do painel em 30/09/2026.
- **O que foi integrado:** total nacional (AC/DC), participação percentual das cinco regiões e rankings top 20 de municípios e UFs, em `data/portfolio/infraestrutura_recarga_abve_snapshot.csv`.
- **Pipeline:** `src/transformation/abve_charging_snapshot_to_silver.py` valida escopo, totais, percentuais, datas e metadados; `src/database/load_abve_charging_to_postgres.py` carrega Silver; `src/database/build_gold_tables.py` produz `gold.infraestrutura_recarga_abve`; o export é `data/portfolio/infraestrutura_recarga_abve_gold.csv`.
- **Limitação:** os rankings são parciais; o painel informa que a rede alcança 1.911 municípios, mas a captura integrada não contém a lista completa nem coordenadas de todos os pontos. Participações regionais não foram convertidas em contagens. Portanto, esta entrega permite comparar a distribuição publicada e os principais polos, mas não calcular cobertura municipal completa, distância até carregadores ou um mapa de todos os eletropostos.
- **Complemento opcional:** [Open Charge Map](https://www.openchargemap.org/develop/api) oferece API com coordenadas, mas exige chave própria e validação de licença/cobertura dos registros antes de uso analítico.

## Arquivos recebidos para exploração — origem não confirmada

- Recebi os arquivos `historico_vendas_ev_brasil.csv`, `vendas_ev_brasil_mes_a_mes.csv` e `dataset_mercado_ev_brasil.csv`.
- Eles não informam fonte, URL, licença ou método de compilação. Além disso, os valores anuais e mensais para modelos comuns não fecham em alguns casos. O arquivo municipal chama população, PIB e frota de estimativas sem registrar ano-base.
- Mantenho-os isolados e marcados `origem_oficial_confirmada = false`; não os uso para calcular resultados oficiais de mercado. A auditoria detalhada fica em [`docs/provided_data_assessment.md`](provided_data_assessment.md).

## Mapa de perguntas e fontes

| Perguntas | Fonte principal | Complemento |
| --- | --- | --- |
| 1–2: evolução e taxa de crescimento | SENATRAN | ABVE |
| 3–8: estados, municípios, penetração e interior | SENATRAN | IBGE |
| 9–10: marcas, modelos e eletrificação | SENATRAN | ABVE |
| 11–13: economia e potencial municipal | IBGE | SENATRAN |
| 14: demanda por recarga | ABVE/Tupi (total nacional, participação regional e top 20 municípios/UFs) | SENATRAN, IBGE; cobertura completa depende de base geográfica adicional |
| 15: previsão de emplacamentos | SENATRAN e/ou ABVE | — |

A série FENABRAVE está implementada como uma fonte independente para as perguntas 1, 2, 8 e 10, com categorias e denominadores próprios; ela não substitui nem é somada à série ABVE.

## Recorte temporal e tamanho

- **Série principal:** arquivos de combustível por UF e município de janeiro de 2024 até o último mês disponível de 2026. São os dados que permitem acompanhar evolução, estados, municípios e capitais versus interior mês a mês.
- **Série complementar:** marca/modelo apenas em meses selecionados. O ZIP de dezembro de 2025 tem cerca de 126 MB e o TXT extraído ocupa cerca de 1,1 GB; baixar todos os meses seria desnecessário para esta etapa.
- **Automação:** o Python vai validar, transformar e consolidar todos os arquivos pequenos de combustível que forem adicionados à Bronze. O arquivo de marca/modelo só será baixado quando for realmente usado.

## Situação das fontes em 30/09/2026

- A página oficial da SENATRAN consultada em 30/09/2026 lista julho de 2026 como a competência mais recente de combustível por UF/município. O coletor procura novos meses em cada execução e grava os meses ausentes no manifesto.
- A API pública CKAN identifica arquivos RENAVAM com marca/modelo e licença indicada como domínio público. Esses registros não trazem combustível na mesma granularidade; não os uso para declarar eletrificação por modelo sem uma classificação independente.
- A ABVE publica boletins mensais com totais, tecnologias e recortes geográficos, além de painéis públicos Power BI incorporados. A classificação mudou em janeiro/2025; automatizar a captura do texto ou dos visuais sem preservar essa quebra poderia criar uma série enganosa. Setembro/2026 ainda não tinha total mensal fechado publicado em 30/09/2026.
- Em setembro de 2026, ABVE/Tupi publicou uma atualização nacional de pontos públicos e semipúblicos referente a agosto de 2026. É uma referência útil para contexto nacional, mas não substitui uma base geolocalizada para estimar demanda por município.
- Os boletins ABVE consultados em 2026 citam dados de infraestrutura da ABVE/Tupi. O Open Charge Map é uma fonte comunitária complementar que requer API key, limite de chamadas e respeito às licenças de cada fornecedor.
- O projeto tem coletor Open Charge Map, mas sua execução ainda depende da chave API local do usuário.

## Licença e publicação

O catálogo CKAN do RENAVAM informa domínio público para o conjunto consultado. Mesmo assim, preservarei a URL, data de coleta, competência e atribuição em cada dado derivado. Para ABVE, FENABRAVE e Open Charge Map, seguirei os termos e requisitos de atribuição da fonte antes de publicar cópias integrais. O GitHub receberá código, documentação e exports agregados pequenos; arquivos brutos pesados serão obtidos pelos coletores.
