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
| Atualização ponta a ponta | Feito para SENATRAN, IBGE, PostgreSQL e exports agregados | `src/run_project.py` |
| Dashboard Power BI | Pendente | Etapa visual do autor |

## Cobertura atual

- SENATRAN: 31 competências, janeiro/2024 a julho/2026, disponíveis localmente.
- Silver SENATRAN: 440.342 linhas de combustível eletrificado; frota total municipal: 172.783 linhas mensais.
- IBGE: 5.570 municípios; o cruzamento liga 4.874 localidades com código IBGE na competência SENATRAN mais recente.
- SENATRAN: agosto e setembro/2026 ainda não aparecem como publicados na página consultada em 30/09/2026.
- IBGE: PIB 2023, população do Censo 2022 e renda domiciliar per capita do Censo 2022; referências e conceitos ficam explícitos nos nomes das colunas.
- ABVE: há relatórios oficiais mensais e um painel público. A série tabular estruturada ainda precisa ser coletada e conciliada, incluindo a mudança de classificação de 2025. Logo, as perguntas de emplacamentos e market share ainda não estão respondidas pela série mensal validada.
- ABVE/Tupi publicou 29.866 pontos públicos e semipúblicos de recarga com referência a agosto/2026; é um total nacional, não uma base municipal de coordenadas para análise de cobertura local.
- Marcas/modelos SENATRAN: o arquivo de dezembro/2025 foi baixado para Bronze. Ele não contém combustível, então não permite isoladamente identificar modelos eletrificados.
- Open Charge Map: o coletor existe, mas depende de uma chave API local e de revisão de cobertura/licença dos registros.

## Próximas entregas técnicas

1. Coletar e conciliar emplacamentos mensais da ABVE com a definição de eletrificado usada em cada ano; o painel e os boletins confirmam os dados, mas a série inteira ainda não foi estruturada no banco.
2. Integrar o mercado total da FENABRAVE/ANFAVEA para medir participação de mercado com um denominador correspondente.
3. Definir uma classificação de marca/modelo eletrificado baseada em fonte verificável; não inferir combustível apenas pelo nome do modelo.
4. Coletar pontos de recarga com cobertura, data de atualização e licença documentadas. O coletor OCM requer uma chave do usuário.
5. Calcular e documentar relações entre renda, PIB, população e adoção; testar sensibilidade dos municípios de oportunidade antes de interpretar o filtro preliminar.
6. Avaliar previsão somente depois da série mensal de emplacamentos estar conciliada, com separação treino/teste e baseline.
7. Construir o dashboard e o case final no portfólio. Os exports agregados já estão em `data/portfolio/`.

## Regras para o fechamento

- Estoque de frota e fluxo de emplacamentos permanecem métricas distintas.
- Cada tabela informa fonte e período de referência.
- Dados fornecidos pelo usuário com origem não confirmada não serão apresentados como oficiais.
- O repositório não recebe `.env`, chaves, bases brutas com mais de 1 GB ou arquivos que o GitHub não consiga versionar de forma adequada.
- Previsões só serão publicadas com separação treino/teste, modelo de referência e métricas de erro.
