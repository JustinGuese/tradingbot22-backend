from datetime import datetime
from os import environ

from pymongo import MongoClient

MONTHDATE = datetime.now().strftime("%Y-%m")

MONGOCLIENT = MongoClient(environ.get("MONGO_URL"))
mongodb = MONGOCLIENT["tradingbot22"]
ERRORCOLLECTION = mongodb["tradingbot22_errors"]

def logToElastic(index: str, document: dict):
    ERRORCOLLECTION.insert_one(document)
        
def logError(module: str, stock: str, error: str, severity = "medium"):
    error = {
        "module": module,
        "ticker" : stock,
        "error": error,
        "@timestamp" : datetime.utcnow().isoformat(),
        "severity": severity
    }
    logToElastic("tradingbot22_errors", error)