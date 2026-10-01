# Aplicações de ML e novas fontes

Atualizado em 01/10/2026. Meu recorte observado está fechado em janeiro/2024–agosto/2026. Meses posteriores só podem aparecer como projeções identificadas, nunca como observações.

## O que consigo estudar com responsabilidade

| Aplicação | O que tenho e posso implementar | Limite e dado que falta |
| --- | --- | --- |
| Vendas futuras por mês, UF, cidade ou marca | Experimentos nacionais BEV/PHEV ABVE e categorias FENABRAVE; rankings mensais de marcas são complementares | Emplacamento é aproximação de vendas realizadas, não toda demanda. Não distribuo previsão nacional pela participação atual para chamar isso de previsão municipal. Top rankings não são universo completo por marca. Preciso de alvos locais/marca contínuos e comparáveis. |
| Crescimento regional da frota | Nova série mensal das cinco regiões e parcela sem UF; backtest Ridge/Random Forest e referências simples, horizontes 1–3 meses | Estoque não é emplacamento. Revisões, transferências e baixas também mudam a frota. Definição SENATRAN ampla, não só BEV. Não somo automaticamente as projeções independentes para criar previsão nacional. |
| Revenda e depreciação | Localizei consulta oficial FIPE | FIPE não oferece API oficial e preço médio não contém quilometragem, saúde da bateria nem preço efetivo de transação. Não baixei base completa nem tratei API de terceiro como oficial. Preciso de transações históricas e identificadores de versão/ano; anúncios não equivalem a venda. |
| Locais de carregadores e demanda por horário | Frota municipal, indicadores IBGE, mapa OSM parcial e ABVE/Tupi permitem triagem exploratória | Não possuo sessões brasileiras por estação, ocupação, potência, conexão e kWh. Oportunidade municipal não é localização ótima de instalação. Preciso de restrições de rede, terreno, acesso e custos. |
| Probabilidade individual de compra | IBGE permite estudar associação agregada municipal | Município de renda alta não define probabilidade de compra de uma pessoa. Preciso de amostra consentida/adequadamente anonimizada de clientes, decisões de compra e atributos anteriores à decisão, com revisão LGPD. Não vou inventar perfis ou rótulos. |
| Autonomia real e consumo | Localizei tabelas oficiais PBEV Inmetro com modelo/versão e consumo/autonomia padronizados | Ainda não ingeri essas tabelas. Ensaios padronizados não são autonomia real por trânsito/clima/relevo. Para ML real preciso de trajetos e telemetria com consumo observado; clima sozinho não fornece o alvo. |
| Manutenção e falha da bateria | Localizei estudos EVBattery e dados experimentais NASA | Não integrei esses dados estrangeiros/experimentais ao mercado brasileiro. Capacidade/saúde estimada não é falha mecânica rotulada. Preciso de histórico BMS, temperatura/ciclos/SOH e eventos de manutenção/falha. |
| Impacto na rede e picos de recarga | Nova coleta ONS de carga horária 2024–ago/2026 e perfis mês/hora/subsistema | ONS mede carga agregada, não contribuição de VEs. SE é Sudeste/Centro-Oeste, não UF. Preciso de sessões de recarga e alimentadores/transformadores para medir impacto local. Cenários com premissas seriam simulações, não previsão aprendida de recarga brasileira. |
| Incentivos e políticas | BCB oferece juros de veículos, Selic mensal e IPCA; encontrei fontes governamentais sobre tributação | Contexto econômico não identifica efeito causal de política. Preciso de eventos normativos verificados, tratamento/exposição, grupo comparável, preços e produção/importação. Notícia inicial e ato publicado podem divergir; não transformo anúncio em alíquota efetiva. |

## Novos dados efetivamente coletados

### BCB/SGS

Guardo três séries mensais com 32 observações cada, total de 96. Todas estão em percentual ao mês, não anual:

