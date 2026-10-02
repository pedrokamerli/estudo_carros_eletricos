"""Consulta no painel público ABVE os modelos associados aos registros de Bauru."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import pandas as pd
import requests
from src.ingestion.download_abve_public_panel import ROOT, PAGE, fetch_metadata
from src.ingestion.capture_abve_aggregates import decode_rows

BRONZE = ROOT/"data/bronze/abve_public"
OUT = ROOT/"data/portfolio/abve_bauru_modelos.csv"


def literal(value):
    return {"Literal":{"Value":"'"+str(value).replace("'","''")+"'"}}


def query_city_model(metadata, api, headers, city="Bauru", state="SP"):
    sources={"e":"Cadastro_Estado","m":"Cadastro_Municipio","v":"BaseVendas_ABVE","t":"Tcalendario"}
    fields=[("t","Ano","Column"),("t","MêsNúmero","Column"),("e","Estado","Column"),("m","Município","Column"),
            ("v","Fabricante","Column"),("v","Modelo","Column"),("v","Tipo_Tecnologia","Column"),("v","Quantidade","Measure")]
    select=[{kind:{"Expression":{"SourceRef":{"Source":alias}},"Property":prop},"Name":prop} for alias,prop,kind in fields]
    # Power BI's public semantic query accepts In conditions for the two cadastro dimensions.
    def condition(alias, prop, value):
        return {"Condition":{"In":{"Expressions":[{"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":prop}}],"Values":[[literal(value)]]}}}
    semantic={"Version":2,"From":[{"Name":a,"Entity":e,"Type":0} for a,e in sources.items()],"Select":select,
              "Where":[condition("m","Município",city),condition("e","Estado",state)]}
    command={"SemanticQueryDataShapeCommand":{"Query":semantic,"Binding":{"Primary":{"Groupings":[{"Projections":list(range(len(fields)))}]},"DataReduction":{"DataVolume":6,"Primary":{"Window":{"Count":10000}}},"Version":1},"ExecutionMetricsKind":1}}
    body={"version":"1.0.0","queries":[{"Query":{"Commands":[command]},"ApplicationContext":{"DatasetId":metadata["models"][0]["dbName"],"Sources":[{"ReportId":metadata["exploration"]["reportId"]}]}}],"cancelQueries":[],"modelId":metadata["models"][0]["id"]}
    response=requests.post(api+"/public/reports/querydata?synchronous=true",headers=headers,json=body,timeout=90)
    response.raise_for_status()
    return response.json(),fields


def main():
    metadata,api,headers,embed=fetch_metadata()
    response,fields=query_city_model(metadata,api,headers)
    rows=decode_rows(response)
    frame=pd.DataFrame(rows,columns=[prop for _,prop,_ in fields])
    if frame.empty or len(frame)>=10000:
        raise ValueError("Consulta Bauru vazia ou atingiu o limite; não publico como completa.")
    frame=frame.rename(columns={"Ano":"ano_referencia","MêsNúmero":"mes_referencia","Estado":"uf","Município":"municipio","Fabricante":"marca","Modelo":"modelo","Tipo_Tecnologia":"tecnologia","Quantidade":"emplacamentos"})
    frame["data_referencia"]=pd.to_datetime(dict(year=frame.ano_referencia,month=frame.mes_referencia,day=1))
    frame["data_captura"]=datetime.now(timezone.utc).isoformat()
    frame["url_fonte"]=PAGE
    frame["escopo"]="Consulta ABVE filtrada por município Bauru e UF SP; fluxo de emplacamentos, não frota."
    frame["limite"]="O painel público não informa comprador, profissão, local de recarga ou transação individual. Registros são agregados por mês, modelo e município. Não usar para inferir causalidade ou ocupação de carregadores."
    BRONZE.mkdir(parents=True,exist_ok=True)
    payload=json.dumps({"campos":fields,"cidade":"Bauru","uf":"SP","resposta":response},ensure_ascii=False)
    digest=hashlib.sha256(payload.encode()).hexdigest()
    (BRONZE/f"bauru_modelos_{digest}.json").write_text(payload,encoding="utf-8")
    frame.to_csv(OUT,index=False)
    print(f"ABVE Bauru: {len(frame)} linhas de modelo; {frame.modelo.nunique()} modelos.")


if __name__ == "__main__":
    main()
