# Status do projeto

## Estado consolidado em 02/10/2026

O projeto já tem um motor analítico reproduzível, nove capítulos no Streamlit, quinze respostas com evidência/limite separados, PostgreSQL Gold carregado e estudo de Bauru. A entrega desta fase está forte para iniciar o Power BI. O que continua aberto é evidência externa nova, não estrutura do projeto: inventário local de recarga, série de preços comparáveis, respostas de pesquisa local e validação prospectiva do ML.

Em 02/10, resolvi a lacuna de modelos por cidade consultando o próprio painel ABVE com os filtros Bauru/SP. O recorte retornou 597 linhas BEV/PHEV desde 2024, 117 modelos e reconciliação mensal exata com o agregado municipal. Também capturei três diretórios públicos de recarga: Seguee (14 estações reportadas, 11 rápidas, R$ 1,54–2,98/kWh), Carregados (shopping, 6 kW médios, confiança 73%, status comunitário funcionando) e MapaVolt (shopping, 3 kW, confiança 12, revisão pendente). Não somei registros potencialmente duplicados.

Atualizado em 01/10/2026. Meu recorte observado está fechado em jan/2024–ago/2026. Setembro não é mais pendência. As notas de pesquisa de 30/09 abaixo são históricas, não ampliam esse corte.

## Atualização de dados e ML em 01/10

### Aprofundamento do motor, sem alterações no dashboard

Acrescentei coleta automatizada de evidências nacionais ABVE/Tupi (totais AC/DC, base anterior e contabilização plug-in desde 2022), seis preços de anúncios primários BYD em 2024 e comparação descritiva de quatro versões com emplacamentos nacionais. Ainda não tenho painel mensal de preços multimarcas, utilização/potência de todos os pontos, recarga residencial ou vendas cruzadas modelo × cidade.

O módulo `market_intelligence` concilia 32 meses por tecnologia entre os recortes nacional, municipal e modelo antes de analisar. Gera crescimento e contribuição por estado/região/cidade/marca, concentração, capitais/interior, recarga regional e vinte cidades, associação parcial renda/adoção controlando população e UF, Bauru e comparadores. Bauru tem 256/326/859 novos BEV/PHEV em jan–ago de 2024/2025/2026, crescimento de 163,5% entre os dois últimos. Dez pares do interior paulista são selecionados por distância em log-população e log-renda, sem usar crescimento para escolhê-los. Relatos de Uber/solar/shoppings não viram variáveis numéricas sem pesquisa.

O desafio de previsão preserva o experimento anterior e testa três métodos adicionais de tendência, com parâmetros registrados. BEV selecionou tendência logarítmica de seis meses e obteve WAPE 23,57% contra 26,89% da persistência; PHEV manteve Ridge e perdeu (32,08% contra 23,10%). É reanálise de teste já conhecido: não alego validação prospectiva ou aprovação operacional. Os intervalos antigos não são reutilizados para os métodos novos.

As 15 respostas estão em `perguntas_evidencias_motor.csv`, separadas em conclusão, evidência e limite. Carreguei e contei 21 novas tabelas Gold numa transação, sem modificar bases antigas. A etapa foi adicionada ao final de `src.run_project`; executei os seis módulos novos separadamente, não a pipeline inteira neste aprofundamento. O dashboard continua com a apresentação anterior e ainda precisa consumir estas novas evidências. Os 27 testes direcionados passaram, incluindo cálculos, invariantes temporais, exports reais e regressão das páginas existentes.

Reorganizei a prévia em sete capítulos narrativos. O capítulo 6 responde às 15 perguntas com estados de evidência explícitos. Incluí filtros didáticos, comparação mensal e acumulada por ano, participação de marcas entre anos, crescimento estadual em 12 meses, capitais/interior, indicadores socioeconômicos e frota/recarga. Eixos, legendas, dicas e números usam linguagem de análise, com tabelas técnicas opcionais. Comparo meses equivalentes e nunca acumulo estoques de frota. O relatório PDF anterior descreve a entrega de dados, não este novo layout.