- 433: variação mensal IPCA, indicador do IBGE disponibilizado pelo SGS.
- 4390: Selic acumulada no mês. Não é meta Selic anual do Copom.
- 25471: taxa média mensal de juros de crédito livre para pessoas físicas na aquisição de veículos. Não é exclusiva de elétricos.

Minha Bronze guarda JSON original, URL exata, captura UTC e hash. O cache evita consultas repetidas. `--refresh` coleta nova versão e mantém snapshots anteriores. A Silver interrompe se houver mês ausente, duplicado, não finito ou fora do recorte. Inflação negativa é permitida.

```powershell
python -m src.ingestion.download_bcb_context
python -m src.ingestion.download_bcb_context --refresh
```

As séries ficam em `silver.contexto_economico_bcb`, `gold.contexto_economico_bcb` e no export `contexto_economico_bcb.csv`.

### ONS

Baixei os três arquivos anuais de carga horária em Parquet e filtrei o resultado até 31/08/2026. O arquivo de 2026 contém registros posteriores ao corte, mas eles ficam apenas no original Bronze e não entram em Silver/Gold/análise.

São 3.072 grupos: 32 meses × quatro subsistemas × 24 horas. A carga média e a máxima são potências em MWmed, não energia mensal em kWh. As contagens expõem a cobertura de cada grupo; nesta captura todos os grupos têm 100% das horas esperadas. Preservo a hora como publicada e não suponho fuso UTC sem documentação.

```powershell
python -m src.ingestion.download_ons_load
python -m src.ingestion.download_ons_load --refresh
```

O catálogo informa Creative Commons Atribuição. Mantenho atribuição ao ONS e URL. Silver local: `perfil_carga_ons.parquet`; Gold/export: `perfil_carga_ons_mensal_hora`.

## Experimentos que executei

### Contexto econômico e vendas

Comparo persistência, Ridge sem contexto e Ridge com três indicadores BCB. Horizonte de um mês, treino mínimo de 18 meses, sete alvos de validação e sete de teste por tecnologia. Uso contexto dois meses anterior ao último mês observado de vendas; nenhum indicador do mês previsto entra nas variáveis. A padronização é ajustada só nos exemplos de treino de cada origem.

Isso reduz risco de divulgação tardia, mas **não prova disponibilidade histórica**: não possuo vintages nem datas de divulgação de todos os valores. O backtest usa snapshots atuais, não deve ser chamado de simulação operacional em tempo real. Não faço projeções econômicas futuras com valores inventados.

Resultado de um passo: BEV escolheu persistência (WAPE teste 13,98%); PHEV escolheu Ridge sem contexto (22,59%), que perdeu para persistência (11,14%). O Ridge com macro não foi selecionado. Portanto, nesta configuração, a nova fonte não justificou trocar o modelo por um mais complexo. Esses erros não são diretamente comparáveis com a média dos três horizontes dos outros experimentos.

```powershell
python -m src.analysis.forecast_macro_abve
```

### Frota regional

Agrego a Silver SENATRAN por UF/região sem perder a parcela sem UF. Exijo continuidade das 32 competências por grupo. Calculo crescimento observado contra o mesmo mês do ano anterior; os primeiros 12 meses ficam nulos, não zero.

Nas cinco regiões treino apenas a parcela com UF conhecida. Comparo persistência, média móvel, sazonalidade de 12 meses, Ridge e Random Forest com a mesma seleção temporal do experimento nacional. O Ridge foi selecionado na validação e teve WAPE médio de teste de 8,44% no Centro-Oeste, 11,15% no Nordeste, 11,90% no Norte, 8,03% no Sudeste e 8,61% no Sul. Superou persistência nas cinco regiões neste teste.

São 900 previsões retrospectivas, 150 linhas de métricas, cinco escolhas e 15 projeções experimentais. Não há intervalo calibrado, aprovação operacional ou prova de que a mesma vantagem continuará. Mais rápido em percentual e maior aumento absoluto são perguntas diferentes: minha série fornece os dois componentes para análise, sem garantir um ranking futuro.

