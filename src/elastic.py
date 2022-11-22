from os import environ

from elasticsearch import Elasticsearch

try:
    ES = Elasticsearch(environ.get("ES_HOST", "http://elasticsearch-service.elk.svc.cluster.local:9200"))
    info = ES.info()
except Exception as e:
    print(e)
    ES = None

def logToElastic(index: str, document: dict):
    global ES
    if ES is not None:
        ES.index(index=index, document=document)
    else:
        print("Elasticsearch not available. skip log.")