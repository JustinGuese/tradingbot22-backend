from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from bots import getBot
from db import Trade, get_db
from logger import logger
from pricing import getCurrentPrice

router = APIRouter()

COMMISSION = 0.0015


@router.post("/buy/{bot_name}/{ticker}/{amount}")
def buy(
    bot_name: str,
    ticker: str,
    amount: float,
    amountInUSD: bool = True,
    db: Session = Depends(get_db),
) -> dict:
    bot = getBot(bot_name, db)
    portfolio = bot.portfolio
    cash = portfolio.get("USD", 0)
    crntPrice = getCurrentPrice(ticker)
    if amount < 0:
        logger.warning("negative amount passed to buy by bot " + bot_name)
        raise HTTPException(status_code=400, detail="shorting not yet implemented")
    if not amountInUSD:
        amount *= crntPrice

    cost = amount * (1 + COMMISSION)
    howMany = amount / crntPrice
    if cash < cost:
        logger.warning(
            f"bot {bot_name} tried to buy {amount} {ticker} but only had {cash} USD"
        )
        raise HTTPException(
            status_code=400,
            detail="not enough cash to buy " + str(amount) + " " + ticker,
        )
    if ticker in portfolio:
        portfolio[ticker] += howMany
    else:
        portfolio[ticker] = howMany
    portfolio["USD"] -= cost
    bot.portfolio = portfolio
    db.commit()

    trade = Trade(
        bot=bot_name,
        ticker=ticker,
        quantity=amount,
        price=crntPrice,
        buy=True,
    )
    db.add(trade)
    db.commit()
    logger.info(f"bot {bot_name} bought {howMany} {ticker} for {cost} USD")
    return portfolio


@router.post("/sell/{bot_name}/{ticker}/{amount}")
def sell(
    bot_name: str,
    ticker: str,
    amount: float,
    amountInUSD: bool = True,
    db: Session = Depends(get_db),
) -> dict:
    bot = getBot(bot_name, db)
    portfolio = bot.portfolio
    crntPrice = getCurrentPrice(ticker)
    if amount < 0:
        logger.warning("negative amount passed to sell by bot " + bot_name)
        raise HTTPException(
            status_code=400, detail="amount for sell must always be positive"
        )
    if not amountInUSD:
        amount *= crntPrice

    if ticker not in portfolio:
        logger.warning(
            f"bot {bot_name} tried to sell {amount} {ticker} but did not have any"
        )
        raise HTTPException(
            status_code=400,
            detail="not enough " + ticker + " to sell " + str(amount),
        )

    howMany = amount / crntPrice
    if portfolio[ticker] < howMany:
        logger.warning(
            f"bot {bot_name} tried to sell {howMany} {ticker} but only had {portfolio[ticker]}"
        )
        raise HTTPException(
            status_code=400,
            detail="not enough " + ticker + " to sell " + str(amount),
        )

    cost = amount * (1 - COMMISSION)
    portfolio[ticker] -= howMany
    portfolio["USD"] += cost
    bot.portfolio = portfolio
    db.commit()

    trade = Trade(
        bot=bot_name,
        ticker=ticker,
        quantity=amount,
        price=crntPrice,
        buy=False,
    )
    db.add(trade)
    db.commit()
    logger.info(f"bot {bot_name} sold {howMany} {ticker} for {cost} USD")
    return portfolio