Validação do novo painel: 13 testes passaram, incluindo as sete páginas, filtros vazios, meses equivalentes, denominador de participação, ranking de um único mês, presença das 15 perguntas, exclusão de localidades desconhecidas dos rankings e identificação dos cenários como qualitativos. A revisão visual também reduziu títulos em janelas estreitas e acrescentou blocos de observação, interpretação e limites. O capítulo 5 interpreta o crescimento em períodos equivalentes e apresenta três cenários qualitativos 2027–2030, com contexto da IEA 2026; não são previsões do ML, probabilidades ou volumes futuros estimados. Os dados e modelos não foram alterados nesta revisão.

Nova entrega desta execução: captura pública ABVE de 32 meses nos recortes tecnologia, fabricante/modelo e município, conciliados por mês e tecnologia; integração dos catálogos Inmetro com quarentena para sobreposições; auditoria dos intervalos de um mês em sete alvos, quatro regiões com cobertura insuficiente. As notas anteriores abaixo descrevem o estado anterior; não substituem a nova entrega.

Carreguei e conferi no PostgreSQL 180 linhas ABVE por tecnologia, 7.531 por modelo e 100.051 por município/tecnologia; 1.176 linhas Inmetro (411/364/401 por ciclo), com duas linhas ambíguas de 2026 em quarentena. Os 49 testes mensais de cobertura estão na Gold. PHEV jul/2024 difere em uma unidade do snapshot anterior; mantive ambos e publiquei a conciliação. Os recortes ABVE incluem MHEV; para comparação temporal uso BEV/PHEV explicitamente.

Nesta entrega executei as etapas novas, não a pipeline antiga inteira. Unittest: 52 casos descobertos, 48 passaram e quatro testes de banco ignorados inicialmente; os quatro passaram separadamente. As sete páginas Streamlit renderizaram sem exceção. O relatório explicativo está em `output/pdf/Relatorio_Entrega_Projeto_EV.pdf` e foi revisado visualmente nas seis páginas.

O ciclo Inmetro com quarentena é parcial. Não concluí associação ABVE/Inmetro por versão nem automação da recarga ABVE. Os testes novos verificam decodificação, unidades, nulos, linhas fundidas, conciliação e independência da calibração em relação aos valores do teste. Esta atualização não implica aprovação operacional do ML.

