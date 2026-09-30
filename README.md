# Brazil Electric Vehicles Data Platform

Projeto de portfólio sobre o mercado de veículos elétricos no Brasil. Vamos construir uma plataforma de dados passo a passo, aprendendo cada ferramenta somente quando ela resolver um problema real.

## Problema de negócio

Uma empresa interessada em mobilidade elétrica precisa entender como o mercado brasileiro está evoluindo, onde a adoção é maior e quais regiões podem representar oportunidades futuras.

**Pergunta principal:** como evoluiu a adoção de veículos elétricos no Brasil e quais estados e municípios apresentam maior potencial de crescimento?

As perguntas analíticas que orientarão o projeto estão em [docs/business_questions.md](docs/business_questions.md). As fontes inicialmente selecionadas e seu vínculo com cada pergunta estão em [docs/data_sources.md](docs/data_sources.md). As definições das métricas estão em [docs/metrics.md](docs/metrics.md). O recorte de coleta está em [docs/collection_scope.md](docs/collection_scope.md).

## Etapa atual

**Fase 2 — Coleta e tratamento local.** A pipeline identifica automaticamente todos os arquivos mensais de combustível de 2024 a 2026 que estiverem na Bronze. Ainda não usamos banco de dados, Spark, Airflow ou outras ferramentas: elas entrarão nas fases adequadas.

## Estrutura inicial

```text
Projeto Portfólio/
├── data/
│   ├── bronze/       # Dados recebidos, preservados como chegaram
│   ├── silver/       # Dados limpos e padronizados (futuro)
│   └── gold/         # Dados prontos para análise (futuro)
├── dashboard/        # Materiais do dashboard (futuro)
├── docs/             # Documentação e decisões do projeto
├── notebooks/        # Explorações e estudos
├── src/
│   ├── ingestion/    # Coleta de dados (futuro)
│   ├── transformation/# Transformações (futuro)
│   ├── quality/      # Validações de qualidade (futuro)
│   └── utils/        # Funções reutilizáveis
├── tests/            # Testes automatizados
├── .gitignore        # Arquivos que o Git não deve enviar
└── requirements.txt  # Bibliotecas Python do projeto
```

## Como abrir no PyCharm

Abra a pasta `D:\Projeto Portfólio` e escolha o interpretador localizado em `.venv`.

No terminal do PyCharm, ative o ambiente com:

```powershell
.\.venv\Scripts\Activate.ps1
```

As bibliotecas serão registradas em `requirements.txt` quando começarmos a usá-las.

## Executar a primeira pipeline

Com o arquivo bruto da SENATRAN salvo em `data/bronze/senatran/`, execute:

```powershell
.\.venv\Scripts\python.exe -m src.run_pipeline
```

A pipeline valida a estrutura de cada arquivo Bronze, identifica a frota eletrificada e cria uma única tabela Parquet na camada Silver com todos os meses disponíveis. Os arquivos de dados continuam locais e não são enviados ao GitHub.

O relatório de qualidade da fonte é criado em `data/quality/senatran/` a cada execução.

## Coletar a série oficial da SENATRAN

Para baixar os arquivos de combustível publicados de janeiro de 2024 até setembro de 2026, execute:

```powershell
.\.venv\Scripts\python.exe -m src.ingestion.download_senatran_fuel_history
```

O script consulta as páginas oficiais da SENATRAN a cada execução. Quando um mês ainda não foi publicado, ele registra a indisponibilidade no manifesto local em vez de criar dados fictícios.

## Gerar as tabelas Gold

Depois de gerar as tabelas Silver, execute o comando abaixo para criar as respostas analíticas de frota por estado, município, tipo de localidade e categoria de eletrificação:

```powershell
.\.venv\Scripts\python.exe -m src.transformation.silver_to_gold
```

O dataset mensal de mercado fornecido pelo usuário deve ser transformado antes da Gold de ranking de marcas e modelos:

```powershell
.\.venv\Scripts\python.exe -m src.transformation.market_dataset_to_silver --input "D:\estudos ciencia de dados\estudo mercaod de carros elétricos\dataset_mercado_ev_brasil.csv"
```

## Coletar indicadores municipais do IBGE

Para baixar PIB municipal de 2023 e população do Censo de 2022, execute os comandos abaixo. Os anos ficam registrados no nome das colunas para não confundir o contexto econômico com o período da frota.

```powershell
.\.venv\Scripts\python.exe -m src.ingestion.download_ibge_municipal_indicators
.\.venv\Scripts\python.exe -m src.transformation.ibge_bronze_to_silver
.\.venv\Scripts\python.exe -m src.transformation.silver_to_gold
```

## Coletar eletropostos

Crie gratuitamente uma chave de API na [Open Charge Map](https://openchargemap.org/develop/api). No terminal do PyCharm, informe a chave apenas para a sessão atual e execute a coleta:

```powershell
$env:OCM_API_KEY = "cole_a_sua_chave_aqui"
.\.venv\Scripts\python.exe -m src.ingestion.download_open_charge_map
```

A chave não é salva em arquivos do projeto e não deve ser enviada ao GitHub.

## Carregar a Silver no PostgreSQL

Depois de criar as tabelas `silver` no pgAdmin, execute:

```powershell
.\.venv\Scripts\python.exe -m src.database.load_silver_to_postgres
```

O carregador evita duplicidade: se uma tabela já estiver preenchida, ele não insere novamente e apenas valida a quantidade de linhas e veículos.

## Regras do projeto

- Não enviar `.venv`, senhas ou arquivos `.env` ao GitHub.
- Preservar os dados originais na camada `data/bronze`.
- Fazer commits pequenos, com mensagens que expliquem a mudança.
