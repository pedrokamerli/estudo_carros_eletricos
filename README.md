# Brazil Electric Vehicles Data Platform

Projeto de portfólio sobre o mercado de veículos elétricos no Brasil. Vamos construir uma plataforma de dados passo a passo, aprendendo cada ferramenta somente quando ela resolver um problema real.

## Problema de negócio

Uma empresa interessada em mobilidade elétrica precisa entender como o mercado brasileiro está evoluindo, onde a adoção é maior e quais regiões podem representar oportunidades futuras.

**Pergunta principal:** como evoluiu a adoção de veículos elétricos no Brasil e quais estados e municípios apresentam maior potencial de crescimento?

As perguntas analíticas que orientarão o projeto estão em [docs/business_questions.md](docs/business_questions.md). As fontes inicialmente selecionadas e seu vínculo com cada pergunta estão em [docs/data_sources.md](docs/data_sources.md). As definições das métricas estão em [docs/metrics.md](docs/metrics.md).

## Etapa atual

**Fase 1 — Setup profissional.** O ambiente Python, o Git, o GitHub e a estrutura inicial estão prontos. Ainda não usamos banco de dados, Spark, Airflow ou outras ferramentas: elas entrarão nas fases adequadas.

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

A pipeline valida a estrutura do arquivo Bronze, identifica a frota eletrificada e cria uma tabela Parquet na camada Silver. Os arquivos de dados continuam locais e não são enviados ao GitHub.

## Regras do projeto

- Não enviar `.venv`, senhas ou arquivos `.env` ao GitHub.
- Preservar os dados originais na camada `data/bronze`.
- Fazer commits pequenos, com mensagens que expliquem a mudança.
