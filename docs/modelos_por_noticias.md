# Minha base de modelos a partir de publicações

Montei uma base documental para começar a responder quais modelos eletrificados aparecem nos rankings de emplacamentos. Cada registro tem marca, nome original, tecnologia conforme a publicação, posição, quantidade quando informada, período e URL. A captura inicial é uma transcrição revisada em 30/09/2026; Python valida, transforma e carrega os registros. A busca e a seleção de novas notícias ainda exigem revisão, não são extração automática recorrente.

## Recortes que já tenho

| Fonte | Período dos dados | Lista | Quantidade disponível | Link |
| --- | --- | --- | --- | --- |
| ABVE | Janeiro/2024 | Top 5 de eletrificados, por modelo/versão | 2 dos 5 modelos | [Publicação](https://abve.org.br/eletrificados-leves-iniciam-2024-com-novo-recorde-de-vendas-em-janeiro/) |
| ABVE | Fevereiro/2024 | Top 5 de eletrificados, por modelo/versão | Nenhum volume por modelo | [Publicação](https://abve.org.br/bevs-lideram-vendas-pelo-terceiro-mes-seguido/) |
| ABVE | Janeiro–abril/2024 | Top 5 acumulado, por modelo/versão | Todos | [Publicação](https://abve.org.br/veiculos-plug-in-chegam-a-70-dos-eletrificados-em-abril-e-batem-novo-recorde/) |
| ABVE | Janeiro–maio/2024 | Top 5 acumulado, por modelo/versão | Todos | [Publicação](https://abve.org.br/numeros-de-maio-apontam-que-interiorizacao-da-eletromobilidade-avanca-no-brasil/) |
| Webmotors | Dezembro/2024 | Top 10 BEV por modelo | Todos; fornecedor do levantamento não explicitado na lista | [Publicação](https://www.webmotors.com.br/wm1/mercado-automotivo/rankings/os-10-carros-eletricos-mais-emplacados-em-dezembro) |
| Webmotors, atribuindo ABVE | Janeiro–maio/2025 | Lista de 5 grupos; inclui híbridos leves | 4 totais diretos; Pulse fica sem total direto | [Publicação](https://www.webmotors.com.br/wm1/carros/eletricos-e-hibridos/hibridos-e-eletricos-versoes-que-tem-mais-saida) |
| Webmotors, atribuindo JATO Dynamics | Agosto/2026 | Top 30 do recorte descrito como 100% elétrico | Todos | [Publicação](https://www.webmotors.com.br/wm1/mercado-automotivo/30-eletricos-mais-vendidos-no-brasil-em-agosto) |

São **65 registros, sete listas, 56 quantidades informadas e nove desconhecidas**. Quatro publicações são da ABVE, como fonte primária; três são reportagens de imprensa. Uma matéria atribuir dados à ABVE/JATO não a transforma em extração direta dessas entidades.

## Decisões para manter a análise correta

- Posição sem quantidade continua com quantidade nula. Não significa zero emplacamentos. Para Pulse/2025, a matéria informa volumes de versões, mas não um total direto: não preenchi esse total por inferência.
- Registro mensal e acumulado têm campos distintos. Não somo janeiro–abril com janeiro–maio, nem chamo o segundo acumulado de vendas somente em maio. Não reconstruo a série mensal por diferenças entre listas top 5 cuja composição muda.
- Os nomes por versão da ABVE e os grupos de modelos das reportagens têm granularidades diferentes. Padronizo apenas caixa e espaços; não junto `Dolphin GS 180 EV` com `Dolphin` ou todos os Haval H6 automaticamente.
- A lista de 2025 contém híbridos leves, embora cite a ABVE. Preservo o escopo próprio da matéria; não uso o total dessa lista como se correspondesse à definição ABVE vigente sem MHEV. Haval H6 fica classificado como grupo misto HEV/PHEV, conforme as versões descritas.
- Na lista de agosto/2026, a tecnologia segue o recorte BEV declarado pela reportagem. Nomes gerais como C10, B10 ou Blazer não autorizam classificar todas as versões encontradas em outras bases como BEV. A conferência de motorização por versão continua necessária para um cruzamento externo.
- Os 30 volumes de agosto/2026 somam 26.927, enquanto a reportagem publica total do segmento de 27.129. A diferença de 202 fica registrada na tabela de cobertura; a lista é parcial. Não substituo o total do segmento pela soma do top 30 nem por um total de outra entidade.
- Notícias de veículos mais buscados/visitados não medem emplacamentos. Também descartei como fechamento anual a [prévia publicada em 30/12/2025](https://www.webmotors.com.br/wm1/carros/dolphin-mini-dolphin-byd-recordes), que se identifica como dados parciais.

## Como uso no PostgreSQL e no Power BI

As fontes estão em `data/portfolio/fontes_rankings_modelos_noticias.csv`; a transcrição está em `data/portfolio/rankings_modelos_noticias_snapshot.csv`. O módulo `src.transformation.news_models_to_silver` valida datas, chaves, posições, contagens e vínculo à fonte e grava um Parquet local. `src.database.load_news_models_to_postgres` carrega `silver.ranking_modelos_noticias`, `gold.ranking_modelos_noticias` e `gold.cobertura_rankings_modelos_noticias` em uma transação. Ambos fazem parte de `src.run_project`.

No Power BI, seleciono **uma `fonte_id` por visual de ranking**, ordeno por `posicao` e mantenho publicador, intervalo e escopo no título/rodapé. Para listas sem volumes, mostro posição em tabela, sem gráfico de quantidade. Não agrego indiscriminadamente diferentes listas, fontes ou períodos. Os exports são `ranking_modelos_noticias_gold.csv` e `cobertura_rankings_modelos_noticias.csv`.

```sql
SELECT posicao, marca, modelo_original, tecnologia_fonte, quantidade_emplacada
FROM gold.ranking_modelos_noticias
WHERE fonte_id = 'wm_202608'
ORDER BY posicao;
```

Esta entrega responde rankings dos recortes publicados, não uma série mensal completa de janeiro/2024 a setembro/2026. Para evolução por modelo, taxas de crescimento e market share nacional contínuo, ainda preciso ampliar cobertura e reconciliar fontes, versões e classificações. Não uso este conjunto descontínuo como treino do ML mensal.
