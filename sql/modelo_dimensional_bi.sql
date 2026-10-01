-- Separo o modelo de consumo das tabelas intermediárias da Gold.
CREATE SCHEMA IF NOT EXISTS bi;

CREATE TABLE IF NOT EXISTS bi.dim_data (
    data DATE PRIMARY KEY,
    ano SMALLINT NOT NULL,
    mes SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    dia SMALLINT NOT NULL,
    trimestre SMALLINT NOT NULL,
    ano_mes CHAR(7) NOT NULL,
    ano_mes_ordem INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS bi.dim_municipio (
    municipio_id TEXT PRIMARY KEY,
    uf TEXT NOT NULL,
    municipio TEXT NOT NULL,
    uf_sigla CHAR(2),
    pais TEXT NOT NULL,
    uf_informada BOOLEAN NOT NULL,
    tipo_localidade TEXT NOT NULL CHECK (tipo_localidade IN ('capital', 'interior', 'nao_informado')),
    codigo_ibge VARCHAR(7) CHECK (codigo_ibge ~ '^[0-9]{7}$'),
    populacao_censo_2022 BIGINT,
    pib_per_capita_aproximado NUMERIC,
    renda_domiciliar_per_capita_2022 NUMERIC,
    oportunidade_preliminar BOOLEAN,
    data_referencia_indicadores_frota DATE,
    UNIQUE (uf, municipio)
);

CREATE TABLE IF NOT EXISTS bi.fato_frota_municipal (
    data_referencia DATE NOT NULL REFERENCES bi.dim_data(data),
    municipio_id TEXT NOT NULL REFERENCES bi.dim_municipio(municipio_id),
    frota_total BIGINT NOT NULL CHECK (frota_total >= 0),
    frota_eletrificada BIGINT NOT NULL CHECK (frota_eletrificada >= 0 AND frota_eletrificada <= frota_total),
    PRIMARY KEY (data_referencia, municipio_id)
);

CREATE TABLE IF NOT EXISTS bi.fato_emplacamentos_plugin_abve (
    data_referencia DATE NOT NULL REFERENCES bi.dim_data(data),
    tecnologia TEXT NOT NULL CHECK (tecnologia IN ('BEV', 'PHEV')),
    emplacamentos_mes BIGINT NOT NULL CHECK (emplacamentos_mes >= 0),
    fonte TEXT NOT NULL CHECK (fonte = 'ABVE'),
    url_fonte TEXT NOT NULL,
    metodo_extracao TEXT NOT NULL,
    PRIMARY KEY (data_referencia, tecnologia)
);

CREATE TABLE IF NOT EXISTS bi.fato_emplacamentos_fenabrave (
    data_referencia DATE NOT NULL REFERENCES bi.dim_data(data),
    categoria_fenabrave TEXT NOT NULL,
    segmento_veiculos TEXT NOT NULL,
    emplacamentos_mes BIGINT NOT NULL CHECK (emplacamentos_mes >= 0),
    fonte TEXT NOT NULL CHECK (fonte = 'FENABRAVE'),
    PRIMARY KEY (data_referencia, categoria_fenabrave, segmento_veiculos)
);

-- Renovo o conjunto em uma transação; as chaves não são números que mudam a cada carga.
TRUNCATE bi.fato_frota_municipal, bi.fato_emplacamentos_plugin_abve,
         bi.fato_emplacamentos_fenabrave, bi.dim_municipio, bi.dim_data;

-- O calendário é diário/contínuo para inteligência temporal, mas as fatos são mensais.
-- Incluo anos completos e espaço para três meses futuros sem inventar fatos nesses dias.
INSERT INTO bi.dim_data
WITH limites AS (
    SELECT MIN(make_date(ano_referencia::int, mes_referencia::int, 1)) AS inicio,
           (date_trunc('year', MAX(make_date(ano_referencia::int, mes_referencia::int, 1))
                                  + interval '3 months') + interval '1 year - 1 day')::date AS fim
    FROM silver.frota_total_municipal
)
SELECT d::date, EXTRACT(YEAR FROM d)::smallint, EXTRACT(MONTH FROM d)::smallint,
       EXTRACT(DAY FROM d)::smallint, EXTRACT(QUARTER FROM d)::smallint,
       to_char(d, 'YYYY-MM'), to_char(d, 'YYYYMM')::integer
FROM limites CROSS JOIN LATERAL generate_series(inicio, fim, interval '1 day') AS dias(d);

INSERT INTO bi.dim_municipio
WITH localidades AS (
    SELECT DISTINCT uf, municipio FROM silver.frota_total_municipal
)
SELECT md5(jsonb_build_array(l.uf, l.municipio)::text), l.uf, l.municipio,
       c.sigla, 'Brasil', l.uf <> 'Sem Informação',
       CASE WHEN l.uf = 'Sem Informação' THEN 'nao_informado'
            WHEN l.municipio = c.capital THEN 'capital' ELSE 'interior' END,
       trim(p.codigo_ibge), p.populacao_censo_2022, p.pib_per_capita_aproximado,
       p.rendimento_domiciliar_per_capita_medio_2022_reais,
       o.oportunidade_preliminar,
       make_date(p.ano_referencia_frota::int, p.mes_referencia_frota::int, 1)
FROM localidades l LEFT JOIN capital_lookup c ON l.uf = c.uf
LEFT JOIN gold.penetracao_municipal_ibge p ON l.uf = p.uf AND l.municipio = p.municipio
LEFT JOIN gold.oportunidade_municipal_preliminar o ON l.uf = o.uf AND l.municipio = o.municipio;

-- A frota total é meu universo; zero significa sem registros eletrificados no recorte.
-- Não multiplico o denominador pelo número de categorias/combustíveis eletrificados.
INSERT INTO bi.fato_frota_municipal
WITH eletrificados AS (
    SELECT ano_referencia, mes_referencia, uf, municipio,
           SUM(quantidade_veiculos)::bigint AS quantidade
    FROM silver.frota_eletrificada GROUP BY ano_referencia, mes_referencia, uf, municipio
)
SELECT make_date(t.ano_referencia::int, t.mes_referencia::int, 1),
       md5(jsonb_build_array(t.uf, t.municipio)::text), t.total_veiculos,
       COALESCE(e.quantidade, 0)
FROM gold.frota_total_municipal t LEFT JOIN eletrificados e
USING (ano_referencia, mes_referencia, uf, municipio);

-- Preservo alvos e taxonomias em fatos distintas. Não existe uma soma ABVE+FENABRAVE.
INSERT INTO bi.fato_emplacamentos_plugin_abve
SELECT data_referencia, tecnologia, emplacamentos_mes, fonte, url_fonte, metodo_extracao
FROM gold.abve_plugin_mensais;

INSERT INTO bi.fato_emplacamentos_fenabrave
SELECT make_date(ano_referencia::int, mes_referencia::int, 1), categoria_fenabrave,
       segmento_veiculos, emplacamentos_mes, 'FENABRAVE'
FROM gold.emplacamentos_fenabrave_mensais;
