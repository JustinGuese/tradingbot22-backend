from datetime import datetime

import yfinance as yf
from sqlalchemy.orm import Session

from db import Recommendation


def getRecommendations(ticker: str, db: Session):
    yfObj = yf.Ticker(ticker)
    recomm = yfObj.recommendations
    if recomm is not None:
        if len(recomm) > 0:
            for index, row in recomm.iterrows():
                # check if we already have this recommendation
                date = index
                # check if ticker, date, company already exist
                result = db.query(Recommendation).filter(Recommendation.ticker == ticker, Recommendation.timestamp == date, Recommendation.company == row['Firm']).first()
                # if result is None: #  why the fuck doesnt this work
                try:
                    fuckpython = type(result.timestamp) is not datetime
                except AttributeError:
                    fuckpython = True
                if fuckpython:
                    recObj = Recommendation(
                            timestamp = date,
                            ticker = ticker,
                            company = row["Firm"], 
                            rating = row["To Grade"],
                            rating_before = row["From Grade"],
                            action = row["Action"],
                    )
                    try:
                        db.merge(recObj)
                        db.commit()
                    except:
                        # why the fuck does sql alchemy not detect this fuck
                        pass
        else:
            print("No recommendations found for %s" % ticker)
    else:
        print("No recommendations found for %s" % ticker)