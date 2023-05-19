from datetime import datetime
from os import environ

from elasticsearch import Elasticsearch

MONTHDATE = datetime.now().strftime("%Y-%m")

ES = None
ES = Elasticsearch(environ.get("ELASTICSEARCH_URL", "http://localhost:9200"))

try:
    print(ES.info())
except Exception as e:
    ES = None


def logToElastic(index: str, document: dict):
    global ES
    if ES is not None:
        ES.index(index=index, body=document)
        
def logError(module: str, stock: str, error: str, severity = "medium"):
    error = {
        "module": module,
        "ticker" : stock,
        "error": error,
        "@timestamp" : datetime.utcnow().isoformat(),
        "severity": severity
    }
    logToElastic("tradingbot22_errors-" + datetime.now().strftime("%Y-%m"), error)