# Análise do Mercado de Veículos Elétricos no Brasil

Este é meu projeto de portfólio para investigar como a mobilidade elétrica está avançando no Brasil, onde a frota se concentra e como a adoção se relaciona com características dos municípios. Eu construo a análise a partir de fontes públicas, registro as limitações de cada dado e organizo o processo para que outra pessoa consiga reproduzi-lo.

## Problema de negócio

Uma empresa que avalia expandir sua atuação em mobilidade elétrica precisa entender onde o mercado já existe, como ele está mudando e quais localidades podem merecer uma análise mais aprofundada. Minha pergunta central é: **como a frota eletrificada evolui no Brasil e onde estão as oportunidades de adoção?**

## O que já construí

- Automatizo o painel público de vendas ABVE: 32 meses por tecnologia, fabricante/modelo e município. Concilio as somas por mês/tecnologia antes de carregar o PostgreSQL. Incluo MHEV de forma explícita; para comparação temporal prefiro filtrar BEV/PHEV.
- Extraio os catálogos anuais PBEV/Inmetro de 2024, 2025 e 2026, preservando modelo, versão, consumo MJ/km e autonomia de ensaio em km. Linhas corrompidas vão para quarentena e o ciclo afetado é marcado como parcial. Não confundo catálogo com vendas nem ensaio com autonomia real.
- Audito intervalos experimentais de um mês com seleção, calibração e teste separados. Quatro das cinco regiões ficaram abaixo da cobertura nominal de 80%; não aprovo as previsões para uso operacional. Veja os resultados em `data/portfolio/ml_intervalos_cobertura.csv`.
- Coleto arquivos mensais de frota por combustível da SENATRAN e preservo os originais na camada Bronze.
- Transformo os dados com Python e Pandas para criar a Silver de veículos eletrificados e a frota total municipal.
- Valido colunas, nulos, duplicidades e quantidades antes de usar os arquivos.
- Integro população do Censo 2022 e PIB municipal de 2023 do IBGE, cruzando município normalizado e UF e mantendo o código IBGE na dimensão resultante.
- Integro também a renda domiciliar per capita média municipal do Censo 2022, mantendo-a separada do PIB.
- Calculo Pearson e Spearman entre indicadores municipais e adoção de eletrificados; trato os coeficientes como associação descritiva, não causal.
- Carrego a Silver no PostgreSQL e gero tabelas Gold para estado, município, categoria, capital/interior, evolução, penetração, correlação socioeconômica e oportunidade preliminar.
- Extraio dos informativos mensais públicos da FENABRAVE os emplacamentos de híbridos e elétricos e os rankings mensais de fabricantes; preservo a fonte e o método de extração em cada registro.
- Organizo 65 registros de modelos em sete rankings publicados pela ABVE ou pela imprensa. Preservo período, fonte, posição, tecnologia conforme a publicação e quantidades desconhecidas; os recortes são parciais, descritos em [docs/modelos_por_noticias.md](docs/modelos_por_noticias.md).
- Comparo quatro métodos de previsão em um backtest temporal, deixando sete competências de fora do treino e publicando métricas/erros para avaliação antes de qualquer projeção futura.
- Avalio Ridge e Random Forest contra três referências simples em horizontes de 1, 2 e 3 meses, separando validação de escolha e teste final. No experimento FENABRAVE, os modelos ML não foram selecionados; publico o resultado e seis projeções de curto prazo identificadas como experimentais, com erros e limitações em [docs/machine_learning.md](docs/machine_learning.md).
- Integro um snapshot mensal da ABVE em tabelas Silver e Gold próprias, preservando a quebra metodológica de janeiro/2025 e as divergências publicadas sem ajuste artificial.
- Completo BEV e PHEV de 2024 com publicações primárias da ABVE e confiro os fechamentos anuais. Com o painel de 2025/2026, tenho 32 meses por tecnologia e um experimento separado de previsão. As escolhas perderam para a referência no teste; não apresento as projeções como previsão operacional aprovada.
- Integro também um snapshot público da ABVE/Tupi sobre infraestrutura de recarga: total nacional, participação regional e rankings top 20 de municípios e UFs, com referência a agosto/2026.
- Disponibilizo um mapa exploratório com 392 objetos de recarga do OpenStreetMap, mantendo acesso, coordenadas, data e atribuição ODbL. Não trato a base comunitária como inventário completo; as regras estão em [docs/recarga_openstreetmap.md](docs/recarga_openstreetmap.md).
- Mantenho a frota SENATRAN (estoque em uma data) separada dos emplacamentos (fluxo durante um período).

