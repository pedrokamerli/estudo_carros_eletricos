# Meu mapa exploratório de recarga

Consultei objetos com `amenity=charging_station` dentro da área administrativa do Brasil pela [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API). Uso um serviço público sem chave pessoal, com identificação do projeto, cache local e uma consulta por atualização. O arquivo original e a consulta ficam na Bronze; uma resposta parcial com `remark`, inclusive em HTTP 200, não substitui a captura anterior.

Na captura integrada nesta entrega há 392 objetos: 85 com acesso público declarado, 35 com acesso restrito declarado, 263 sem informação de acesso e nove com outros valores que precisam de revisão. Apenas sete têm município preenchido em `addr:city`. Não invento código IBGE nem atribuo município por proximidade a uma capital.

## O que a unidade significa

Cada linha é um objeto OSM identificado por tipo/ID, não a quantidade de carregadores, vagas ou conectores. Objetos diferentes podem representar o mesmo local físico; não prometo deduplicação física. Nós têm coordenadas próprias e vias/relações usam centro aproximado, marcado em `coordenada_aproximada`. Preservo tags de conectores em JSON e capacidade no formato original, sem somar padrões heterogêneos.

A [documentação da tag](https://wiki.openstreetmap.org/wiki/Tag:amenity%3Dcharging_station) explica o mapeamento de locais de recarga. É uma base comunitária incompleta, com acesso/operador/endereço frequentemente ausentes. Ausência no OSM não significa ausência de infraestrutura. Não concilio sua contagem de objetos com os pontos publicados pela ABVE/Tupi nem uso o snapshot atual como histórico mensal para treinar ML.

## Como reproduzo

```powershell
.\.venv\Scripts\python.exe -m src.ingestion.download_osm_charging
.\.venv\Scripts\python.exe -m src.transformation.osm_charging_to_silver
.\.venv\Scripts\python.exe -m src.database.load_osm_charging_to_postgres
.\.venv\Scripts\python.exe -m src.database.export_portfolio_data
```

A coleta reutiliza a Bronze existente; para solicitar uma captura nova uso `--refresh`. Não configuro chamadas paralelas ou repetição agressiva no servidor público. As etapas estão em `src.run_project`; um servidor indisponível interrompe a execução, sem publicar captura incompleta.

No PostgreSQL, `silver.recarga_osm` e `gold.recarga_osm` mantêm os objetos, referência da base OSM e horário real UTC da captura. O export separado é `data/portfolio/recarga_osm.csv`. No Power BI, uso latitude/longitude como coordenadas e `osm_id` como chave, expondo acesso, fonte e data. Não agrego essa tabela junto dos totais ABVE/Tupi.

## Licença e atribuição

Os dados OSM são disponibilizados sob [ODbL](https://www.openstreetmap.org/copyright). Mantenho esta camada separada dos outros dados e do código do projeto. O CSV e a tabela conservam licença, URL e atribuição; no mapa/dashboard público mostro **© OpenStreetMap contributors**, com link para a página de licença. Redistribuições dessa base/derivações precisam observar os requisitos de atribuição e compartilhamento aplicáveis da ODbL; a licença dos dados não é uma licença automática para o restante do código ou para as demais fontes.
