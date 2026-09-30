# Dados de demonstração do portfólio

Os CSVs desta pasta são exports agregados das tabelas Gold do PostgreSQL. Eles permitem que quem visita o repositório explore os principais resultados sem baixar os arquivos brutos da SENATRAN ou instalar o banco.

Os arquivos com `dados_fornecidos` no nome vêm de material recebido pelo autor e ainda não têm origem oficial confirmada. Eles não devem ser apresentados como série oficial da ABVE.

Para coletar as fontes públicas, atualizar o PostgreSQL e recriar os arquivos, execute `src.run_project`. Para exportar novamente apenas os CSVs a partir de um banco já atualizado, execute:

```powershell
.\.venv\Scripts\python.exe -m src.database.export_portfolio_data
```

Cada CSV mantém período e/ou fonte na própria tabela. A documentação em `docs/data_sources.md` descreve as fontes e limitações.
