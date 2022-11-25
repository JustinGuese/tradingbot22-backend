from datetime import datetime
from os import environ

from elasticsearch import Elasticsearch

MONTHDATE = datetime.now().strftime("%Y-%m")

try:
    ES = Elasticsearch(environ.get("ES_HOST", "http://elasticsearch-service.elk.svc.cluster.local:9200"))
    info = ES.info()
except Exception as e:
    print(e)
    ES = None

def logToElastic(index: str, document: dict):
    global ES, MONTHDATE
    if ES is not None:
        # adding month data such that we can delete old data later on
        ES.index(index=index+"-"+MONTHDATE, document=document)
    else:
        print("Elasticsearch not available. skip log.")
        
def logError(module: str, stock: str, error: str, severity = "medium"):
    error = {
        "module": module,
        "ticker" : stock,
        "error": error,
        "@timestamp" : datetime.utcnow().isoformat(),
        "severity": severity
    }
    logToElastic("tradingbot22_errors", error)