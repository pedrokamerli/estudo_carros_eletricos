# Avaliação dos arquivos de mercado fornecidos

## Decisão de uso

Recebi três CSVs com histórico anual de modelos, vendas mensais por modelo e um conjunto municipal de emplacamentos. Mantive-os no projeto como material de exploração, mas **não os trato como fonte oficial** nem os misturo com as séries SENATRAN, FENABRAVE ou ABVE. Não encontrei citação, URL, relatório de origem, licença ou método de coleta nos arquivos.

Em 30/09/2026, confirmei que produzi esses CSVs com uma pesquisa no Gemini. Isso esclarece a ferramenta usada, mas não confirma cada número: ainda faltam as publicações originais e a metodologia. A base de notícias rastreáveis criada depois está separada, documentada em `docs/modelos_por_noticias.md`, sem reaproveitar esses valores como fatos confirmados.

## O que verifiquei

| Arquivo | Estrutura observada | Limitação principal |
| --- | --- | --- |
| `historico_vendas_ev_brasil.csv` | 15 linhas, cinco modelos BEV por ano, 2024–2026 | Não informa se os números são ano fechado ou acumulado, nem cita a fonte. |
| `vendas_ev_brasil_mes_a_mes.csv` | 160 linhas, 32 meses entre jan/2024 e ago/2026, cinco modelos BEV por mês | Não cita fonte e não cobre todas as tecnologias de eletrificação. |
| `dataset_mercado_ev_brasil.csv` | 19.901 linhas, 2021–2026, 23 municípios, 13 UFs e três categorias | Não tem campo de fonte; população, PIB per capita e frota são estimativas sem ano/base de referência informados. |

O terceiro arquivo passou por verificações **estruturais**: os 19.901 IDs são únicos, não há campos vazios e não encontrei contagens negativas. Isso não valida a origem nem a veracidade dos valores.

Também comparei os dois arquivos de modelos nos anos e nomes comuns. Em 2025, por exemplo, o histórico anual informa 11.500 para BYD Dolphin, enquanto a soma dos doze meses do outro arquivo é 13.507; para Volvo EX30 os valores são 4.800 e 6.420. Como as diferenças não vêm acompanhadas de explicação metodológica, não uso esses arquivos para afirmar volumes de mercado. Em 2024 e 2026, as listas de modelos também não coincidem integralmente.

## Como os mantenho isolados

Os carregadores registram `origem_oficial_confirmada = false`. As tabelas e exports mantêm “fornecido” no nome — por exemplo, `gold.emplacamentos_mensais_fornecidos`, `emplacamentos_mensais_dados_fornecidos.csv` e `ranking_marcas_modelos_dados_fornecidos.csv`. Posso usar esses dados para praticar filtros e visuais, mas o dashboard deve identificá-los como **não verificados** e não deve usá-los para conclusões do estudo principal.

## O que preciso para reclassificá-los

Preciso da URL ou publicação original de cada arquivo, a data de extração, definições das categorias/medidas e, no arquivo municipal, o ano e a metodologia das estimativas de população, PIB e frota. Se esses metadados não existirem, a decisão correta é deixá-los como exemplo não verificado ou removê-los das conclusões, não completar a origem por suposição.
