from datetime import datetime, timedelta
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


@router.get("/allBotsByWorth/")
def getPortfolioSortedByBots(
    withPortfolio: bool = False, db: Session = Depends(get_db)
):
    bots = db.query(PortfolioWorths).all()
    latestUpdate = (
        db.query(PortfolioWorths.timestamp)
        .order_by(PortfolioWorths.timestamp.desc())
        .first()
    )
    rettich = []
    for bot in bots:
        daysActive = (datetime.utcnow() - bot.created_at).days
        ret = bot.portfolio_worth - bot.start_money
        if daysActive > 0:
            ret /= daysActive
            ret *= 365
        else:
            ret = 0
        if withPortfolio:
            rettich.append(
                (bot.name, bot.portfolio_worth, round(ret, 2), bot.portfolio)
            )
        else:
            rettich.append((bot.name, bot.portfolio_worth, round(ret, 2)))

    rettich = sorted(rettich, key=lambda x: x[1], reverse=True)
    return {
        "latestUpdate": latestUpdate,
        "isRecent": latestUpdate > datetime.utcnow() - timedelta(days=1),
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
