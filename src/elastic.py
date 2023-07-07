import base64
import json
from datetime import datetime
from os import environ

import requests
# from elasticsearch import Elasticsearch
from python_openobserve.openobserve import OpenObserve

MONTHDATE = datetime.now().strftime("%Y-%m")

# ES = None

# try:
#     ES = Elasticsearch(environ.get("ELASTICSEARCH_URL", "http://localhost:9200"))
#     print(ES.info())
# except Exception as e:
#     print("Elastic Error: ", e)
#     ES = None
    
        
# openobserve support
OO = OpenObserve("root@example.com", "Complexpass#123") # host = "http://openobserve.openobserve.svc.cluster.local:5080"

def logToElastic(index: str, document: dict):
    global  OO
    # if ES is not None:
    #     ES.index(index=index, body=document)
    if OO is not None:
        try:
            OO.index(index, document)
        except Exception as e:
            print("skip - OpenObserve Error: ", str(e))
        
def logError(module: str, stock: str, error: str, severity = "medium"):
    error = {
        "module": module,
        "ticker" : stock,
        "error": error,
        "@timestamp" : datetime.utcnow(),
        "severity": severity
    }
    logToElastic("tradingbot22_errors-" + datetime.now().strftime("%Y-%m"), error)