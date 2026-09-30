# Dados de demonstração do portfólio

Os CSVs desta pasta são exports agregados das tabelas Gold do PostgreSQL, exceto `emplacamentos_abve_mensais.csv` e `infraestrutura_recarga_abve_snapshot.csv`, que são snapshots fonte transcritos e versionados. Eles permitem que quem visita o repositório explore os principais resultados sem baixar os arquivos brutos da SENATRAN ou instalar o banco.

Os arquivos com `dados_fornecidos` no nome vêm de material recebido pelo autor e ainda não têm origem oficial confirmada. Eles não devem ser apresentados como série oficial da ABVE.

A avaliação estrutural e a comparação entre os arquivos anuais/mensais estão em [`docs/provided_data_assessment.md`](../../docs/provided_data_assessment.md). Mesmo sem nulos ou IDs repetidos, esses checks não confirmam a origem dos números.

Entre os exports públicos há tabelas de frota e adoção municipal, correlações descritivas com indicadores do IBGE, emplacamentos mensais e rankings de fabricantes da FENABRAVE. Os relatórios FENABRAVE cobrem janeiro/2024 a agosto/2026, no recorte de autos e comerciais leves; as categorias “híbridos” e “elétricos” são próprias da fonte e não devem ser tratadas como equivalentes à classificação ABVE. Janeiro/2024 foi transcrito visualmente de PDF e esse método aparece nas linhas correspondentes.

`emplacamentos_abve_mensais.csv` é um snapshot agregado transcrito do painel público ABVE Data em 30/09/2026. Traz total mensal de jan/2024 a ago/2026 e as categorias BEV/PHEV/HEV/HEV Flex de jan/2025 em diante. A regra mudou em jan/2025; a coluna `regra_classificacao` identifica essa quebra. Em ago/2025, o total do histórico e a soma da tabela tecnológica diferem em 16 unidades; as colunas mantêm os dois números e a divergência. Também há diferenças entre os acumulados jan–ago do painel e os citados em notícias ABVE: 16 unidades em 2025 e 6 em 2026. Mantive os valores do painel no arquivo e registrei as discrepâncias; não forcei conciliação. Setembro/2026 não estava publicado como mês fechado na data da captura. O snapshot passa por validações Silver, é carregado em `silver.abve_emplacamentos_mensais` e origina `gold.emplacamentos_abve_mensais`; ainda não há atualização automática da fonte. `emplacamentos_abve_mensais_gold.csv` é o export preparado para análise no Power BI. Comparações de crescimento respeitam a regra de classificação e não atravessam a mudança metodológica.

`infraestrutura_recarga_abve_snapshot.csv` registra a captura do painel público ABVE/Tupi em 30/09/2026, com referência agosto/2026: total nacional AC/DC, participações regionais e rankings top 20 de municípios e UFs. A validação preserva explicitamente o escopo top 20; não é o inventário completo dos pontos, não traz coordenadas e não sustenta cálculos de cobertura para todos os municípios. Os dados são validados em Silver, carregados em `silver.abve_infraestrutura_recarga` e modelados em `gold.infraestrutura_recarga_abve`; `infraestrutura_recarga_abve_gold.csv` é o export para exploração no Power BI.

Os arquivos `backtest_previsao_fenabrave.csv` e `backtest_detalhe_previsao_fenabrave.csv` comparam quatro baselines usando fevereiro/2024 a janeiro/2026 para treino e fevereiro a agosto/2026 para teste. São erros retrospectivos para avaliar métodos — não previsões futuras validadas.

Para coletar as fontes públicas, atualizar o PostgreSQL e recriar os arquivos, execute `src.run_project`. Para exportar novamente apenas os CSVs a partir de um banco já atualizado, execute:

```powershell
.\.venv\Scripts\python.exe -m src.database.export_portfolio_data
```

Cada CSV mantém período e/ou fonte na própria tabela. A documentação em `docs/data_sources.md` descreve as fontes e limitações.
