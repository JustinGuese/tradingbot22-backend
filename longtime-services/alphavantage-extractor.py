from datetime import date, datetime
from os import environ

import requests

from db import (
    AlphaGainerLoserType,
    AlphaGainersLosers,
    AlphaSentiment,
    AlphaSentimentArticle,
    SentimentCategory,
    db,
)

BASEURL = "https://www.alphavantage.co/query/"


def alphaPctConv(pctstring):
    return round(float(pctstring.replace("%", "")) / 100, 2)


def getGainersLosers():
    url = BASEURL + "?function=TOP_GAINERS_LOSERS&apikey=" + environ["ALPHAVANTAGE_KEY"]

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


def sentimentTranslate(sentimentstr: str) -> SentimentCategory:
    if sentimentstr == "Bearish":
        return SentimentCategory.VERY_NEGATIVE
    elif sentimentstr == "Somewhat-Bearish":
        return SentimentCategory.NEGATIVE
    elif sentimentstr == "Bullish":
        return SentimentCategory.VERY_POSITIVE
    elif sentimentstr == "Somewhat-Bullish":
        return SentimentCategory.POSITIVE
    else:
        raise ValueError("Unknown sentiment category: " + sentimentstr)


def ticker2YfinanceFormat(tickerstr: str) -> str:
    if "CRYPTO:" in tickerstr or "FOREX:" in tickerstr:
        _, tickerstr = tickerstr.split(":")
        tickerstr += "-USD"
    return tickerstr


def getSentimenAndNews():
    # first start with general news
    url = (
        BASEURL
        + "?function=NEWS_SENTIMENT&limit=1000&apikey="
        + environ["ALPHAVANTAGE_KEY"]
    )

    response = requests.request("GET", url)
    response.raise_for_status()
    response = response.json()
    # sentiment_score_definition':'x <= -0.35: Bearish; -0.35 < x <= -0.15: Somewhat-Bearish; -0.15 < x < 0.15: Neutral; 0.15 <= x < 0.35: Somewhat_Bullish; x >= 0.35: Bullish'
    # 'relevance_score_definition': '0 < x <= 1, with a higher score indicating higher relevance.'
    for article in response["feed"]:
        # first check if exists already
        dbart = (
            db.query(AlphaSentimentArticle)
            .filter(AlphaSentimentArticle.title == article["title"])
            .first()
        )
        if dbart:
            continue

        dbarticle = AlphaSentimentArticle(
            timestamp=datetime.strptime(article["time_published"], "%Y%m%dT%H%M%S"),
            author=article["authors"][0] if len(article["authors"]) > 0 else None,
            title=article["title"],
            summary=article["summary"],
            category=article["category_within_source"]
            if article["category_within_source"] != "n/a"
            else None,
            source=article["source"],
        )
        db.add(dbarticle)
        db.commit()
        db.refresh(dbarticle)

        for ticker in article["ticker_sentiment"]:
            if ticker["ticker_sentiment_label"] != "Neutral":
                # kick out every neutral sentiment - why save?
                db.add(
                    AlphaSentiment(
                        ticker=ticker2YfinanceFormat(ticker["ticker"]),
                        timestamp=dbarticle.timestamp,
                        article_id=dbarticle.id,
                        article_relevance_score=round(
                            float(ticker["relevance_score"]), 2
                        ),
                        article_sentiment_score=round(
                            float(ticker["ticker_sentiment_score"]), 2
                        ),
                        article_sentiment_category=sentimentTranslate(
                            ticker["ticker_sentiment_label"]
                        ),
                    )
                )
        db.commit()


getSentimenAndNews()
# getGainersLosers()
