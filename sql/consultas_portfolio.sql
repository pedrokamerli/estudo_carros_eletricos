-- Procuro o ranking somente na última competência, para não misturar os meses.
SELECT uf, total_veiculos_eletrificados
FROM gold.frota_por_estado
WHERE (ano_referencia, mes_referencia) = (
    SELECT ano_referencia, mes_referencia
    FROM gold.frota_por_estado
    ORDER BY ano_referencia DESC, mes_referencia DESC
    LIMIT 1
)
ORDER BY total_veiculos_eletrificados DESC
LIMIT 10;

-- Comparo os erros de cada método no teste final, separando os horizontes.
SELECT categoria_fenabrave, horizonte_meses, metodo, mae, rmse, wape_percentual
FROM gold.ml_backtest_metricas
WHERE etapa = 'teste'
ORDER BY categoria_fenabrave, horizonte_meses, wape_percentual;

-- Vejo a escolha feita antes do teste e se ela superou a referência simples.
SELECT * FROM gold.ml_selecao_modelos ORDER BY categoria_fenabrave;

-- Consulto projeções como experimento, preservando o rótulo e a data de treino.
SELECT categoria_fenabrave, data_referencia, emplacamentos_previstos, metodo,
       fim_treino, status
FROM gold.ml_projecoes_experimentais
ORDER BY categoria_fenabrave, data_referencia;
