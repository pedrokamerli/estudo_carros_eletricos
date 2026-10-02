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

-- Confiro os cartões nacionais usando a fato dimensional na última competência.
SELECT data_referencia, SUM(frota_eletrificada) AS frota_eletrificada,
       SUM(frota_total) AS frota_total,
       SUM(frota_eletrificada) FILTER (WHERE NOT d.uf_informada) AS eletrificados_sem_uf
FROM bi.fato_frota_municipal f JOIN bi.dim_municipio d USING(municipio_id)
WHERE data_referencia = (SELECT MAX(data_referencia) FROM bi.fato_frota_municipal)
GROUP BY data_referencia;

-- Comparo jan-ago em anos distintos, sem somar ABVE com FENABRAVE.
SELECT EXTRACT(YEAR FROM data_referencia)::int AS ano,
       tecnologia, SUM(emplacamentos_mes) AS emplacamentos_jan_ago
FROM bi.fato_emplacamentos_plugin_abve
WHERE EXTRACT(MONTH FROM data_referencia) BETWEEN 1 AND 8
GROUP BY ano, tecnologia ORDER BY tecnologia, ano;

-- Posicionamento documental de preços por marca: não chamar de preço médio de mercado.
SELECT marca, anuncios, preco_minimo_reais, preco_mediano_reais,
       preco_maximo_reais, data_inicio, data_fim
FROM gold.precos_resumo_marca
ORDER BY preco_mediano_reais;

-- Bauru: modelos com ficha Inmetro e/ou preço, sem atribuir uma versão que o painel não informa.
SELECT marca, modelo, tecnologia, emplacamentos,
       autonomia_mediana_ensaio_km, consumo_mediano_mj_km,
       preco_mediano_reais, status_inmetro, status_preco
FROM gold.bauru_modelos_tecnologia_preco
ORDER BY emplacamentos DESC;

-- Catálogo técnico Inmetro para comparar autonomia e consumo por modelo.
SELECT marca, modelo, anos_catalogados, versoes_catalogadas,
       autonomia_min_ensaio_km, autonomia_mediana_ensaio_km,
       autonomia_max_ensaio_km, consumo_mediano_mj_km
FROM gold.inmetro_catalogo_modelo
ORDER BY marca, modelo;