```powershell
python -m src.analysis.forecast_regional_fleet
```

## Fontes pesquisadas e estado da integração

- [BCB — dados abertos](https://www.bcb.gov.br/acessoinformacao/dadosabertos): integrado. [Metadados SGS 25471](https://www3.bcb.gov.br/sgspub/consultarmetadados/consultarMetadadosSeries.do?hdOidSerieSelecionada=25471&method=consultarMetadadosSeriesInternet) e [Selic 4390](https://dadosabertos.bcb.gov.br/pt_PT/dataset/4390-taxa-de-juros---selic-acumulada-no-mes).
- [ONS — curva de carga](https://dados.ons.org.br/dataset/curva-carga): integrado como contexto agregado, não alvo de recarga EV.
- [Inmetro — tabelas PBEV](https://www.gov.br/inmetro/pt-br/assuntos/regulamentacao/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica/veiculos-automotivos-pbe-veicular/): localizado, extração ainda pendente. [Definição do consumo elétrico](https://www.gov.br/inmetro/pt-br/acesso-a-informacao/perguntas-frequentes/avaliacao-da-conformidade/etiquetagem-para-veiculos-leves/como-e-calculado-o-consumo-dos-carros-eletricos/).
- [FIPE — consulta oficial](https://veiculos.fipe.org.br/): localizado, não integrado; o site declara que não disponibiliza API.
- [Caltech ACN-Data](https://ev.caltech.edu/dataset.html): sessões reais em instalações dos EUA. API exige cadastro/token; opção de estudo separado, não baixada e não evidência de demanda brasileira.
- [EVBattery — artigo dos autores](https://arxiv.org/abs/2201.12358): pesquisa de saúde/capacidade, não integrado; disponibilidade/licença/representatividade precisam de revisão antes de uso.
- [NASA — battery aging](https://data.nasa.gov/dataset/groups/li-ion-battery-aging-datasets): candidato para projeto experimental separado; não integrado nem rotulado como frota brasileira.
- [Agência Gov — tributação oficializada](https://agenciagov.ebc.com.br/noticias/202311/retomada-de-tributacao-para-veiculos-eletrificados-e-oficializada-pelo-dou): fonte governamental localizada; não criei variável de política baseada apenas na notícia. Link original MDIC redirecionou para autenticação nesta consulta. A verificação de atos e exceções permanece pendente.

## Como automatizo e o que ainda não automatizei

`python -m src.run_project` já inclui BCB, ONS, experimentos econômicos/regionais, cargas PostgreSQL, modelo dimensional e exports. Ele para no primeiro erro. A execução é iniciada manualmente; não criei serviço recorrente, tarefa do Windows ou infraestrutura de nuvem. O cache evita baixar tudo novamente.

Não existe ainda extração automática aprovada dos snapshots dos painéis ABVE nem série completa por modelo. Não contorno login, captcha ou limites da fonte. Só considero uma nova fonte integrada depois de validar unidade, alvo, recorte, licença, chaves e proveniência.

## Próximos passos priorizados

Verifiquei a execução completa em 01/10/2026. Os 40 casos unitários passaram; os quatro testes de integração BI/PostgreSQL também passaram quando habilitados separadamente. O teste unitário padrão ignora esses quatro casos de banco. Não executei as funções legadas exclusivas de pytest.

1. Completar extração do PBEV por modelo/versão e validar a classificação sem confundir ensaio com medição real.
2. Buscar fonte mensal comparável de emplacamentos municipais e por marca/modelo. Ranking parcial ausente não significa zero.
3. Ampliar avaliação de frota por UF, testar erros por horizonte e calibrar intervalos antes de publicar previsão como recomendação.
4. Para recarga, buscar parceria/base brasileira com sessões e ocupação; enquanto faltar, apresentar apenas mapa parcial e triagem territorial.
5. Reservar compra individual, bateria, autonomia real e depreciação com bateria/km para estudos separados ou parceria de dados. Não misturar bases estrangeiras com brasileiras para preencher lacunas.