- Coletei 96 observações mensais BCB/SGS e 3.072 perfis mês/hora/subsistema ONS. Coletores com cache, fonte, captura e hash; Silver, Gold e exports integrados.
- Testei indicadores econômicos na previsão nacional BEV/PHEV: o Ridge com contexto não foi escolhido na validação. Não alego melhora nem causalidade.
- Avaliei frota mensal nas cinco regiões: Ridge escolhido na validação e melhor que persistência no teste de cada região. Resultado experimental, sem intervalo calibrado ou garantia operacional.
- Criei o modelo dimensional BI e medidas DAX iniciais. DAX ainda não executado em PBIX; construção visual continua com o autor.
- O mapa das nove aplicações de ML distingue entregas, fontes localizadas e dados indisponíveis em `docs/novas_aplicacoes_ml.md`. Não implementei nove modelos com bases inadequadas.
- Executei o fluxo completo com sucesso em 01/10/2026, incluindo novas fontes, ML regional/econômico, esquema BI e exports. Executei 40 casos unitários com sucesso e os quatro testes BI/PostgreSQL separadamente; as funções legadas exclusivas de pytest não foram executadas.
- Criei a prévia local Streamlit com seis áreas, filtros e download dos recortes. Ela lê exports públicos sem acesso ao banco e não executa atualizações. As seis páginas passaram pelo teste de renderização, incluindo competência histórica e mapa com filtro vazio. O Power BI ainda é a entrega visual principal pendente.

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
| Cruzamento municipal IBGE | Feito e publicado no PostgreSQL; 5.528 das 5.574 localidades da frota total SENATRAN cruzaram com IBGE, incluindo as sem registros eletrificados | `src/transformation/silver_to_gold.py`, `src/database/load_municipal_insights_to_postgres.py` |
| Indicadores econômicos municipais | Feito: PIB 2023, população do Censo 2022 e renda domiciliar per capita do Censo 2022 | `src/ingestion/download_ibge_municipal_indicators.py`, `data/portfolio/penetracao_municipal_ibge.csv` |
| Oportunidade municipal preliminar | Feito como filtro exploratório de quartis de PIB, renda e adoção; não é previsão | `gold.oportunidade_municipal_preliminar` |
| Sensibilidade de oportunidade | Feito: nove cenários de percentis, 17 municípios no corte original e 7–30 nos cenários com frota de ago/2026; interseção, união e Jaccard publicados | `gold.sensibilidade_oportunidade`, `src/analysis/opportunity_sensitivity.py` |
| Correlação socioeconômica e adoção | Implementada com Pearson e Spearman para PIB, renda e população versus dois indicadores de adoção; é descritiva, não causal | `gold.correlacao_municipal_socioeconomia_adocao` |
| Backtest de previsão | Feito: 4 baselines, 24 meses de treino e 7 meses de teste para cada categoria FENABRAVE; resultado carregado em Gold | `gold.backtest_previsao_fenabrave`, `gold.backtest_detalhe_previsao_fenabrave` |
| Experimento ML e projeções curtas | Ridge e Random Forest comparados com 3 referências simples; validação e teste separados, horizontes 1–3 meses; 330 previsões retrospectivas, 60 métricas e 6 projeções experimentais | `src/analysis/forecast_ml.py`, `gold.ml_*`, `docs/machine_learning.md` |
| Auditoria dos dados fornecidos | Feita: estrutura, cobertura e consistência interna avaliadas; não há fonte documentada e os exports seguem explicitamente não verificados | `docs/provided_data_assessment.md` |
| Coleta de emplacamentos FENABRAVE | Feito para os boletins mensais públicos de autos e comerciais leves, jan/2024–ago/2026 | `src/ingestion/download_fenabrave_monthly_reports.py` |
| Série ABVE | Snapshot de 32 totais mensais (jan/2024–ago/2026) e tecnologia em 20 meses (jan/2025–ago/2026); validado em Silver, carregado em PostgreSQL e modelado em Gold; captura ainda manual | `data/portfolio/emplacamentos_abve_mensais.csv`, `silver.abve_emplacamentos_mensais`, `gold.emplacamentos_abve_mensais` |
| Infraestrutura de recarga ABVE/Tupi | Feito: 46 linhas de snapshot com total nacional, 5 participações regionais e rankings top 20 de municípios/UFs; validado, carregado em Silver/Gold e exportado; captura manual e sem coordenadas completas | `silver.abve_infraestrutura_recarga`, `gold.infraestrutura_recarga_abve`, `data/portfolio/infraestrutura_recarga_abve_gold.csv` |
| Silver/Gold FENABRAVE | Feito: 64 linhas de categorias mensais e 960 registros de ranking mensal de fabricantes | `silver.fenabrave_*`, `gold.*_fenabrave_*` |
| Rankings documentais de modelos | Feito como cobertura parcial: 65 registros em sete listas ABVE/imprensa, 56 quantidades informadas e nove desconhecidas; publicação/período preservados | `silver.ranking_modelos_noticias`, `gold.ranking_modelos_noticias`, `gold.cobertura_rankings_modelos_noticias`, `docs/modelos_por_noticias.md` |
| Atualização ponta a ponta | Executada com sucesso em 30/09/2026, incluindo SENATRAN ago/2026, ABVE plug-in/ML, OSM, PostgreSQL e exports; 27 testes unitários passaram | `src/run_project.py` |
| Dashboard Power BI | Pendente | Etapa visual do autor |
| Histórico plug-in ABVE e ML por tecnologia | Feito: 32 meses por BEV/PHEV, 64 registros; totais de 2024 conciliados com fechamento anual; escolhas não superaram persistência no teste | `gold.abve_plugin_mensais`, `gold.ml_abve_*`, `docs/machine_learning.md` |
| Mapa comunitário de recarga | Integrado como complemento parcial: 392 objetos, 85 com acesso público declarado; não é inventário completo nem série de treino ML | `gold.recarga_osm`, `docs/recarga_openstreetmap.md` |

