import yfinance as yf
from sqlalchemy.orm import Session

from db import Recommendation


def getRecommendations(ticker: str, db: Session):
    yfObj = yf.Ticker(ticker)
    recomm = yfObj.recommendations
    if len(recomm) > 0:
        for index, row in recomm.iterrows():
            # check if we already have this recommendation
            date = index
            if db.query(Recommendation).filter(Recommendation.ticker == ticker).filter(Recommendation.timestamp == date).filter(Recommendation.company == row["Firm"]).first() is None:
                recObj = Recommendation(
                        timestamp = date,
                        ticker = ticker,
                        company = row["Firm"], #  what the fuck pandas?!
                        rating = row["To Grade"],
                        rating_before = row["From Grade"],
                        action = row["Action"],
                )
                db.add(recObj)
        db.commit()
    else:
        print("No recommendations found for %s" % ticker)