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

## Infraestrutura de recarga — fonte a confirmar

- **Referência regulatória:** [veículos elétricos na ANEEL](https://www.gov.br/aneel/pt-br/assuntos/veiculos-eletricos).
- **Objetivo:** identificar uma fonte aberta com localização de eletropostos para responder à pergunta 14.
- **Status:** **não definida ainda**. O portal de dados abertos da ANEEL é uma fonte oficial importante para o setor elétrico, mas a disponibilidade de uma base nacional de eletropostos precisa ser verificada antes da coleta.

## Mapa de perguntas e fontes

| Perguntas | Fonte principal | Complemento |
| --- | --- | --- |
| 1–2: evolução e taxa de crescimento | SENATRAN | ABVE |
| 3–8: estados, municípios, penetração e interior | SENATRAN | IBGE |
| 9–10: marcas, modelos e eletrificação | SENATRAN | ABVE |
| 11–13: economia e potencial municipal | IBGE | SENATRAN |
| 14: demanda por recarga | Fonte de eletropostos a confirmar | SENATRAN, IBGE |
| 15: previsão de emplacamentos | SENATRAN e/ou ABVE | — |

## Recorte temporal e tamanho

- **Série principal:** arquivos de combustível por UF e município de janeiro de 2024 até o último mês disponível de 2026. São os dados que permitem acompanhar evolução, estados, municípios e capitais versus interior mês a mês.
- **Série complementar:** marca/modelo apenas em meses selecionados. O ZIP de dezembro de 2025 tem cerca de 126 MB e o TXT extraído ocupa cerca de 1,1 GB; baixar todos os meses seria desnecessário para esta etapa.
- **Automação:** o Python vai validar, transformar e consolidar todos os arquivos pequenos de combustível que forem adicionados à Bronze. O arquivo de marca/modelo só será baixado quando for realmente usado.

## Próxima ação

A próxima fase será escolher um primeiro arquivo da SENATRAN, baixar apenas uma amostra e entender suas colunas. O dado original será preservado na camada `data/bronze`.
