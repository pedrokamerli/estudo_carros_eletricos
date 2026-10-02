# Checklist completo do Power BI

Este roteiro leva a entrega visual da conexão ao PostgreSQL até a publicação no portfólio. A regra central é não misturar estoque de frota, fluxo de emplacamentos, anúncios de preços, ensaios técnicos e projeções.

## 1. Preparar

- [ ] Abrir o Power BI Desktop e iniciar o PostgreSQL.
- [ ] Conectar ao servidor `localhost:5432`, banco `ev_brasil_db`, schema `gold`.
- [ ] Salvar o `.pbix` em uma pasta do projeto.
- [ ] Nunca salvar senha ou `.env` no GitHub.

## 2. Importar as tabelas

### Mercado e geografia

- [ ] `emplacamentos_abve_mensais`
- [ ] `emplacamentos_fenabrave_mensais`
- [ ] `frota_por_estado`
- [ ] `evolucao_frota_por_estado`
- [ ] `frota_por_municipio`
- [ ] `penetracao_municipal_ibge`
- [ ] `frota_capital_vs_interior`

### Produto, preço e tecnologia

- [ ] `ranking_marcas_fenabrave_mensal`
- [ ] `abve_publico_modelo`
- [ ] `bauru_modelos_mensal`
- [ ] `bauru_modelos_ranking`
- [ ] `bauru_modelos_tecnologia_preco`
- [ ] `inmetro_catalogo_modelo`
- [ ] `precos_historicos_documentais`
- [ ] `precos_resumo_marca`
- [ ] `precos_resumo_marca_tecnologia`

### Recarga, oportunidades e ML

- [ ] `infraestrutura_recarga_abve`
- [ ] `recarga_osm`
- [ ] `bauru_recarga_evidencias`
- [ ] `bauru_solar_context`
- [ ] `oportunidade_municipal_preliminar`
- [ ] `sensibilidade_oportunidade`
- [ ] `ml_backtest_metricas`
- [ ] `ml_selecao_modelos`
- [ ] `ml_projecoes_experimentais`
- [ ] `ml_avaliacao_prospectiva`

## 3. Criar o modelo

- [ ] Usar `bi.dim_data` como calendário e marcar como tabela de datas.
- [ ] Relacionar `data_referencia` com as tabelas mensais em relações 1:N.
- [ ] Manter ABVE e FENABRAVE como fatos separados.
- [ ] Não relacionar fatos agregados apenas por município, marca ou ano.
- [ ] Não relacionar preço com venda quando não houver chave de versão confiável.
- [ ] Não somar frota de vários meses.
- [ ] Conferir se não há relações ambíguas.

## 4. Importar as medidas

- [ ] Copiar as medidas de [medidas_base.dax](../power_bi/medidas_base.dax).
- [ ] Copiar as medidas de [medidas_produto.dax](../power_bi/medidas_produto.dax).
- [ ] Formatar quantidades como inteiros.
- [ ] Formatar percentuais como `%`.
- [ ] Formatar preços como `R$`.
- [ ] Identificar autonomia como `km de ensaio`.
- [ ] Identificar consumo como `MJ/km de ensaio`.

## 5. Montar as páginas

### Página 1 — Resumo executivo

- [ ] Cartões de emplacamentos, crescimento e frota atual.
- [ ] Linha mensal BEV/PHEV.
- [ ] Texto com a principal descoberta.
- [ ] Fonte e período no rodapé.

Pergunta: **Como o mercado de veículos elétricos está avançando?**

### Página 2 — Evolução

- [ ] Linha mensal por tecnologia.
- [ ] Segmentadores de ano e tecnologia.
- [ ] Crescimento anual e tooltip com mês/quantidade.

Pergunta: **O crescimento é contínuo ou acontece em saltos?**

### Página 3 — Geografia

- [ ] Ranking de estados.
- [ ] Ranking/mapa de municípios.
- [ ] Indicador por 100 mil habitantes.
- [ ] Capital versus interior.
- [ ] Competência visível.

Pergunta: **Onde a adoção está concentrada e onde começa a se espalhar?**

### Página 4 — Marcas e modelos

- [ ] Ranking de marcas.
- [ ] Ranking de modelos.
- [ ] Composição BEV/PHEV.
- [ ] Filtros de marca, modelo e tecnologia.

Pergunta: **Quais produtos estão puxando o mercado?**

### Página 5 — Preço e produto

- [ ] Dispersão de preço anunciado versus autonomia de ensaio.
- [ ] Tamanho da bolha = emplacamentos quando houver correspondência.
- [ ] Tabela com preço, autonomia e consumo.
- [ ] Mostrar apenas correspondências seguras.
- [ ] Avisar que preço não é transação e autonomia não é autonomia real.

Pergunta: **Quais modelos combinam produto, preço e adoção observada?**

### Página 6 — Bauru

- [ ] Evolução jan–ago de 2024, 2025 e 2026.
- [ ] Comparação com cidades semelhantes.
- [ ] Ranking de modelos locais.
- [ ] Autonomia, consumo e preço documentado.
- [ ] Evidências de recarga e contexto solar.
- [ ] Limitações da coleta local.

Pergunta: **Bauru cresce apenas em volume ou também em diversidade de modelos?**

### Página 7 — Oportunidades

- [ ] Ranking/mapa de municípios candidatos.
- [ ] PIB, renda e penetração.
- [ ] Sensibilidade dos cortes.
- [ ] Texto deixando claro que é filtro exploratório.

Pergunta: **Onde vale investigar expansão?**

### Página 8 — ML

- [ ] Comparar modelo com persistência.
- [ ] Mostrar WAPE/MAE/RMSE.
- [ ] Gráfico observado versus previsto.
- [ ] Informar treino, teste e horizonte.
- [ ] Rotular projeções como experimentais.

Pergunta: **O modelo aprendeu algo útil ou apenas repetiu o último mês?**

## 6. Storytelling e design

- [ ] Começar pelo problema de negócio.
- [ ] Mostrar tamanho, evolução, geografia e produtos.
- [ ] Usar Bauru como história local.
- [ ] Encerrar com oportunidades, ML e limitações.
- [ ] Usar títulos em formato de pergunta.
- [ ] Usar poucas cores e manter a mesma identidade visual.
- [ ] Reservar laranja para alertas/projeções.
- [ ] Criar tooltips explicativos.
- [ ] Mostrar fonte e período em todas as páginas.

## 7. Validação final

- [ ] Comparar cartões com PostgreSQL e Streamlit.
- [ ] Confirmar que frota usa somente a última competência.
- [ ] Confirmar que ABVE não foi somada à FENABRAVE.
- [ ] Confirmar que preços são anunciados.
- [ ] Confirmar que autonomia é ensaio Inmetro.
- [ ] Conferir filtros, valores em branco e escalas dos gráficos.
- [ ] Revisar em tela cheia e exportar PDF.

## 8. Publicar

- [ ] Salvar o `.pbix`.
- [ ] Exportar imagens das páginas principais.
- [ ] Adicionar imagens ao README.
- [ ] Escrever três descobertas e três limitações.
- [ ] Incluir links do GitHub e dashboard.
- [ ] Não publicar senhas, `.env` ou dados brutos sensíveis.

Considero o Power BI pronto quando os números batem com o banco, cada visual informa fonte/período e a narrativa deixa claro o que é fato, hipótese e projeção.
