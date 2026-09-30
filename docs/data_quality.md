# Qualidade de dados — SENATRAN

## Objetivo

Antes de transformar a Bronze em Silver, a pipeline verifica se a fonte pode ser usada com segurança.

## Regras críticas

- As colunas `UF`, `Município`, `Combustível Veículo` e `Qtd. Veículos` precisam existir.
- Esses campos não podem ter valores ausentes.
- A quantidade de veículos deve ser numérica e maior que zero.

Se alguma regra crítica falhar, a pipeline para e não cria uma Silver nova.

## Regra de alerta

`UF = Sem Informação` não elimina o registro, pois o veículo ainda contribui para o total nacional. A linha recebe marcação de localização não informada e fica fora de rankings geográficos.

## Resultado

Cada execução cria um relatório JSON em `data/quality/senatran/`. Ele registra total de linhas, valores nulos, quantidades inválidas e veículos sem UF.
