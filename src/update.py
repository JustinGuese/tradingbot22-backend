from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from bots import getBot
from db import Bot, get_db
from logger import logger
from portfolio import getPortfolioWorth
from pricing import getCurrentPrice
from ratings import __updateEarningDates

router = APIRouter()


@router.get("/portfolioworths")
def updatePortfolioWorths(db: Session = Depends(get_db)):
    bots = db.query(Bot).all()
    for bot in bots:
        # getPortfolioWorth automatically commits update to db
        _ = getPortfolioWorth(bot.name, db)
    return {"message": "success"}


@router.get("/earningdates")
def updateEarningDates(db: Session = Depends(get_db)):
    botportfolios = db.query(Bot.portfolio).all()
    # all stocks means all keys
    allStocks = [list(portfolio[0].keys()) for portfolio in botportfolios]
    # flatten list
    allStocks = [item for sublist in allStocks for item in sublist]
    for stock in allStocks:
        if stock == "USD":
            continue
        # getPortfolioWorth automatically commits update to db
        __updateEarningDates(stock, db)
    return {"message": "success"}
