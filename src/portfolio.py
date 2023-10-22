from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from bots import getBot
from db import Bot, get_db
from logger import logger
from pricing import getCurrentPrice

router = APIRouter()


@router.get("/{bot_name}", response_model=Dict[str, float])
def getPortfolio(bot_name: str, db: Session = Depends(get_db)):
    return getBot(bot_name, db).portfolio


@router.get("/allBotsByWorth/")
def getPortfolioSortedByBots(withPortfolio: bool = True, db: Session = Depends(get_db)):
    bots = db.query(Bot.name, Bot.portfolio_worth, Bot.portfolio).all()
    if not withPortfolio:
        bots = [(bot.name, bot.portfolio_worth) for bot in bots]
    else:
        bots = [(bot.name, bot.portfolio_worth, bot.portfolio) for bot in bots]
    bots = sorted(bots, key=lambda x: x[1], reverse=True)
    return bots


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
            # TODO: add shorting support -> negative amount
            total += abs(amount) * getCurrentPrice(ticker)
        if amount != 0:
            cleanedPortfolio[ticker] = amount
    total = round(total, 2)
    bot.portfolio = cleanedPortfolio
    bot.portfolio_worth = total
    db.commit()
    return total
