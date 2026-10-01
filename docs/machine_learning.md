# Meu experimento de previsão mensal

Quero avaliar se o histórico mensal permite antecipar os emplacamentos de curto prazo. Uso a série FENABRAVE de **autos e comerciais leves**, de fevereiro/2024 a agosto/2026: 31 observações por categoria, elétricos e híbridos. Janeiro/2024 está fora porque cobre somente autos. Não misturo frota SENATRAN nem categorias ABVE nesse alvo.

## Como preparei o experimento

Comparei persistência do último mês, média dos três últimos meses, sazonal ingênuo de 12 meses, regressão Ridge e Random Forest. A Ridge usa padronização ajustada somente no treino e `alpha=10`. A floresta usa 100 árvores, profundidade máxima 3, mínimo de 3 exemplos por folha e semente 42. Fixei esses parâmetros antes do teste; não fiz busca de parâmetros na pequena amostra.

As variáveis são logaritmos dos três últimos emplacamentos, média dos três logaritmos, índice temporal e seno/cosseno do mês previsto. Para cada horizonte (1, 2 e 3 meses), ajusto um modelo direto: o alvo é aquele mês futuro, e todos os exemplos de treino já têm seu alvo observado antes da origem. Transformo o alvo com `log1p` e volto para a escala de veículos com `expm1`, limitando previsões negativas a zero.

Começo com 18 meses disponíveis e expando o treino a cada origem. A validação usa alvos de agosto/2025 a janeiro/2026. Escolho um método por categoria pela média dos WAPEs dos três horizontes, com peso igual por horizonte. Congelo essa escolha antes de avaliar os alvos de fevereiro a agosto/2026. No teste, o modelo é reajustado quando novas observações passadas ficam disponíveis, sem mudar a regra escolhida. Não faço divisão aleatória.

Uma origem pode gerar até três previsões; por isso o detalhe contém vários prognósticos do mesmo mês, com origens/horizontes diferentes. São 330 linhas de detalhe e 60 linhas de métricas (2 categorias × 2 etapas × 5 métodos × 3 horizontes). São janelas sobrepostas, não 330 meses independentes. Cada linha informa fim de treino, fonte, segmento, versão do scikit-learn e SHA-256 do Parquet de entrada.

## O que encontrei

Na validação, a média de três meses venceu para elétricos (WAPE médio 16,21%); no teste, chegou a 36,36%, pior que a persistência (26,94%). Para híbridos, a persistência foi escolhida: WAPE médio de validação 14,66% e teste 17,58%. Os modelos Ridge e Random Forest não foram selecionados. Não troquei a escolha depois de olhar o teste.

Esse resultado mostra que acrescentar ML não garantiu ganho preditivo. O crescimento recente e o histórico curto dificultam extrapolar o padrão. A execução gera seis projeções **experimentais** para setembro–novembro/2026, reajustando o método selecionado com o histórico até agosto/2026. Setembro permanece previsto, nunca observado, até a fonte publicar o fechamento. Não há intervalo de previsão calibrado; não uso essas projeções como recomendação operacional ou prova de crescimento futuro. O método de elétricos não passou a comparação com a referência no teste.

## Como interpreto os erros

- MAE: erro absoluto médio em veículos.
- RMSE: erro que dá mais peso a falhas grandes, também em veículos.
- WAPE: soma dos erros absolutos dividida pela soma dos reais, em percentual, dentro de cada categoria/etapa/horizonte.
- WAPE médio da seleção: média simples dos três WAPEs por horizonte; não é o WAPE global nem o MAPE do backtest anterior.

## Como reproduzo e consulto

Depois de instalar `requirements.txt` e gerar a Silver:

```powershell
.\.venv\Scripts\python.exe -m src.analysis.forecast_ml
.\.venv\Scripts\python.exe -m src.database.load_ml_to_postgres
```

Os módulos também fazem parte de `src.run_project`. O PostgreSQL contém `gold.ml_backtest_detalhe`, `gold.ml_backtest_metricas`, `gold.ml_selecao_modelos` e `gold.ml_projecoes_experimentais`. Os quatro CSVs de mesmo nome estão em `data/portfolio/`. No dashboard, mostro o erro do teste junto das projeções e filtro categoria, método, etapa e horizonte antes de agregar.

Os testes temporais verificam que alterar valores futuros não muda uma previsão anterior e que meses faltantes e valores negativos são rejeitados. A abordagem segue a [documentação de previsão com variáveis defasadas do scikit-learn](https://scikit-learn.org/stable/auto_examples/applications/plot_time_series_lagged_features.html) e a [regressão Ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html).
