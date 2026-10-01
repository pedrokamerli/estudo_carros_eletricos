# Perguntas de negócio e análise

Estas são as perguntas que definem o escopo do meu projeto. Vou responder cada uma com a fonte, período, unidade e limitações dos dados claramente identificados.

1. Como os emplacamentos de veículos elétricos evoluíram no Brasil ao longo dos anos?
2. Qual foi a taxa de crescimento anual desse mercado?
3. Quais estados possuem o maior número de veículos elétricos?
4. Quais estados apresentam o maior crescimento percentual?
5. Quais municípios possuem a maior quantidade de veículos elétricos?
6. Quais municípios apresentam maior participação de veículos elétricos em relação à frota total?
7. O crescimento dos veículos elétricos está concentrado nas capitais ou também está avançando para cidades do interior?
8. Quais marcas possuem maior participação no mercado de veículos elétricos?
9. Quais modelos de veículos elétricos são mais emplacados?
10. Quais tipos de eletrificação mais crescem no Brasil, como elétrico puro, híbrido e híbrido plug-in?
11. Existe relação entre PIB, renda, população e adoção de veículos elétricos nos municípios?
12. Quais municípios possuem boas condições econômicas, mas ainda baixa adoção de veículos elétricos?
13. Quais municípios apresentam maior potencial de crescimento para os próximos anos?
14. Quais regiões podem demandar maior expansão de infraestrutura de recarga?
15. É possível prever a evolução dos emplacamentos de veículos elétricos no Brasil?

## Respostas reproduzíveis do motor em 01/10/2026

As 15 respostas passam a ser geradas em `data/portfolio/perguntas_evidencias_motor.csv`, com pergunta, conclusão, tipo de evidência, arquivo de apoio e limite separados. O dashboard anterior não é atualizado automaticamente por esta entrega; a análise é executada fora dele.

Para a pergunta 7, calculo contribuição do interior ao acréscimo nacional de novos BEV/PHEV, além da participação na frota. Para a 11, acrescento associação parcial de renda/adoção controlando posições de população e UF, sem alegar causalidade. Para a 13, analiso Bauru e pares socioeconômicos escolhidos sem usar crescimento como critério. Isso identifica trajetórias passadas, não comprova potencial futuro.

Para a 14, substituo a comparação com frota ampla por participação de novos BEV/PHEV versus participação na rede pública/semipública. Norte, Centro-Oeste e Nordeste ficam acima de 1 nos dois recortes avaliados (jan–ago e jun–ago/2026), sinal de maior peso relativo das novas vendas que dos pontos. A prioridade é investigar uso e capacidade nessas regiões; não afirmo déficit ou número ideal de pontos. A estimativa nacional publicada de veículos plug-in acumulados desde 2022 fica separada de estoque SENATRAN e de fluxos de oito meses. O top 20 municipal de recarga não é inventário completo.

Preços: iniciei seis observações primárias, restritas a uma marca em 2024; quatro versões têm comparação descritiva com emplacamentos nacionais. Ainda faltam preços mensais comparáveis de múltiplas marcas, condições de compra e associação validada por versão para modelar efeitos de preço. Ausência desses dados não é preenchida com notícias genéricas, preços atuais ou CSVs sem origem.

ML: a nova escolha BEV obteve WAPE 23,57% contra 26,89% da persistência, mas o teste já era conhecido. PHEV permaneceu em 32,08% contra 23,10% da referência. Preservo as escolhas anteriores e não aprovo previsões operacionais. Novos meses precisam avaliar o protocolo congelado, sem reajuste para favorecer o resultado.

## Regra de leitura

Frota SENATRAN é um estoque observado em uma competência; emplacamentos FENABRAVE e ABVE são fluxos de vendas. As duas fontes de emplacamentos têm recortes e definições próprios e permanecem separadas até uma reconciliação metodológica documentada.
