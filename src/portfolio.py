from datetime import datetime, timedelta
from enum import Enum
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from bots import getBot
from db import Bot, PortfolioWorths, get_db
from logger import logger
from pricing import getCurrentPrice

router = APIRouter()


@router.get("/{bot_name}", response_model=Dict[str, float])
def getPortfolio(bot_name: str, db: Session = Depends(get_db)):
    return getBot(bot_name, db).portfolio


class SortOptions(str, Enum):
    worth = "worth"
    returnPerYear = "returnPerYear"


@router.get("/allBotsByWorth/")
def getPortfolioSortedByBots(
    withPortfolio: bool = False,
    sortby: SortOptions = SortOptions.returnPerYear,
    db: Session = Depends(get_db),
):
    bots = db.query(Bot).all()
    # latestUpdate = (
    #     db.query(PortfolioWorths.timestamp)
    #     .order_by(PortfolioWorths.timestamp.desc())
    #     .first()
    # )
    rettich = []
    for bot in bots:
        daysActive = (datetime.utcnow() - bot.created_at).days
        ret = bot.portfolio_worth - bot.start_money
        if daysActive > 0:
            ret /= daysActive
            ret *= 365
        else:
            ret = 0
        # calculate pct per year
        pctPerYear = ret / bot.start_money * 100
        rettich.append(
            (
                bot.name,
                bot.portfolio_worth,
                round(ret, 2),
                daysActive,
                int(pctPerYear),
                None if not withPortfolio else bot.portfolio,
            )
        )
    # sort by
    if sortby == SortOptions.worth:
        sortby = 1
    elif sortby == SortOptions.returnPerYear:
        sortby = 2
    else:
        raise ValueError("sortby must be one of: ", str(SortOptions))

    rettich = sorted(rettich, key=lambda x: x[sortby], reverse=True)
    # make more readable
    rettich = [
        {
            "botname": name,
            "worthUSD": worth,
            "returnPerYearUSD": ret,
            "daysActive": daysActive,
            "pctPerYear": pctPerYear,
            "portfolio": portfolio,
        }
        for name, worth, ret, daysActive, pctPerYear, portfolio in rettich
    ]
    return {
        # "latestUpdate": latestUpdate, # cursed
        "bots": rettich,
    }


@router.get("/worth/{bot_name}")
def getPortfolioWorth(bot_name: str, db: Session = Depends(get_db)) -> float:
    bot = db.query(Bot).filter(Bot.name == bot_name).first()
    if not bot:
        raise HTTPException(status_code=404, detail="bot not found")
    portfolio = bot.portfolio

    total = 0
    cleanedPortfolio = {}
    for ticker, amount in portfolio.items():
        if ticker == "USD":
            total += amount
        else:
            try:
                # TODO: add shorting support -> negative amount
                total += abs(amount) * getCurrentPrice(ticker)
            except Exception as e:
                logger.error(e)
                # but continue
        if amount != 0:
            cleanedPortfolio[ticker] = amount
    total = round(total, 2)
    bot.portfolio = cleanedPortfolio
    bot.portfolio_worth = total
    db.commit()
    return total
