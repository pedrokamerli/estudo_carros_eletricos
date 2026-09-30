# Dados de demonstração do portfólio

Os CSVs desta pasta são exports agregados das tabelas Gold do PostgreSQL. Eles permitem que quem visita o repositório explore os principais resultados sem baixar os arquivos brutos da SENATRAN ou instalar o banco.

Os arquivos com `dados_fornecidos` no nome vêm de material recebido pelo autor e ainda não têm origem oficial confirmada. Eles não devem ser apresentados como série oficial da ABVE.

Entre os exports públicos há tabelas de frota e adoção municipal, correlações descritivas com indicadores do IBGE, emplacamentos mensais e rankings de fabricantes da FENABRAVE. Os relatórios FENABRAVE cobrem janeiro/2024 a agosto/2026, no recorte de autos e comerciais leves; as categorias “híbridos” e “elétricos” são próprias da fonte e não devem ser tratadas como equivalentes à classificação ABVE. Janeiro/2024 foi transcrito visualmente de PDF e esse método aparece nas linhas correspondentes.

Os arquivos `backtest_previsao_fenabrave.csv` e `backtest_detalhe_previsao_fenabrave.csv` comparam quatro baselines usando fevereiro/2024 a janeiro/2026 para treino e fevereiro a agosto/2026 para teste. São erros retrospectivos para avaliar métodos — não previsões futuras validadas.

Para coletar as fontes públicas, atualizar o PostgreSQL e recriar os arquivos, execute `src.run_project`. Para exportar novamente apenas os CSVs a partir de um banco já atualizado, execute:

```powershell
.\.venv\Scripts\python.exe -m src.database.export_portfolio_data
```

Cada CSV mantém período e/ou fonte na própria tabela. A documentação em `docs/data_sources.md` descreve as fontes e limitações.
