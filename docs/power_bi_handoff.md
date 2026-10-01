# Minhas bases para construir o dashboard

Conecto o Power BI ao PostgreSQL `localhost:5432`, banco `ev_brasil_db`, schema `gold`, ou uso os exports pequenos em `data/portfolio/`. A senha fica somente na configuração local. Não relaciono duas tabelas agregadas de granularidades diferentes diretamente só pelo nome do município ou pelo ano: isso multiplica linhas e distorce totais.

## Quais perguntas consigo analisar

| Perguntas | Tabelas Gold principais | Cobertura e interpretação |
| --- | --- | --- |
| 1–2: evolução e crescimento dos emplacamentos | `emplacamentos_fenabrave_mensais`, `emplacamentos_abve_mensais` | Séries separadas até ago/2026; respeitar segmento e classificação de cada fonte |
| 3–4: estados e crescimento da frota | `frota_por_estado`, `evolucao_frota_por_estado` | Jan/2024–jul/2026; estoque da SENATRAN |
| 5–6: municípios e participação | `frota_por_municipio`, `penetracao_municipal_ibge` | Frota mensal e indicador da última competência; penetração inclui localidades sem registros eletrificados |
| 7: capital/interior | `frota_capital_vs_interior` | Comparar competências; participação de uma fotografia não prova crescimento |
| 8: fabricantes | `ranking_marcas_fenabrave_mensal` | Ranking por categoria/mês; filtrar categoria e segmento antes de comparar |
| 9: modelos eletrificados | Sem tabela oficial validada | CSVs recebidos sem origem confirmada não resolvem esta pergunta |
| 10: tecnologias | `emplacamentos_abve_mensais` | BEV/PHEV/HEV/HEV Flex a partir de jan/2025; categorias SENATRAN não são equivalências automáticas |
| 11: economia e adoção | `correlacao_municipal_socioeconomia_adocao`, `penetracao_municipal_ibge` | Correlações descritivas na competência jul/2026, sem inferir causalidade |
| 12–13: candidatos a oportunidade | `oportunidade_municipal_preliminar`, `sensibilidade_oportunidade` | Filtro econômico/de adoção e nove cenários; não mede demanda nem prevê crescimento municipal |
| 14: recarga | `infraestrutura_recarga_abve` | Rede nacional, participação regional e top 20 municípios/UFs em ago/2026; sem cobertura geográfica completa |
| 15: capacidade de previsão | `ml_backtest_metricas`, `ml_backtest_detalhe`, `ml_selecao_modelos`, `ml_projecoes_experimentais` | ML comparado com referências simples; projeções experimentais de 1–3 meses, sem intervalo calibrado |

## Como evito distorções no visual

- Frota é estoque: somar todos os meses conta os mesmos veículos várias vezes. Para um cartão de frota atual, filtro a última competência.
- Emplacamentos são fluxo: somo meses somente dentro da mesma fonte, categoria, segmento e regra metodológica. Não somo ABVE com FENABRAVE.
- Na recarga, filtro `nivel_geografico`. Total nacional, regiões, estados e municípios são recortes sobrepostos; não somo esses níveis. As regiões têm participações, não contagens preenchidas.
- A tabela `penetracao_municipal_ibge` tem frota da última competência e indicadores IBGE de anos anteriores. Campos de referência permanecem visíveis em título/rodapé. Localidades sem código não entram em cruzamentos IBGE.
- Para correlações, mostro também dispersão, amostra e valores extremos. Para oportunidade, mostro como a quantidade de candidatos muda com os cortes; não chamo o filtro de probabilidade.
- Para ML, filtro `etapa = teste` e um horizonte antes de comparar erros. As previsões do mesmo mês feitas por métodos/origens diferentes não são parcelas de vendas. A previsão de setembro/2026 ainda não é venda observada.

## Consultas de apoio

O arquivo `sql/consultas_portfolio.sql` contém quatro consultas conferidas no PostgreSQL: ranking estadual na última competência, comparação de erros, seleção de métodos e projeções experimentais. O campo do ranking é `total_veiculos_eletrificados`.

## Lacunas que continuam visíveis

Ainda faltam uma fonte validada de emplacamentos por modelo eletrificado e um inventário completo de pontos de recarga com coordenadas/cobertura/licença. Os snapshots ABVE estão integrados, mas a atualização da captura do painel é manual. Os meses não publicados ficam ausentes; não são preenchidos com valores previstos. Essas limitações devem aparecer no case e no dashboard.
