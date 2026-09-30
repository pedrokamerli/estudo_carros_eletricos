# Análise do Mercado de Veículos Elétricos no Brasil

Este é meu projeto de portfólio para investigar como a mobilidade elétrica está avançando no Brasil, onde a frota se concentra e como a adoção se relaciona com características dos municípios. Eu construo a análise a partir de fontes públicas, registro as limitações de cada dado e organizo o processo para que outra pessoa consiga reproduzi-lo.

## Problema de negócio

Uma empresa que avalia expandir sua atuação em mobilidade elétrica precisa entender onde o mercado já existe, como ele está mudando e quais localidades podem merecer uma análise mais aprofundada. Minha pergunta central é: **como a frota eletrificada evolui no Brasil e onde estão as oportunidades de adoção?**

## O que já construí

- Coleto arquivos mensais de frota por combustível da SENATRAN e preservo os originais na camada Bronze.
- Transformo os dados com Python e Pandas para criar a Silver de veículos eletrificados e a frota total municipal.
- Valido colunas, nulos, duplicidades e quantidades antes de usar os arquivos.
- Integro população do Censo 2022 e PIB municipal de 2023 do IBGE, cruzando município normalizado e UF e mantendo o código IBGE na dimensão resultante.
- Integro também a renda domiciliar per capita média municipal do Censo 2022, mantendo-a separada do PIB.
- Carrego a Silver no PostgreSQL e gero tabelas Gold para estado, município, categoria, capital/interior, evolução, penetração e oportunidade preliminar.
- Mantenho a frota SENATRAN (estoque em uma data) separada dos emplacamentos (fluxo durante um período).

## Recorte e limites atuais

A série mensal disponível neste ambiente vai de **janeiro de 2024 a julho de 2026**, com 31 competências. A SENATRAN ainda não havia publicado agosto e setembro de 2026 na última consulta registrada. O coletor verifica as páginas oficiais e incorpora novos meses quando forem publicados.

O indicador municipal de adoção compara veículos eletrificados com a frota total do município. Também calculo veículos eletrificados por 100 mil habitantes. O PIB é de 2023 e a população é do Censo de 2022; portanto, o PIB per capita combinado é uma aproximação com anos de referência diferentes.

A renda domiciliar per capita vem do Censo 2022 e não é a mesma coisa que PIB per capita. A oportunidade preliminar usa municípios no quartil superior de PIB per capita e renda domiciliar, junto com penetração eletrificada baixa; isso é um filtro exploratório, não uma previsão de demanda.

Os arquivos de marcas e modelos da SENATRAN não informam combustível no mesmo registro. Por isso, não uso essa base para afirmar que um modelo específico é elétrico. O arquivo de mercado que recebi do usuário também está identificado como origem ainda não confirmada e não substitui dados oficiais de emplacamentos.

## Fontes

- [SENATRAN — frota de veículos](https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/estatisticas-frota-de-veiculos-senatran): estoque mensal por localidade e combustível.
- [IBGE/SIDRA — PIB municipal](https://sidra.ibge.gov.br/tabela/6784): PIB corrente municipal, referência 2023.
- [IBGE/SIDRA — população do Censo](https://sidra.ibge.gov.br/tabela/4709): população municipal, referência 2022.
- [IBGE/SIDRA — renda domiciliar per capita](https://sidra.ibge.gov.br/tabela/10295): média municipal do Censo 2022, variável 13431.
- [ABVE Data](https://abve.org.br/abve-data/): série complementar de vendas e eletrificação; integração automatizada ainda em andamento.
- [Open Charge Map](https://openchargemap.org/develop/api): fonte complementar de pontos de recarga; a coleta requer uma chave pessoal gratuita.

O inventário, os métodos de acesso e as limitações estão em [docs/data_sources.md](docs/data_sources.md). As métricas estão em [docs/metrics.md](docs/metrics.md), as perguntas em [docs/business_questions.md](docs/business_questions.md) e o status de cada entrega em [docs/project_status.md](docs/project_status.md).

## Tecnologias

Python, Pandas, PyArrow/Parquet, SQL, PostgreSQL, Git/GitHub e Power BI. Uso cada ferramenta para uma parte concreta do fluxo: Python coleta e transforma, Parquet armazena as camadas locais, PostgreSQL organiza as tabelas analíticas e Power BI será usado para comunicar os resultados. Spark e orquestração em nuvem ficam como evolução caso o volume e a execução recorrente justifiquem essa complexidade.

## Como reproduzir no Windows

1. Clone o repositório e abra a pasta no PyCharm.
2. Crie o ambiente e instale as dependências:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Crie um arquivo `.env` local com os dados de conexão do seu PostgreSQL, seguindo [.env.example](.env.example). Não envie esse arquivo ao GitHub.
4. Crie o banco `ev_brasil_db` no PostgreSQL. O carregador cria os schemas `silver` e `gold`.
5. Com o banco acessível e o `.env` configurado, execute o fluxo público completo:

```powershell
.\.venv\Scripts\python.exe -m src.run_project
```

O comando baixa os meses publicados, registra os meses ainda indisponíveis, recria Bronze/Silver/Gold no PostgreSQL e exporta os CSVs agregados. Os arquivos brutos e Parquet não são versionados; os resultados agregados pequenos ficam em `data/portfolio/` e podem ser recriados pela mesma execução. As fontes opcionais ABVE/Tupi, o arquivo fornecido pelo usuário e Open Charge Map permanecem separadas até sua coleta/classificação ser validada.

## Power BI

Minha etapa visual será conectar o Power BI ao PostgreSQL (`localhost:5432`, banco `ev_brasil_db`) e usar as tabelas do schema `gold`. Vou começar pela evolução mensal, distribuição por estado, penetração municipal e capital versus interior. As tabelas de marcas/modelos devem ser usadas somente depois que a origem e a classificação de eletrificação estiverem validadas.

## Estrutura

```text
data/       Bronze, Silver, Gold e saídas compartilháveis do portfólio
docs/       problema, fontes, métricas, qualidade e status
src/        ingestão, transformações, qualidade e conexão com PostgreSQL
```

## Meu objetivo

Quero que este projeto mostre como conduzo um problema de dados do início à análise: entendo a pergunta, localizo fontes, coleto e valido os dados, documento decisões, modelo indicadores e apresento os resultados. As conclusões finais e o dashboard serão acrescentados depois da análise e da validação dos dados.
