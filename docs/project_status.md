# Status do projeto

Atualizado em 30/09/2026. Este documento diferencia o que está implementado do que ainda depende de fonte, credencial ou decisão analítica.

## Entregas implementadas

| Parte | Estado | Evidência no projeto |
| --- | --- | --- |
| Pergunta de negócio e escopo | Feito | `docs/business_questions.md`, `docs/collection_scope.md` |
| Coleta mensal SENATRAN por combustível | Feito para os meses publicados no portal | `src/ingestion/download_senatran_fuel_history.py` e manifesto local |
| Coleta PIB municipal e população | Feito | `src/ingestion/download_ibge_municipal_indicators.py` |
| Silver eletrificada e validações | Feito | `src/transformation/bronze_to_silver.py`, `src/quality/` |
| PostgreSQL e conexão Python | Feito | `src/database/connection.py`, `src/database/load_silver_to_postgres.py` |
| Tabelas Gold de frota e evolução | Feito | `src/database/build_gold_tables.py` |
| Frota total e participação municipal | Feito; frota eletrificada comparada com frota total na mesma competência | `src/transformation/bronze_to_silver.py`, `gold.penetracao_municipal_ibge` |
| Cruzamento municipal IBGE | Feito e publicado no PostgreSQL; 4.874 dos 4.914 municípios SENATRAN cruzaram com IBGE | `src/transformation/silver_to_gold.py`, `src/database/load_municipal_insights_to_postgres.py` |
| Indicadores econômicos municipais | Feito: PIB 2023, população do Censo 2022 e renda domiciliar per capita do Censo 2022 | `src/ingestion/download_ibge_municipal_indicators.py`, `data/portfolio/penetracao_municipal_ibge.csv` |
| Oportunidade municipal preliminar | Feito como filtro exploratório de quartis de PIB, renda e adoção; não é previsão | `gold.oportunidade_municipal_preliminar` |
| Correlação socioeconômica e adoção | Implementada com Pearson e Spearman para PIB, renda e população versus dois indicadores de adoção; é descritiva, não causal | `gold.correlacao_municipal_socioeconomia_adocao` |
| Backtest de previsão | Feito: 4 baselines, 24 meses de treino e 7 meses de teste para cada categoria FENABRAVE; resultado carregado em Gold | `gold.backtest_previsao_fenabrave`, `gold.backtest_detalhe_previsao_fenabrave` |
| Auditoria dos dados fornecidos | Feita: estrutura, cobertura e consistência interna avaliadas; não há fonte documentada e os exports seguem explicitamente não verificados | `docs/provided_data_assessment.md` |
| Coleta de emplacamentos FENABRAVE | Feito para os boletins mensais públicos de autos e comerciais leves, jan/2024–ago/2026 | `src/ingestion/download_fenabrave_monthly_reports.py` |
| Silver/Gold FENABRAVE | Feito: 64 linhas de categorias mensais e 960 registros de ranking mensal de fabricantes | `silver.fenabrave_*`, `gold.*_fenabrave_*` |
| Atualização ponta a ponta | Feito e executado com SENATRAN, IBGE, FENABRAVE, PostgreSQL e exports agregados | `src/run_project.py` |
| Dashboard Power BI | Pendente | Etapa visual do autor |

## Cobertura atual

