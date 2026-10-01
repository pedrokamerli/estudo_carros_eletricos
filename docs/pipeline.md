# Pipeline local

Meu estudo observado usa janeiro/2024–agosto/2026. Para executar todas as fontes públicas e integrações, uso:

```powershell
.\.venv\Scripts\python.exe -m src.run_project
```

Isso inclui SENATRAN, IBGE, FENABRAVE, OSM, BCB e ONS; transformação dos snapshots ABVE; avaliações de ML; PostgreSQL, esquema dimensional BI e exports. Os snapshots ABVE continuam com captura manual. A execução para no primeiro erro e não agenda tarefas recorrentes. BCB e ONS aceitam `--refresh` nos seus coletores para renovar o cache mantendo versões anteriores.

A seção abaixo descreve especificamente a transformação SENATRAN, chamada pelo fluxo completo. As referências do ONS e os limites dos novos experimentos estão em `docs/novas_aplicacoes_ml.md`.

## Objetivo

Transformar o arquivo bruto da SENATRAN, preservado na camada Bronze, em uma tabela Silver de frota eletrificada pronta para análises posteriores.

## Fluxo

```text
Excel da SENATRAN (Bronze)
        ↓
Validação de colunas obrigatórias
        ↓
Validação de qualidade e relatório JSON
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
- Valores ausentes em campos essenciais e quantidades não positivas interrompem a pipeline.
- Registros sem UF geram alerta no relatório, mas permanecem na tabela Silver.

## Como executar

```powershell
.\.venv\Scripts\python.exe -m src.run_pipeline
```

## Como testar as regras

O comando abaixo executa os casos `unittest.TestCase`; ele não executa funções legadas exclusivas de pytest. Os quatro testes de integração BI com PostgreSQL são opcionais e exigem `$env:EV_RUN_BI_INTEGRATION_TESTS='1'`.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'
```
