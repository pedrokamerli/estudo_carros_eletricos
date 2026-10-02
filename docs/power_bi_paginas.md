# Roteiro de páginas do Power BI

## 1. Resumo executivo

Cartões: emplacamentos ABVE no período, crescimento anual, frota eletrificada na última competência e participação sem UF. Inclua uma faixa curta: “estoque e fluxo são indicadores diferentes”.

## 2. Evolução do mercado

Linha mensal por BEV/PHEV, com seletor de tecnologia e ano. Use `fato_emplacamentos_plugin_abve`; não some com FENABRAVE.

## 3. Geografia da adoção

Mapa ou barras por estado/município usando `frota_por_estado`, `frota_por_municipio` ou `penetracao_municipal_ibge`. Mostre a competência selecionada e não some estoques mensais.

## 4. Produto: marcas, modelos e tecnologia

Ranking de marcas/modelos ABVE e composição BEV/PHEV. Para Bauru, use `bauru_modelos_tecnologia_preco` e exiba o status de pareamento.

## 5. Preço e especificação

Dispersão com preço anunciado no eixo X e autonomia de ensaio no eixo Y; tamanho da bolha = emplacamentos. Use apenas linhas com `status_inmetro = modelo_correspondido_sem_versao` e deixe claro que preço é anúncio e autonomia é ensaio.

## 6. Bauru

Evolução jan–ago por ano, comparação com pares, ranking local de modelos, contexto de recarga e energia solar. Evite transformar o contexto solar municipal em prova de recarga doméstica.

## 7. Oportunidade e futuro

Mostre municípios candidatos, sensibilidade dos cortes e backtest do ML. Projeções experimentais devem ter rótulo “não validada prospectivamente”.

### Regras visuais

- Títulos devem responder uma pergunta, não apenas nomear uma tabela.
- Toda página deve mostrar fonte e período.
- Use “preço anunciado”, “autonomia de ensaio” e “emplacamentos”; não use “preço médio”, “autonomia real” ou “vendas totais” sem a definição correspondente.
