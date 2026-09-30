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
- **Limites:** estas categorias são as do boletim FENABRAVE e não equivalem necessariamente a BEV/HEV/PHEV da ABVE. Não combinar as séries sem uma reconciliação documentada. O portal indica que rankings de modelos exigem cadastro/login; este fluxo público não obtém tais dados.

### Painel oficial da ABVE

- **Fonte:** [ABVE Data — Geral](https://abve.org.br/bi-geral/).
- **Formato atual:** painel público Power BI incorporado no site da ABVE.
- **Uso planejado:** validar a série de emplacamentos e categorias divulgadas pela associação; esta métrica continuará separada da frota registrada pela SENATRAN.
- **Limitação atual:** o painel não oferece CSV público direto. A extração programática exigirá um conector específico para Power BI, que será implementado somente quando o acesso aos dados do painel for validado.

## Infraestrutura de recarga — fonte a confirmar

- **Referência regulatória:** [veículos elétricos na ANEEL](https://www.gov.br/aneel/pt-br/assuntos/veiculos-eletricos).
- **Objetivo:** identificar uma fonte aberta com localização de eletropostos para responder à pergunta 14.
- **Status:** **não definida ainda**. O portal de dados abertos da ANEEL é uma fonte oficial importante para o setor elétrico, mas a disponibilidade de uma base nacional de eletropostos precisa ser verificada antes da coleta.

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
| 14: demanda por recarga | Fonte de eletropostos a confirmar | SENATRAN, IBGE |
| 15: previsão de emplacamentos | SENATRAN e/ou ABVE | — |

A série FENABRAVE está implementada como uma fonte independente para as perguntas 1, 2, 8 e 10, com categorias e denominadores próprios; ela não substitui nem é somada à série ABVE.

## Recorte temporal e tamanho

- **Série principal:** arquivos de combustível por UF e município de janeiro de 2024 até o último mês disponível de 2026. São os dados que permitem acompanhar evolução, estados, municípios e capitais versus interior mês a mês.
- **Série complementar:** marca/modelo apenas em meses selecionados. O ZIP de dezembro de 2025 tem cerca de 126 MB e o TXT extraído ocupa cerca de 1,1 GB; baixar todos os meses seria desnecessário para esta etapa.
- **Automação:** o Python vai validar, transformar e consolidar todos os arquivos pequenos de combustível que forem adicionados à Bronze. O arquivo de marca/modelo só será baixado quando for realmente usado.

## Situação das fontes em 30/09/2026

- A página oficial da SENATRAN consultada em 30/09/2026 lista julho de 2026 como a competência mais recente de combustível por UF/município. O coletor procura novos meses em cada execução e grava os meses ausentes no manifesto.
- A API pública CKAN identifica arquivos RENAVAM com marca/modelo e licença indicada como domínio público. Esses registros não trazem combustível na mesma granularidade; não os uso para declarar eletrificação por modelo sem uma classificação independente.
- A ABVE publica boletins mensais com totais, tecnologias e recortes geográficos, além do painel ABVE Data. Os conceitos e a classificação mudam entre períodos; a extração automatizada ainda será conciliada antes de virar uma série única.
- Em setembro de 2026, ABVE/Tupi publicou uma atualização nacional de pontos públicos e semipúblicos referente a agosto de 2026. É uma referência útil para contexto nacional, mas não substitui uma base geolocalizada para estimar demanda por município.
- Os boletins ABVE consultados em 2026 citam dados de infraestrutura da ABVE/Tupi. O Open Charge Map é uma fonte comunitária complementar que requer API key, limite de chamadas e respeito às licenças de cada fornecedor.
- O projeto tem coletor Open Charge Map, mas sua execução ainda depende da chave API local do usuário.

## Licença e publicação

O catálogo CKAN do RENAVAM informa domínio público para o conjunto consultado. Mesmo assim, preservarei a URL, data de coleta, competência e atribuição em cada dado derivado. Para ABVE, FENABRAVE e Open Charge Map, seguirei os termos e requisitos de atribuição da fonte antes de publicar cópias integrais. O GitHub receberá código, documentação e exports agregados pequenos; arquivos brutos pesados serão obtidos pelos coletores.