## Recorte e limites atuais

A série mensal SENATRAN do meu estudo vai de **janeiro de 2024 a agosto de 2026**, com 32 competências. Fechei o recorte em agosto; setembro não é mais pendência de coleta. A planilha de agosto tem um rodapé de total nacional que separo somente depois de conciliá-lo com o detalhe, sem alterar a Bronze. FENABRAVE e as séries BEV/PHEV ABVE usam esse mesmo corte. Projeções posteriores ficam explicitamente separadas das observações.

O indicador municipal de adoção compara veículos eletrificados com a frota total do município. Também calculo veículos eletrificados por 100 mil habitantes. O PIB é de 2023 e a população é do Censo de 2022; portanto, o PIB per capita combinado é uma aproximação com anos de referência diferentes.

A renda domiciliar per capita vem do Censo 2022 e não é a mesma coisa que PIB per capita. A oportunidade preliminar usa municípios no quartil superior de PIB per capita e renda domiciliar, junto com penetração eletrificada baixa; isso é um filtro exploratório, não uma previsão de demanda.

Nos relatórios FENABRAVE, janeiro/2024 cobre somente autos; a partir de fevereiro/2024, o recorte é autos e comerciais leves. Essa diferença fica numa coluna de cada tabela e precisa ser filtrada ao comparar taxas.

Como primeiro resultado, a análise municipal mostra uma associação positiva entre renda domiciliar e eletrificados por 100 mil habitantes (Spearman 0,690 em 5.528 localidades cruzadas com IBGE, usando a frota de agosto/2026). A base municipal inclui localidades sem registros eletrificados no recorte, usando a frota total da mesma competência como universo. O filtro de oportunidade seleciona 17 municípios no corte original; em nove cenários de percentis, a quantidade varia de 7 a 30. Isso não demonstra causalidade nem estima demanda futura. Em agosto/2026, os totais agregados da FENABRAVE (64.055) também coincidem com a soma publicada pela ABVE entre eletrificados (57.386) e MHEV (6.669); vou usar essa checagem para investigar escopos, sem assumir equivalência nas categorias individuais.

A frota eletrificada nacional SENATRAN de agosto/2026 soma 1.266.671 registros de veículos na definição de combustíveis do projeto, incluindo 148.204 sem UF informada. Mantenho essa parcela no total nacional e separo 1.118.467 com UF conhecida para os recortes geográficos. Esse estoque e sua definição não equivalem ao fluxo de emplacamentos de leves ABVE.

Os arquivos de marcas e modelos da SENATRAN não informam combustível no mesmo registro. Por isso, não uso essa base para afirmar que um modelo específico é elétrico. O histórico mensal por modelo agora vem do painel público ABVE, separado dos rankings documentais antigos. Modelo e município são agregados independentes: não identificam o modelo vendido em cada cidade. Meus primeiros CSVs de mercado foram montados com pesquisa no Gemini e continuam com origem não confirmada; não entram no treino principal do ML.

## Fontes

