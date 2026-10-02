# Como aprofundei o projeto — 01/10/2026

## O que fiz e por quê

Comecei pela hipótese local: Bauru parece ter mais carros elétricos nas ruas. Em vez de transformar essa percepção em uma conclusão sobre recarga residencial ou energia solar, comparei os registros oficiais com cidades semelhantes.

O motor calcula uma síntese separada do dashboard. Bauru registrou 859 novos BEV/PHEV em jan–ago/2026, frente a 326 em 2025 e 256 em 2024. A alta de 163,5% ficou 27,3 pontos percentuais acima dos 136,2% do conjunto de dez pares. Calculo a taxa dos pares somando seus registros antes de dividir; não faço média simples de taxas. Bauru ocupa a sexta posição em volume entre as onze cidades. Crescimento rápido não significa maior mercado.

A seleção dos pares utiliza população e renda de 2022, padronizadas em escala logarítmica, entre cidades não capitais de SP. Não selecionei as cidades pelo crescimento. Isso melhora a comparação descritiva, mas não isola causas nem garante crescimento futuro.

## Preços com rastreabilidade

Ampliei os seis anúncios de 2024 para 39 observações de três marcas. Além das fontes BYD e GWM, incluí a [tabela pública oficial da Mercedes-Benz de fevereiro/2024](https://imprensa.mercedes-benz.com.br/storage/files/90C3pndHyyP2sBABMJriW4IVeAHASelLi59pUAMO.pdf), extraindo somente as oito linhas classificadas como elétricas. Guardei o PDF original, hash, data da captura, versão e condições. Quando o ano/modelo não foi declarado, deixei vazio.

Também gero estatísticas descritivas por marca e tecnologia: quantidade de anúncios, mínimo, mediana e máximo. Esses resumos organizam a comparação de posicionamento, mas não são média de mercado e não permitem estimar depreciação.

O painel ABVE também permite consultar município, marca e modelo simultaneamente. Para Bauru/SP obtive 597 linhas BEV/PHEV desde 2024, 117 modelos e reconciliação exata com o agregado municipal. Isso resolve a lacuna de modelos por cidade sem cruzamento artificial. Ainda não informa comprador ou local de recarga.

Para enriquecer a leitura técnica, gerei `bauru_modelos_tecnologia_preco.csv`. O pareamento é conservador no nível de modelo: 101 dos 117 modelos encontraram especificações Inmetro e 19 encontraram preço documental por chave textual compatível. Não atribuo uma versão específica quando o painel ABVE não a identifica exatamente.

Não comparei preços de versões diferentes como se fosse depreciação. Não preenchi meses ausentes, não estimei preço atual e não associei automaticamente essas versões aos emplacamentos municipais. A amostra é útil para documentar oferta; ainda não permite regressão confiável de preço versus vendas.

## Recarga: evidência local e limites

Obtive a malha oficial IBGE de Bauru, código 3506003. O coletor procura objetos OSM em uma caixa geográfica e depois verifica cada coordenada dentro do polígono, respeitando áreas vazias. Nós usam coordenadas próprias; vias/relações usam centro aproximado, com essa limitação registrada.

Nesta execução, o primeiro servidor Overpass retornou erro/timeout e o segundo também expirou. Para não parar a pesquisa, coletei três diretórios públicos complementares: Seguee reporta 14 estações, 11 rápidas e preços de R$ 1,54–2,98/kWh; Carregados registra o Bauru Shopping com confiança comunitária de 73%, potência média de 6 kW e status “Funcionando”; MapaVolt registra outro cadastro do shopping com 3 kW, status “Revisar” e confiança 12. Esses registros podem representar o mesmo local, por isso não somo as contagens. Eles são evidência de disponibilidade publicada, não censo, telemetria ou prova de funcionamento contínuo.

A ausência de uma captura OSM municipal não equivale à ausência de carregadores. O coletor reaproveita capturas válidas e só faz nova consulta com `--refresh`. É opcional e não impede a pipeline principal.

## Contexto solar municipal

Também baixei o cadastro oficial de geração distribuída da [ANEEL](https://dadosabertos.aneel.gov.br/dataset/relacao-de-empreendimentos-de-geracao-distribuida) e filtrei Bauru/SP. O recorte registra 9.934 empreendimentos fotovoltaicos e 79.600,59 kW cadastrados. Isso mede oferta municipal de geração distribuída; não identifica quais residências pertencem a donos de elétricos e não prova onde cada veículo recarrega.

Mesmo uma captura bem-sucedida não comprovará funcionamento ou cobertura completa. Para recomendar instalação de carregadores, ainda preciso verificar acesso, potência, preço, funcionamento, uso e recarga doméstica. Identificadores OSM podem representar o mesmo local físico; não os chamo de quantidade de carregadores. A licença ODbL e a atribuição são preservadas.

## Previsões: preservei uma aposta antes do resultado

Congelei as projeções de BEV/PHEV para novembro/2026, registradas em 01/10/2026 e treinadas até agosto. Setembro e outubro já não eram meses futuros para esse registro. O arquivo não é reescrito em novas execuções.

Isso prepara a comparação com resultados futuros, mas as observações ainda não estão disponíveis nesta entrega. O módulo `src.analysis.evaluate_frozen_predictions` já compara automaticamente os valores quando o mês encerra e a observação aparece na base. Até lá, os campos observado e erro ficam vazios e o status permanece pendente, nunca com erro zero inventado. Não há avaliação prospectiva concluída, aprovação operacional ou intervalos calibrados para os novos métodos. BEV melhorou em uma reanálise histórica com teste já conhecido; PHEV não superou a referência. Preservei os dois protocolos separados no painel.

## O que mudou na apresentação

- Capítulo 4 compara participação dos novos carros **com tomada** com participação dos pontos públicos/semipúblicos. A relação orienta investigação, não mede déficit.
- Capítulo 5 distingue protocolo original, reanálise exploratória e registro futuro pendente.
- Capítulo 6 lê as quinze respostas do motor, com tabela de evidência e limite de interpretação.
- Capítulo 8 mostra Bauru, evolução anual, dez pares e hipóteses locais.
- Capítulo 9 mostra preços documentados, filtros por marca e links primários.

## Como uso no Power BI

As novas tabelas estão em `gold` no PostgreSQL. Também compartilho os CSVs agregados em `data/portfolio/`.

| Tabela | Grão / uso | Cuidado |
|---|---|---|
| `bauru_estudo_sintese` | Uma linha de síntese | Percentuais não são somáveis |
| `estudo_bauru_pares_socioeconomicos` | Uma linha por cidade | Usar taxas com base explícita e distinguir frota de emplacamentos |
| `estudo_bauru_mensal` | Cidade × mês | Fluxo mensal BEV/PHEV; não frota |
| `precos_historicos_documentais` | Anúncio × versão × ano/modelo | Não somar preços ou interpolar meses |
| `ml_registro_prospectivo` | Tecnologia × mês futuro registrado | Não misturar projeção com observado |
| `ml_avaliacao_prospectiva` | Tecnologia × mês alvo | Erro vazio significa pendente, não previsão perfeita |
| `perguntas_evidencias_motor` | Uma linha por pergunta | Mostrar resposta, evidência e limite juntos |
| `inteligencia_recarga_regional` | Uma linha por região | Não relacionar diretamente aos fatos de vendas causando duplicação |

Não existe tabela de modelos vendidos por município: os fatos de modelo e município são recortes separados. Um cruzamento pelo mês não descobre o modelo vendido em Bauru.

## O que ainda falta

1. Obter uma captura local íntegra e verificar funcionamento dos pontos com operadores ou visita.
2. Ampliar preços comparáveis por versão/mês/marca, com fontes verificáveis.
3. Coletar observações posteriores e comparar com as projeções congeladas; não ajustar retrospectivamente os valores registrados.
4. Realizar pesquisa voluntária para medir recarga em casa, energia solar e destinos. Ainda não coletei respostas.
5. Montar a entrega visual final no Power BI.

Testei os novos parsers, geografia com áreas vazias, base agregada de comparação, impossibilidade de reescrita do registro, exports reais, avaliação sem inventar observações, pareamento conservador de modelos e as nove páginas Streamlit. A suíte atual contém 87 testes, com quatro integrações externas ignoradas quando o serviço não está disponível. Conferi a carga transacional e a contagem das tabelas de inteligência, incluindo preços, Inmetro e modelos enriquecidos.