## Cobertura atual

- SENATRAN: 32 competências, janeiro/2024 a agosto/2026, disponíveis localmente.
- Silver SENATRAN: 459.993 linhas de combustível eletrificado; frota total municipal: 178.357 linhas mensais.
- IBGE: 5.570 municípios; o cruzamento liga 5.528 das 5.574 localidades presentes na frota total da competência SENATRAN mais recente. A análise municipal inclui as localidades sem registros eletrificados; 46 localidades ficam sem associação, sem código inventado.
- SENATRAN: agosto/2026 foi encontrado no portal e integrado; setembro ainda não foi encontrado. O rodapé de agosto concilia com 135.907.590 veículos de todas as motorizações no detalhe e foi separado sem alterar a Bronze. A frota eletrificada nacional do projeto soma 1.266.671, incluindo 148.204 sem UF; a Gold nacional conserva o total da Silver em todas as competências e separa a parcela geográfica conhecida.
- FENABRAVE: 32 competências disponíveis, janeiro/2024 a agosto/2026; 64 linhas de híbridos/elétricos e 960 linhas dos rankings mensais de fabricantes. Janeiro/2024 cobre somente autos, enquanto os relatórios de fevereiro/2024 em diante cobrem autos e comerciais leves. Janeiro foi transcrito visualmente e conferido no PDF, pois a codificação de fonte impede extração textual confiável; segmento e método ficam registrados por linha.
- Backtest: usa fevereiro/2024–agosto/2026 para manter o segmento autos + comerciais leves; os primeiros 24 meses são treino e os 7 últimos formam um teste walk-forward de um passo à frente. A persistência do último mês teve menor MAPE nos dois grupos (14,80% em “elétricos”; 8,52% em “híbridos”), mas não trato isso como validação suficiente para uma projeção futura.
- IBGE: PIB 2023, população do Censo 2022 e renda domiciliar per capita do Censo 2022; referências e conceitos ficam explícitos nos nomes das colunas.
- FENABRAVE: a série responde evolução e crescimento apenas segundo as categorias amplas “híbridos” e “elétricos” do boletim, no recorte de autos e comerciais leves. Rankings de fabricantes são disponibilizados por categoria/mês; não equivalem automaticamente à taxonomia ABVE (BEV/HEV/PHEV).
- ABVE: os painéis públicos incorporados em Power BI e notícias mensais foram verificados. O snapshot tem 32 totais mensais e 20 meses de composição tecnológica, foi transcrito do painel e integrado em Silver/Gold; falta automatizar atualização. A classificação mudou em jan/2025 e o último mês fechado encontrado em 30/09/2026 foi ago/2026. Em ago/2025, a soma das quatro categorias fica 16 unidades abaixo do total mensal no painel; os acumulados do painel excedem os citados nas notícias em 16 unidades para jan–ago/2025 e 6 unidades para jan–ago/2026. Registrei as diferenças sem ajuste inventado.
- Conferência agregada de agosto/2026: FENABRAVE soma 64.055 “híbridos + elétricos”; a ABVE separa 57.386 eletrificados e 6.669 MHEV, também somando 64.055. Isso dá uma pista de escopo para futura reconciliação, mas **não** prova equivalência entre as categorias por tecnologia.
- ABVE Silver/Gold: o snapshot passa por validações de 32 meses contínuos, 20 meses com composição, contagens não negativas e conciliação registrada no arquivo; carreguei 32 linhas em `silver.abve_emplacamentos_mensais` e criei `gold.emplacamentos_abve_mensais`. O export para Power BI é `emplacamentos_abve_mensais_gold.csv`. A captura ainda é manual.
- ABVE/Tupi publicou 29.866 pontos públicos e semipúblicos de recarga, referência agosto/2026. Integrei 46 linhas: total nacional, participações das cinco regiões e top 20 de municípios e UFs. O painel diz que a rede alcança 1.911 municípios, mas não expõe no recorte transcrito todos os municípios nem coordenadas; não é possível calcular cobertura completa/distâncias. Veja `docs/data_sources.md` e `docs/metrics.md`.
- Marcas/modelos SENATRAN: o arquivo de dezembro/2025 foi baixado para Bronze. Ele não contém combustível, então não permite isoladamente identificar modelos eletrificados. Os boletins FENABRAVE permitem rankings de fabricantes por categoria. A nova base de notícias contém 65 registros em sete rankings/períodos entre 2024 e 2026; 56 quantidades informadas e nove desconhecidas. Fontes primárias e imprensa estão identificadas, assim como recortes mensais/acumulados e modelo/versão versus grupo de modelos. Não há ainda uma série mensal completa por modelo.
- Open Charge Map: o coletor opcional existe, mas depende de uma chave API local e de revisão de cobertura/licença dos registros; não é necessário para os indicadores agregados ABVE/Tupi já integrados.

