# Dados de demonstração do portfólio

Os CSVs desta pasta são exports das tabelas Gold do PostgreSQL, exceto `emplacamentos_abve_mensais.csv`, `infraestrutura_recarga_abve_snapshot.csv`, `rankings_modelos_noticias_snapshot.csv` e `fontes_rankings_modelos_noticias.csv`, que são snapshots/catálogos de fontes transcritos e versionados. Eles permitem que quem visita o repositório explore os principais resultados sem baixar os arquivos brutos da SENATRAN ou instalar o banco.

Os arquivos com `dados_fornecidos` no nome vêm de material recebido pelo autor e ainda não têm origem oficial confirmada. Eles não devem ser apresentados como série oficial da ABVE.

Os arquivos de `modelos_noticias` são outra base: 65 registros documentais em sete listas publicadas pela ABVE ou Webmotors, com 56 quantidades e nove desconhecidas. Os exports Gold de ranking e cobertura preservam fonte, granularidade e intervalo; não representam todos os modelos nem uma série mensal completa. Para um ranking, filtro uma `fonte_id`; não somo listas acumuladas sobrepostas. Veja [`docs/modelos_por_noticias.md`](../../docs/modelos_por_noticias.md).

A avaliação estrutural e a comparação entre os arquivos anuais/mensais estão em [`docs/provided_data_assessment.md`](../../docs/provided_data_assessment.md). Mesmo sem nulos ou IDs repetidos, esses checks não confirmam a origem dos números.

Entre os exports públicos há tabelas de frota e adoção municipal, correlações descritivas com indicadores do IBGE, emplacamentos mensais e rankings de fabricantes da FENABRAVE. Os relatórios FENABRAVE cobrem janeiro/2024 a agosto/2026, no recorte de autos e comerciais leves; as categorias “híbridos” e “elétricos” são próprias da fonte e não devem ser tratadas como equivalentes à classificação ABVE. Janeiro/2024 foi transcrito visualmente de PDF e esse método aparece nas linhas correspondentes.

`emplacamentos_abve_mensais.csv` é um snapshot agregado transcrito do painel público ABVE Data em 30/09/2026. Traz total mensal de jan/2024 a ago/2026 e as categorias BEV/PHEV/HEV/HEV Flex de jan/2025 em diante. A regra mudou em jan/2025; a coluna `regra_classificacao` identifica essa quebra. Em ago/2025, o total do histórico e a soma da tabela tecnológica diferem em 16 unidades; as colunas mantêm os dois números e a divergência. Também há diferenças entre os acumulados jan–ago do painel e os citados em notícias ABVE: 16 unidades em 2025 e 6 em 2026. Mantive os valores do painel no arquivo e registrei as discrepâncias; não forcei conciliação. Setembro/2026 não estava publicado como mês fechado na data da captura. O snapshot passa por validações Silver, é carregado em `silver.abve_emplacamentos_mensais` e origina `gold.emplacamentos_abve_mensais`; ainda não há atualização automática da fonte. `emplacamentos_abve_mensais_gold.csv` é o export preparado para análise no Power BI. Comparações de crescimento respeitam a regra de classificação e não atravessam a mudança metodológica.

`infraestrutura_recarga_abve_snapshot.csv` registra a captura do painel público ABVE/Tupi em 30/09/2026, com referência agosto/2026: total nacional AC/DC, participações regionais e rankings top 20 de municípios e UFs. A validação preserva explicitamente o escopo top 20; não é o inventário completo dos pontos, não traz coordenadas e não sustenta cálculos de cobertura para todos os municípios. Os dados são validados em Silver, carregados em `silver.abve_infraestrutura_recarga` e modelados em `gold.infraestrutura_recarga_abve`; `infraestrutura_recarga_abve_gold.csv` é o export para exploração no Power BI.

Os arquivos `backtest_previsao_fenabrave.csv` e `backtest_detalhe_previsao_fenabrave.csv` comparam quatro baselines usando fevereiro/2024 a janeiro/2026 para treino e fevereiro a agosto/2026 para teste. São erros retrospectivos para avaliar métodos — não previsões futuras validadas.

O experimento adicional de ML tem quatro arquivos `ml_*.csv`: detalhe das previsões retrospectivas, métricas por etapa/horizonte, escolha feita na validação e projeções experimentais para os próximos três meses. Compara Ridge e Random Forest com referências simples; escolhe antes do teste e preserva o resultado mesmo quando perde para a referência. Os CSVs conservam fonte, segmento, versão do scikit-learn e hash da Silver. Não misturo validação com teste nem somo diferentes métodos/horizontes como se fossem vendas. Os detalhes e resultados estão em [`docs/machine_learning.md`](../../docs/machine_learning.md).

`sensibilidade_oportunidade.csv` compara nove combinações de percentis e sua sobreposição com a regra original, na mesma amostra municipal. A base de penetração inclui localidades sem registros eletrificados, presentes na frota total da mesma competência. Na atualização de ago/2026, as correlações e a lista de oportunidade foram recalculadas: 5.528 localidades associadas ao IBGE, 17 candidatos no corte original e 7–30 nos cenários. São filtros exploratórios, não demanda futura estimada.

`evolucao_frota_nacional.csv` inclui todos os registros eletrificados da Silver, inclusive UF desconhecida, e separa `total_veiculos_uf_informada` de `total_veiculos_sem_uf`. Rankings geográficos excluem a UF desconhecida; por isso sua soma não equivale ao total nacional sem acrescentar essa parcela. Na planilha Bronze de ago/2026, uma última linha traz o total nacional de todas as motorizações: só a separo após conciliação com o detalhe para evitar duplicação.

Para coletar as fontes públicas, atualizar o PostgreSQL e recriar os arquivos, execute `src.run_project`. Para exportar novamente apenas os CSVs a partir de um banco já atualizado, execute:

```powershell
.\.venv\Scripts\python.exe -m src.database.export_portfolio_data
```

Cada CSV mantém período e/ou fonte na própria tabela. A documentação em `docs/data_sources.md` descreve as fontes e limitações.

`recarga_osm.csv` é uma camada separada de dados OpenStreetMap sob ODbL: 392 objetos mapeados, não 392 carregadores. Preservo atribuição **© OpenStreetMap contributors** e link da licença por registro e no dashboard. A cobertura é comunitária/incompleta e o acesso frequentemente não está informado. Não somo seus objetos com os pontos ABVE/Tupi nem interpreto ausência no mapa como ausência de infraestrutura. Veja [`docs/recarga_openstreetmap.md`](../../docs/recarga_openstreetmap.md) para uso, reprodução e licença.

`abve_plugin_2024_fontes.csv` contém minha transcrição revisada dos valores mensais BEV/PHEV em publicações primárias ABVE, não um export do banco. `abve_plugin_mensais.csv` é a série integrada de 32 meses por tecnologia, disponível também na Gold. Os quatro arquivos `ml_abve_*.csv` avaliam esse alvo separadamente da FENABRAVE: as escolhas feitas na validação perderam para persistência no teste. Projeções continuam experimentais; fontes/captura atuais não equivalem a um histórico de todas as revisões passadas. Não somo esses emplacamentos com os de outras fontes nem uso rankings de modelos como total mensal de treino.
