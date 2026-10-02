# Runbook operacional

Este documento descreve como reproduzo a entrega sem depender do Streamlit.

## Execução completa

No terminal do projeto:

```powershell
.venv\Scripts\python.exe -m src.run_project
```

A pipeline interrompe no primeiro erro para não publicar uma camada incompleta. Os dados brutos ficam em `data/bronze` (ignorados pelo Git); os exports pequenos e auditáveis ficam em `data/portfolio`.

## Auditoria antes do Power BI

```powershell
.venv\Scripts\python.exe -m src.analysis.build_project_audit
.venv\Scripts\python.exe -m unittest discover -s tests -q
```

O arquivo `data/portfolio/auditoria_exports.csv` registra linhas, colunas, nulos, duplicidades, negativos numéricos, período, hash SHA-256 e status de cada export. Negativos são sinalizados para interpretação — erros, variações e coordenadas podem ser negativos por definição — e não são apagados automaticamente.

## Camadas e responsabilidades

- **Bronze:** cópia bruta da fonte, com URL, data de captura e hash quando aplicável.
- **Silver:** limpeza, padronização e classificação, sem preencher ausências com zero.
- **Gold/portfolio:** agregações para perguntas de negócio, com grão e limitações descritos.
- **PostgreSQL:** tabelas `gold` para consumo analítico.
- **Streamlit/Power BI:** comunicação visual; não executam coleta nem alteram os dados.

## Regra de interpretação

Frota, emplacamentos, anúncios de preço, geração solar e pontos de recarga são indicadores diferentes. Só cruzo fatos quando a chave e o período permitem; caso contrário, publico a relação como hipótese e explico o que ainda precisa de validação.
