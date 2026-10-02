# Minhas bases para construir o dashboard

Conecto o Power BI ao PostgreSQL `localhost:5432`, banco `ev_brasil_db`, schema `gold`, ou uso os exports pequenos em `data/portfolio/`. A senha fica somente na configuração local. Não relaciono duas tabelas agregadas de granularidades diferentes diretamente só pelo nome do município ou pelo ano: isso multiplica linhas e distorce totais.

## Quais perguntas consigo analisar

| Perguntas | Tabelas Gold principais | Cobertura e interpretação |
| --- | --- | --- |
| 1–2: evolução e crescimento dos emplacamentos | `emplacamentos_fenabrave_mensais`, `emplacamentos_abve_mensais` | Séries separadas até ago/2026; respeitar segmento e classificação de cada fonte |
| 3–4: estados e crescimento da frota | `frota_por_estado`, `evolucao_frota_por_estado` | Jan/2024–ago/2026; estoque da SENATRAN |
| 5–6: municípios e participação | `frota_por_municipio`, `penetracao_municipal_ibge` | Frota mensal e indicador da última competência; penetração inclui localidades sem registros eletrificados |
| 7: capital/interior | `frota_capital_vs_interior` | Comparar competências; participação de uma fotografia não prova crescimento |
| 8: fabricantes | `ranking_marcas_fenabrave_mensal` | Ranking por categoria/mês; filtrar categoria e segmento antes de comparar |
| 9: modelos eletrificados | `ranking_modelos_noticias`, `cobertura_rankings_modelos_noticias` | Sete listas ABVE/imprensa e 65 registros; filtrar fonte/período, separar mensal de acumulado; não é série completa |
| 10: tecnologias | `emplacamentos_abve_mensais`, `abve_plugin_mensais` | BEV/PHEV têm 32 meses, jan/2024–ago/2026; HEV/HEV Flex no snapshot a partir de jan/2025; não somar as duas tabelas |
| 11: economia e adoção | `correlacao_municipal_socioeconomia_adocao`, `penetracao_municipal_ibge` | Correlações descritivas na competência ago/2026, sem inferir causalidade |
| 12–13: candidatos a oportunidade | `oportunidade_municipal_preliminar`, `sensibilidade_oportunidade` | Filtro econômico/de adoção e nove cenários; não mede demanda nem prevê crescimento municipal |
| 14: recarga | `infraestrutura_recarga_abve`, `recarga_osm` | Agregados ABVE/Tupi em ago/2026 e mapa comunitário separado de 392 objetos; cobertura incompleta, acessos distintos e atribuição ODbL obrigatória |
| 15: capacidade de previsão | `ml_backtest_metricas`, `ml_backtest_detalhe`, `ml_selecao_modelos`, `ml_projecoes_experimentais`; equivalentes `ml_abve_*` | Alvos ABVE/FENABRAVE separados; escolhas BEV/PHEV perderam para persistência no teste; projeções experimentais de 1–3 meses, sem intervalo calibrado |
| Preços e produto | `precos_historicos_documentais`, `precos_resumo_marca`, `precos_resumo_marca_tecnologia`, `inmetro_catalogo_modelo` | Anúncios e ensaios técnicos; não são transações, FIPE ou autonomia real |
| Bauru: modelos enriquecidos | `bauru_modelos_tecnologia_preco` | Pareamento conservador por modelo; versões sem chave segura ficam sem especificação/preço |

## Como evito distorções no visual

- Frota é estoque: somar todos os meses conta os mesmos veículos várias vezes. Para um cartão de frota atual, filtro a última competência.
- O total em `evolucao_frota_nacional` inclui veículos sem UF. Mostro essa parcela num indicador de qualidade; rankings de UF/município têm apenas localização conhecida e não devem ser apresentados como cobertura integral do total nacional.
- Emplacamentos são fluxo: somo meses somente dentro da mesma fonte, categoria, segmento e regra metodológica. Não somo ABVE com FENABRAVE.
- Na recarga, filtro `nivel_geografico`. Total nacional, regiões, estados e municípios são recortes sobrepostos; não somo esses níveis. As regiões têm participações, não contagens preenchidas.
- A tabela `penetracao_municipal_ibge` tem frota da última competência e indicadores IBGE de anos anteriores. Campos de referência permanecem visíveis em título/rodapé. Localidades sem código não entram em cruzamentos IBGE.
- Para correlações, mostro também dispersão, amostra e valores extremos. Para oportunidade, mostro como a quantidade de candidatos muda com os cortes; não chamo o filtro de probabilidade.
- Para ML, filtro `etapa = teste` e um horizonte antes de comparar erros. As previsões do mesmo mês feitas por métodos/origens diferentes não são parcelas de vendas. A previsão de setembro/2026 ainda não é venda observada.

## Consultas de apoio

O arquivo `sql/consultas_portfolio.sql` contém consultas conferidas no PostgreSQL para ranking estadual, erros do ML, seleção de métodos, projeções, preços, modelos de Bauru e catálogo Inmetro. O campo do ranking é `total_veiculos_eletrificados`.

## Lacunas que continuam visíveis

Ainda faltam cobertura mensal completa e motorização por versão comparável para modelos, além de um inventário completo de pontos de recarga com coordenadas/cobertura/licença. A base documental de modelos já permite mostrar os rankings dos sete recortes publicados, com quantidades ausentes preservadas; as regras estão em `docs/modelos_por_noticias.md`. Os snapshots ABVE e a transcrição das notícias estão integrados, mas a captura/revisão é manual. Os meses não publicados ficam ausentes; não são preenchidos com valores previstos. Essas limitações devem aparecer no case e no dashboard.
# Complemento: Bauru, preços e prova futura

Adicionei `gold.bauru_estudo_sintese`, `gold.precos_historicos_documentais` e `gold.ml_registro_prospectivo`. As respostas atualizadas estão em `gold.perguntas_evidencias_motor`; comparações municipais em `gold.estudo_bauru_pares_socioeconomicos`. O inventário local de recarga continua indisponível, não é zero.

Grãos, indicadores e limites constam em [entrega_bauru_precos.md](entrega_bauru_precos.md). Não somar percentuais, preços, estoques mensais ou relacionar fatos de modelos e municípios como se fossem observações conjuntas.
