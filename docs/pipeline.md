# Primeira pipeline local

## Objetivo

Transformar o arquivo bruto da SENATRAN, preservado na camada Bronze, em uma tabela Silver de frota eletrificada pronta para análises posteriores.

## Fluxo

```text
Excel da SENATRAN (Bronze)
        ↓
Validação de colunas obrigatórias
        ↓
Classificação explícita dos combustíveis eletrificados
        ↓
Classificação da localidade: capital, interior ou não informado
        ↓
Parquet da frota eletrificada (Silver)
```

## Regras atuais

- A transformação considera combustíveis com componente elétrico, híbrido e híbrido plug-in.
- Registros sem UF não são descartados: recebem `uf_informada = False` e `tipo_localidade = nao_informado`.
- A fonte Bronze nunca é modificada.

## Como executar

```powershell
.\.venv\Scripts\python.exe -m src.run_pipeline
```

## Como testar as regras

```powershell
.\.venv\Scripts\python.exe -m pytest
```
