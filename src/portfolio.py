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


@router.get("/worth/{bot_name}")
def getPortfolioWorth(bot_name: str, db: Session = Depends(get_db)) -> float:
    bot = db.query(Bot).filter(Bot.name == bot_name).first()
    if not bot:
        raise HTTPException(status_code=404, detail="bot not found")
    portfolio = bot.portfolio

    total = 0
    for ticker, amount in portfolio.items():
        if ticker == "USD":
            total += amount
        else:
            # TODO: add shorting support -> negative amount
            total += abs(amount) * getCurrentPrice(ticker)
    bot.portfolio_worth = total
    db.commit()
    return total
