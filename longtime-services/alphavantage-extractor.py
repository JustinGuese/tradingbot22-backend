from datetime import date
from os import environ

import requests

from db import AlphaGainerLoserType, AlphaGainersLosers, db


def alphaPctConv(pctstring):
    return round(float(pctstring.replace("%", "")) / 100, 2)


def getGainersLosers():
    url = (
        "https://www.alphavantage.co/query/?function=TOP_GAINERS_LOSERS&apikey="
        + environ["ALPHAVANTAGE_KEY"]
    )

    response = requests.request("GET", url)
    response.raise_for_status()
    response = response.json()
    # first gainers
    for row in response["top_gainers"]:
        db.add(
            AlphaGainersLosers(
                ticker=row["ticker"],
                day=date.today(),
                category=AlphaGainerLoserType.GAINER,
                price=float(row["price"]),
                change_amount=float(row["change_amount"]),
                change_pct=alphaPctConv(row["change_percentage"]),
                volume=int(row["volume"]),
            )
        )
    # then losers
    for row in response["top_losers"]:
        db.add(
            AlphaGainersLosers(
                ticker=row["ticker"],
                day=date.today(),
                category=AlphaGainerLoserType.LOSER,
                price=float(row["price"]),
                change_amount=float(row["change_amount"]),
                change_pct=alphaPctConv(row["change_percentage"]),
                volume=int(row["volume"]),
            )
        )
    # then most active
    for row in response["most_actively_traded"]:
        db.add(
            AlphaGainersLosers(
                ticker=row["ticker"],
                day=date.today(),
                category=AlphaGainerLoserType.MOST_ACTIVE,
                price=float(row["price"]),
                change_amount=float(row["change_amount"]),
                change_pct=alphaPctConv(row["change_percentage"]),
                volume=int(row["volume"]),
            )
        )
    db.commit()


getGainersLosers()
