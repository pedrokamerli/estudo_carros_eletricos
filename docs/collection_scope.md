# Recorte de coleta: 2024 a 2026

Quero uma série histórica boa, mas leve o suficiente para estudar e rodar no meu computador.

## O que vou guardar para análise mensal

Vou coletar os arquivos de **combustível por UF e município** da SENATRAN de janeiro de 2024 até agosto de 2026. Fechei esse recorte em 01/10/2026; setembro não é pendência. Esses arquivos são menores e respondem às perguntas principais do projeto: evolução da frota eletrificada, crescimento, estados, municípios e capitais versus interior.

## O que não vou baixar em massa

Os arquivos de **marca e modelo** são muito maiores. Um único recorte mensal pode gerar mais de 1 GB após a extração. Por isso, vou baixá-los somente quando chegar à análise de marcas e modelos e apenas para meses de referência.

## Como a automação vai funcionar

1. Eu adiciono um arquivo oficial de combustível na pasta `data/bronze/senatran`.
2. O Python confere as colunas e registra problemas de qualidade.
3. O Python transforma todos os meses disponíveis em uma tabela Silver pronta para análise.
4. Quando eu quiser investigar marcas ou modelos, executo a coleta sob demanda de um único mês:

```powershell
python src/ingestion/download_senatran_brand_model.py --year 2025 --month 12
```

Se eu realmente for processar esse mês, adiciono `--extract`. Sem essa opção, mantenho apenas o ZIP e economizo espaço.

## Regra do projeto

Não vou baixar dados só porque estão disponíveis. Cada arquivo precisa ajudar a responder uma das perguntas de negócio.