- [SENATRAN — frota de veículos](https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/estatisticas-frota-de-veiculos-senatran): estoque mensal por localidade e combustível.
- [IBGE/SIDRA — PIB municipal](https://sidra.ibge.gov.br/tabela/6784): PIB corrente municipal, referência 2023.
- [IBGE/SIDRA — população do Censo](https://sidra.ibge.gov.br/tabela/4709): população municipal, referência 2022.
- [IBGE/SIDRA — renda domiciliar per capita](https://sidra.ibge.gov.br/tabela/10295): média municipal do Censo 2022, variável 13431.
- [ABVE Data](https://abve.org.br/abve-data/bi-geral/): automatizo os agregados públicos de vendas por mês/tecnologia, modelo e município, sem login. Guardo a resposta original em Bronze. A interface interna do painel pode mudar; não é uma API oficialmente contratada. Os snapshots anteriores permanecem para auditoria.
- [ABVE — dados até agosto de 2026](https://abve.org.br/com-57-mil-emplacamentos-em-agosto-eletrificados-abrem-a-corrida-para-o-milhao-em-setembro/): referência de validação publicada (57.386 em agosto; 328.477 em janeiro–agosto), usada como conferência independente da série do painel.
- [ABVE/Tupi — infraestrutura de recarga](https://abve.org.br/recarga-rapida-dc-quase-triplica-em-12-meses-e-ja-responde-por-38-da-rede-brasileira/): total nacional e distribuição da rede pública/semipública, referência agosto/2026. O [painel de eletropostos](https://abve.org.br/abve-data/bi-eletropostos/) publica recortes regionais e rankings top 20; o projeto preserva esse escopo parcial, não uma lista completa de coordenadas.
- [FENABRAVE — imprensa e informativos mensais](https://www.fenabrave.org.br/portalv2/home/imprensa): fonte dos totais mensais nas categorias publicadas como “híbridos” e “elétricos” e dos rankings de fabricantes. Rankings gerais de modelos nos boletins não identificam por si só a motorização. Já tenho rankings documentais de modelos eletrificados para alguns períodos, mas ainda preciso de uma série mensal completa para acompanhar sua evolução.
- [ABVE Data](https://abve.org.br/abve-data/): o snapshot anterior e a nova captura ficam separados. PHEV de julho/2024 difere em uma unidade entre eles; preservo a divergência. Não somo as fontes nem ignoro mudanças na classificação MHEV.
- [Inmetro/PBEV](https://www.gov.br/inmetro/pt-br/assuntos/regulamentacao/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica/veiculos-automotivos-pbe-veicular): catálogos de versões, sem associação automática ambígua aos nomes ABVE e sem assumir disponibilidade histórica por mês.
- [Open Charge Map](https://openchargemap.org/develop/api): possível complemento para coordenadas; coleta requer chave API e revisão de licença/cobertura de cada registro.
- [OpenStreetMap/Overpass](https://wiki.openstreetmap.org/wiki/Overpass_API): camada comunitária de objetos de recarga integrada sem chave pessoal, sob ODbL e com cobertura incompleta.

O inventário, os métodos de acesso e as limitações estão em [docs/data_sources.md](docs/data_sources.md). Também documentei por que os CSVs recebidos sem origem confirmada ficam isolados em [docs/provided_data_assessment.md](docs/provided_data_assessment.md). As métricas estão em [docs/metrics.md](docs/metrics.md), as perguntas em [docs/business_questions.md](docs/business_questions.md) e o status de cada entrega em [docs/project_status.md](docs/project_status.md).

## Prévia interativa local

Reorganizei o painel em sete capítulos, com narrativa e respostas explícitas às 15 perguntas. Comparo anos mês a mês e por acumulados do mesmo intervalo; os filtros de anos, tecnologia e mês têm escopo explicado. Incluí rankings de tamanho versus crescimento, participação municipal, capitais versus interior, renda versus adoção e frota versus recarga. Hipóteses e previsões experimentais são diferenciadas de respostas observadas. As tabelas técnicas ficam em seções opcionais e os gráficos têm unidades, legendas, dicas ao passar o mouse e números em formato brasileiro.

Na revisão do painel, separei “o que vejo”, “por que importa” e “o que falta provar”. Retirei localidades sem identificação dos rankings de cidades, preservando os registros nos dados originais. Na seção de futuro, apresento uma análise preliminar de 2024–2026 e três cenários qualitativos para 2027–2030. Esses cenários não são previsões do modelo nem têm probabilidades atribuídas; uso a IEA como contexto externo e mantenho os testes de ML visíveis para explicar por que ainda não aprovo projeções operacionais.

### O motor da análise e meu estudo de Bauru

Acrescentei uma etapa independente do painel que responde às 15 perguntas com arquivos de evidência, identifica a contribuição absoluta de estados e marcas para o crescimento e acompanha a expansão no interior. Escolhi Bauru, onde moro, como estudo de caso: comparo sua evolução com cidades do interior paulista e com dez pares selecionados por população e renda, sem escolher os pares pelo crescimento que tiveram. Meus relatos sobre Uber, solar residencial e recarga em shoppings motivam hipóteses, mas não são tratados como dados de uma pesquisa representativa.

Para investigar recarga, cruzei a participação dos novos emplacamentos BEV/PHEV com a participação dos pontos públicos e semipúblicos ABVE/Tupi. O índice orienta onde pesquisar capacidade e uso, sem contar híbridos sem tomada como demanda de recarga. Também automatizei a extração dos totais nacionais publicados e fiz uma comparação limitada às vinte cidades com pontos informados. Cidade fora desse ranking não recebe zero carregadores.

Comecei uma base documental de preços com seis anúncios primários de versões BYD em 2024. Comparei quatro versões King/Song Pro com os respectivos emplacamentos nacionais em agosto–setembro/2024. É um estudo inicial de preço anunciado e volume, não preço pago, preço atual, FIPE ou elasticidade da demanda. Não atribuo esses modelos às vendas de Bauru: a fonte municipal não fornece esse cruzamento.

Na previsão, mantive o experimento original e acrescentei drift de 12 meses, Holt amortecido e tendência logarítmica de seis meses. Seleciono pela validação temporal e publico erro, viés e comparação com referências. A reanálise melhorou BEV no teste conhecido, mas não PHEV; só meses futuros podem oferecer uma avaliação prospectiva nova. O protocolo e os hashes ficam em `output/analysis/`, e as novas evidências em `data/portfolio/` e nas tabelas `gold.inteligencia_*`, `gold.estudo_bauru_*` e `gold.ml_desafio_*`.

Posso reproduzir esta etapa sem abrir o dashboard:

```powershell
python -m src.ingestion.download_charging_evidence
python -m src.ingestion.download_price_evidence
python -m src.analysis.market_intelligence
python -m src.analysis.forecast_challengers
python -m src.analysis.question_evidence
python -m src.database.load_market_intelligence
```

Criei um painel Streamlit para explorar frota, municípios, emplacamentos, marcas/modelos, resultados de ML e o mapa parcial de recarga. Ele lê somente os exports públicos, sem precisar da senha do PostgreSQL e sem disparar coleta/treinamento. É uma prévia complementar; o Power BI continua sendo a entrega visual principal.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Abro `http://127.0.0.1:8501`. Para renovar os dados, executo `python -m src.run_project` antes de abrir ou recarregar o painel. Para encerrar o servidor, uso Ctrl+C no terminal. A configuração local não publica o serviço na internet.

## Tecnologias

Também automatizei a coleta de 96 observações econômicas mensais do BCB e da carga horária do ONS, resumida em 3.072 grupos mês/hora/subsistema. Testei contexto econômico nas vendas e previsão de frota nas cinco regiões. O Ridge regional superou persistência neste teste, mas continua experimental; contexto econômico não melhorou a seleção das vendas. Minha análise das nove aplicações, fontes, resultados e limites está em [docs/novas_aplicacoes_ml.md](docs/novas_aplicacoes_ml.md). O esquema estrela e as medidas iniciais para o Power BI estão descritos em [docs/modelo_dimensional_bi.md](docs/modelo_dimensional_bi.md).

Python, Pandas, NumPy, scikit-learn, PyMuPDF, PyArrow/Parquet, SQL, PostgreSQL, Git/GitHub e Power BI. Uso cada ferramenta para uma parte concreta do fluxo: Python coleta e transforma, scikit-learn ajusta os modelos de previsão, PyMuPDF extrai texto dos boletins PDF, Parquet armazena as camadas locais, PostgreSQL organiza as tabelas analíticas e Power BI será usado para comunicar os resultados. Spark e orquestração em nuvem ficam como evolução caso o volume e a execução recorrente justifiquem essa complexidade.

## Como reproduzir no Windows

1. Clone o repositório e abra a pasta no PyCharm.
2. Crie o ambiente e instale as dependências:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Crie um arquivo `.env` local com os dados de conexão do seu PostgreSQL, seguindo [.env.example](.env.example). Não envie esse arquivo ao GitHub.
4. Crie o banco `ev_brasil_db` no PostgreSQL. O carregador cria os schemas `silver` e `gold`.
5. Com o banco acessível e o `.env` configurado, execute o fluxo público completo:

```powershell
.\.venv\Scripts\python.exe -m src.run_project
```

O comando coleta e valida fontes, carrega PostgreSQL e exporta resultados. Agora inclui Inmetro, agregados públicos ABVE e auditoria de intervalos. Os coletores reaproveitam arquivos para reprodução; para recapturar vendas ABVE uso `python -m src.ingestion.capture_abve_aggregates --refresh`, seguido da transformação e carga. O recorte observado permanece jan/2024–ago/2026. A recarga ABVE/Tupi continua como snapshot manual. PDFs, respostas brutas e Parquet ficam locais; agregados auditáveis ficam em `data/portfolio/`. Não somo ABVE e FENABRAVE; mantenho dados fornecidos sem fonte confirmada separados do treino.

## Power BI

Preparei o mapa de perguntas, tabelas e cuidados de agregação em [docs/power_bi_handoff.md](docs/power_bi_handoff.md), com consultas SQL conferidas em [sql/consultas_portfolio.sql](sql/consultas_portfolio.sql).

Minha etapa visual será conectar o Power BI ao PostgreSQL (`localhost:5432`, banco `ev_brasil_db`) e usar o schema `gold`. As novas tabelas são `abve_publico_tecnologia`, `abve_publico_modelo`, `abve_publico_municipio`, `inmetro_versoes_eletrificadas` e `ml_intervalos_*`. Uso a data como dimensão; não cruzo fatos municipais e fatos de modelos como se fossem a mesma linha. Os catálogos Inmetro não entram automaticamente como atributos históricos do treino. Power BI, medidas DAX e validação visual ainda são minha entrega final.

## Estrutura

```text
data/       Bronze, Silver, Gold e saídas compartilháveis do portfólio
docs/       problema, fontes, métricas, qualidade e status
src/        ingestão, transformações, qualidade e conexão com PostgreSQL
```

## Meu objetivo

Quero que este projeto mostre como conduzo um problema de dados do início à análise: entendo a pergunta, localizo fontes, coleto e valido os dados, documento decisões, modelo indicadores e apresento os resultados. As conclusões finais e o dashboard serão acrescentados depois da análise e da validação dos dados.

## Meu estudo local e a prova das previsões

Incluí Bauru como estudo de caso porque moro na cidade e percebo a presença dos elétricos no cotidiano. Comparei períodos iguais: foram 256, 326 e 859 novos BEV/PHEV em janeiro–agosto de 2024, 2025 e 2026. A alta de 163,5% em 2026 superou os 136,2% do conjunto de dez cidades paulistas semelhantes em renda e população. Não escolhi esses pares pelo crescimento e não interpreto a comparação como prova causal. Ainda não medi o papel de motoristas de aplicativo, energia solar residencial ou recarga em shoppings.

Ampliei minha amostra para 29 anúncios de preços de BYD/GWM, com data, versão, condição comercial, fonte primária e hash do documento bruto. É um histórico documental de 2024/2025, não uma série mensal FIPE, preço de transação ou preço atual. Não preencho meses sem evidência nem uso esses anúncios esparsos para estimar elasticidade ou depreciação.

Meu Streamlit agora tem capítulos específicos de Bauru e preços. As 15 respostas vêm do motor analítico, evitando manter uma conclusão no código e outra no dashboard. Na recarga regional, comparo novos BEV/PHEV com a rede pública/semipública, sem incluir híbridos sem tomada nesse indicador.

Registrei em 01/10/2026 as projeções de novembro/2026 em `data/registry/previsoes_congeladas_2026_10.json`. Novas execuções preservam esse registro. Ainda não há resultado prospectivo: o valor real precisa ser publicado, coletado e conciliado. A reanálise histórica que melhorou BEV não transforma o modelo em previsão aprovada; PHEV ainda perde para a referência simples.

Preparei um coletor local que consulta recarga OSM e valida a localização pela malha municipal IBGE. Nesta execução, os dois servidores Overpass falharam; não publiquei uma contagem de Bauru. A coleta é opcional para não bloquear o restante do projeto:

```powershell
.\.venv\Scripts\python.exe -m src.ingestion.download_bauru_charging --refresh
.\.venv\Scripts\python.exe -m src.database.load_market_intelligence
```

Incluí também um avaliador que compara as projeções congeladas somente quando o mês termina e há observação na base; sem valor real, não calcula erro. Detalhei entregas, limites, testes e uso no Power BI em [docs/entrega_bauru_precos.md](docs/entrega_bauru_precos.md).
