from os import environ

from elasticsearch import Elasticsearch

try:
    ES = Elasticsearch(environ.get("ES_HOST", "https://elasticsearch-service.elk.svc.cluster.local:9200"))
except Exception as e:
    print(e)
    ES = None

def logToElastic(index: str, document: dict):
    global ES
    if ES:
        ES.index(index=index, document=document)
    else:
        print("Elasticsearch not available. skip log.")