- SENATRAN: 31 competências, janeiro/2024 a julho/2026, disponíveis localmente.
- Silver SENATRAN: 440.342 linhas de combustível eletrificado; frota total municipal: 172.783 linhas mensais.
- IBGE: 5.570 municípios; o cruzamento liga 4.874 localidades com código IBGE na competência SENATRAN mais recente.
- SENATRAN: agosto e setembro/2026 ainda não aparecem como publicados na página consultada em 30/09/2026.
- FENABRAVE: 32 competências disponíveis, janeiro/2024 a agosto/2026; 64 linhas de híbridos/elétricos e 960 linhas dos rankings mensais de fabricantes. Janeiro/2024 cobre somente autos, enquanto os relatórios de fevereiro/2024 em diante cobrem autos e comerciais leves. Janeiro foi transcrito visualmente e conferido no PDF, pois a codificação de fonte impede extração textual confiável; segmento e método ficam registrados por linha.
- Backtest: usa fevereiro/2024–agosto/2026 para manter o segmento autos + comerciais leves; os primeiros 24 meses são treino e os 7 últimos formam um teste walk-forward de um passo à frente. A persistência do último mês teve menor MAPE nos dois grupos (14,80% em “elétricos”; 8,52% em “híbridos”), mas não trato isso como validação suficiente para uma projeção futura.
- IBGE: PIB 2023, população do Censo 2022 e renda domiciliar per capita do Censo 2022; referências e conceitos ficam explícitos nos nomes das colunas.
- FENABRAVE: a série responde evolução e crescimento apenas segundo as categorias amplas “híbridos” e “elétricos” do boletim, no recorte de autos e comerciais leves. Rankings de fabricantes são disponibilizados por categoria/mês; não equivalem automaticamente à taxonomia ABVE (BEV/HEV/PHEV).
- ABVE: há relatórios oficiais mensais e um painel público. A série mensal estruturada ainda precisa ser coletada e conciliada, incluindo a mudança de classificação de 2025. Manter ABVE separada da FENABRAVE até haver reconciliação documentada.
- Conferência agregada de agosto/2026: FENABRAVE soma 64.055 “híbridos + elétricos”; a ABVE separa 57.386 eletrificados e 6.669 MHEV, também somando 64.055. Isso dá uma pista de escopo para futura reconciliação, mas **não** prova equivalência entre as categorias por tecnologia.
- ABVE/Tupi publicou 29.866 pontos públicos e semipúblicos de recarga com referência a agosto/2026; é um total nacional, não uma base municipal de coordenadas para análise de cobertura local. A ABVE reportou também 57.386 eletrificados leves em agosto/2026 e 328.477 no acumulado janeiro–agosto; uso esses números como validação publicada, não como uma série ABVE mensal já carregada.
- Marcas/modelos SENATRAN: o arquivo de dezembro/2025 foi baixado para Bronze. Ele não contém combustível, então não permite isoladamente identificar modelos eletrificados. Os boletins públicos da FENABRAVE trazem ranking de fabricantes, mas o portal reserva o ranking de modelos para usuário cadastrado.
- Open Charge Map: o coletor existe, mas depende de uma chave API local e de revisão de cobertura/licença dos registros.

## Próximas entregas técnicas

1. Coletar e conciliar a série mensal ABVE e documentar a mudança de classificação; mantê-la em tabela própria.
2. Se eu quiser usar os três CSVs recebidos como evidência do estudo principal, localizar a fonte original, licença, data de extração e definições; sem isso continuam excluídos das conclusões oficiais.
3. Obter acesso autenticado ao portal FENABRAVE para avaliar modelos mais vendidos e confirmar os campos/regras de exportação. Não compartilhar senha no chat; caso necessário, usar o login localmente.
4. Coletar pontos de recarga com cobertura, data de atualização e licença documentadas. O coletor Open Charge Map requer uma chave API local.
5. Interpretar correlações com gráficos/distribuições e testar sensibilidade do filtro de oportunidade; associação não prova causa.
6. Aumentar o histórico comparável e testar o backtest em novas janelas antes de publicar previsão futura. As tabelas de erro estão disponíveis para visualização, mas ainda não há uma projeção futura validada.
7. Construir o dashboard Power BI e o case visual do portfólio. Os exports agregados já estão em `data/portfolio/`.

## Regras para o fechamento

- Estoque de frota e fluxo de emplacamentos permanecem métricas distintas.
- Cada tabela informa fonte e período de referência.
- Dados fornecidos pelo usuário com origem não confirmada não serão apresentados como oficiais.
- O repositório não recebe `.env`, chaves, bases brutas com mais de 1 GB ou arquivos que o GitHub não consiga versionar de forma adequada.
- Previsões só serão publicadas com separação treino/teste, modelo de referência e métricas de erro.