## Próximas entregas técnicas

1. Automatizar atualização dos snapshots ABVE de vendas e recarga se houver forma pública estável de extrair os painéis; as integrações atuais validam e carregam os snapshots, mas ainda exigem transcrição/captura manual. Mantenho o recorte observado encerrado em agosto/2026.
2. Se eu quiser usar os três CSVs recebidos como evidência do estudo principal, localizar a fonte original, licença, data de extração e definições; sem isso continuam excluídos das conclusões oficiais.
3. Ampliar a base documental de modelos, que já tem sete rankings rastreáveis, para mais competências e versões comparáveis; avaliar fontes diretas/exportações adicionais sem presumir que um login garanta os campos necessários. Não compartilhar senha no chat. Não preencher lacunas a partir dos CSVs produzidos com Gemini sem referência original.
4. Para mapa completo de recarga, ampliar e avaliar inventário/coordenadas sem assumir cobertura completa de uma base comunitária. ABVE/Tupi responde distribuição agregada/top 20; OSM já está integrado como mapa parcial sem chave pessoal. Open Charge Map segue opcional e requer chave local.
5. Mostrar as correlações, distribuições e a sensibilidade do filtro no Power BI. A sensibilidade já foi calculada em nove cenários, sem alterar a regra original para aumentar a lista; associação não prova causa.
6. Atualizar a avaliação preditiva quando houver novas competências: o experimento ML usa validação e teste separados, com horizontes 1–3 meses, e disponibiliza seis projeções experimentais. Os modelos ML não venceram na validação; a escolha de elétricos também perdeu para a persistência no teste final. Não há previsão operacional aprovada ou intervalo calibrado. Metodologia e métricas estão em `docs/machine_learning.md`.
7. Construir o dashboard Power BI e o case visual do portfólio. Os exports agregados já estão em `data/portfolio/`; esta é a etapa visual reservada ao autor.

## Regras para o fechamento

- Estoque de frota e fluxo de emplacamentos permanecem métricas distintas.
- Cada tabela informa fonte e período de referência.
- Dados fornecidos pelo usuário com origem não confirmada não serão apresentados como oficiais.
- O repositório não recebe `.env`, chaves, bases brutas com mais de 1 GB ou arquivos que o GitHub não consiga versionar de forma adequada.
- Previsões só serão publicadas com separação treino/teste, modelo de referência e métricas de erro.
# Entrega local, preços e registro futuro — 01/10/2026

Acrescentei síntese de Bauru frente a dez pares, 31 anúncios documentais BYD/GWM, registro imutável de projeções para novembro, avaliador automático e integração das respostas do motor ao Streamlit. Carreguei 29 tabelas de inteligência com contagens conferidas. Não executei novamente a pipeline inteira.

O coletor local de recarga foi implementado e recebeu a malha IBGE. A consulta OSM falhou nos dois servidores: não há novo inventário validado de Bauru, nem conclusão de zero carregadores. Faltam funcionamento/utilização, histórico comparável de preços e pesquisa local. O teste prospectivo depende de observações futuras e ainda não ocorreu. Detalhes e uso no Power BI: [entrega_bauru_precos.md](entrega_bauru_precos.md).
