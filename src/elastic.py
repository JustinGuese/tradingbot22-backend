import base64
import json
from datetime import datetime
from os import environ

import requests
from elasticsearch import Elasticsearch

MONTHDATE = datetime.now().strftime("%Y-%m")

ES = None
OO = None

try:
    ES = Elasticsearch(environ.get("ELASTICSEARCH_URL", "http://localhost:9200"))
    print(ES.info())
except Exception as e:
    print("Elastic Error: ", e)
    ES = None
    
    
class OpenObserve:
    def __init__(self, user, password) -> None:
        bas64encoded_creds = base64.b64encode(bytes(user + ":" + password, "utf-8")).decode("utf-8")
        org = "tradingbot22"
        openobserve_host = "http://openobserve.openobserve.svc.cluster.local:5080"
        self.openobserve_url = openobserve_host + "/api/" + org + "/" + "[STREAM]" + "/_json"
        self.headers =  {"Content-type": "application/json", "Authorization": "Basic " + bas64encoded_creds}

    def index(self, index: str, document: dict):
        res = requests.post(self.openobserve_url.replace("[STREAM]", index), headers=self.headers, data=json.dumps(document))
        res.raise_for_status()
        
# openobserve support
user = "root@example.com"
password = "Complexpass#123"

OO = OpenObserve(user, password)


def logToElastic(index: str, document: dict):
    global ES, OO
    if ES is not None:
        ES.index(index=index, body=document)
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
        "@timestamp" : datetime.utcnow().isoformat(),
        "severity": severity
    }
    logToElastic("tradingbot22_errors-" + datetime.now().strftime("%Y-%m"), error)