from typing import Dict

import numpy as np
import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from bots import getBot
from db import EarningDates, Trade, get_db
from logger import logger
from pricing import getCurrentPrice

router = APIRouter()


def __updateEarningDates(ticker: str, db: Session) -> float:
    earnDf = yf.Ticker(ticker).earnings_dates
    if earnDf is not None:
        for index, row in earnDf.iterrows():
            if all(row.isna()):
                continue
            edobj = EarningDates(
                ticker=ticker,
                timestamp=index,
                estimate=row["EPS Estimate"],
                reported=row["Reported EPS"],
                surprise_pct=row["Surprise(%)"],
            )
            db.merge(edobj)
        db.commit()
    else:
        logger.warning("could not get earning dates for " + ticker)


@router.get("/earningdates/{ticker}")
def getEarningDates(ticker: str, db: Session = Depends(get_db)):
    __updateEarningDates(ticker, db)
    ed = db.query(EarningDates).filter(EarningDates.ticker == ticker).all()
    ed = [jsonable_encoder(e) for e in ed]
    for e in ed:
        for k, v in e.items():
            if isinstance(v, float) and np.isnan(v):
                e[k] = None
    return ed
