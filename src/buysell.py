import json
from datetime import datetime
from os import environ

import yfinance as yf
from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session

from allowed_stocks import ALLOWED_STOCKS
# from alpy import AlpacaInterface
from db import Bot, Trade
from elastic import logToElastic
from notification import sendToSlack
from pricing_functions import COMMISSION, __getCurrentPrice

# alpacaInterface = AlpacaInterface()

async def __buy_stock(botname: str, ticker: str, 
        db: Session, amount: float = -1,
        amountInUSD: bool = False, short: bool = False):
    if ticker == "USD":
        raise HTTPException(status_code=400, detail="USD is not a stock")
    bot = db.query(Bot).filter(Bot.name == botname).first()
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    # if ticker not in ALLOWED_STOCKS:
    #     raise HTTPException(status_code=400, detail="Ticker not allowed")
    # get current price
    currentPrice = await __getCurrentPrice(ticker)
    # check if bot has enough money
    if amountInUSD:
        amount = amount / currentPrice * (1 - COMMISSION)
    if bot.portfolio["USD"] < amount * currentPrice:
        raise HTTPException(status_code=400, detail="Not enough money")
    # add trade on bot
    # if amount == -1 then buy all we can
    if amount == -1:
        amount = bot.portfolio["USD"] / currentPrice * (1 - COMMISSION)
    if amount < 0:
        raise HTTPException(status_code=400, detail="Amount cant be negative")
    if short:
        amount = -amount
        
    if ticker in bot.portfolio:
        if bot.portfolio[ticker] > 0 and short:
            # uhoh!
            raise HTTPException(status_code=400, detail="Already long on this stock. cant open short. sell first")
        elif bot.portfolio[ticker] < 0 and not short:
            # uhoh!
            raise HTTPException(status_code=400, detail="Already short on this stock. cant open long. sell first")
        bot.portfolio[ticker] += amount
    else:
        bot.portfolio[ticker] = amount
        
    # abs to support shorts and long
    bot.portfolio["USD"] -= abs(amount) * currentPrice * (1 + COMMISSION)
    db.commit()
    # then create trade object
    trade = Trade(
            bot = botname,
            ticker = ticker,
            buy = True,
            short = short,
            price = currentPrice,
            quantity = amount,
            live = bot.live
            )
    db.add(trade)
    db.commit()
    # and finally log 2 elastic, silently fails if not reachable
    logToElastic("tradingbot22_trades", {
            "botName" : bot.name, 
            "@timestamp" : datetime.utcnow(),
            "ticker": ticker,
            "buy": True,
            "short": short,
            "price": currentPrice,
            "quantity": amount
            })
    # if botname in ALERT_ON_BUY env var, send a slack message
    if bot.name in environ.get("ALERT_ON_BUY", "").split(","):
        sendToSlack(bot.name, f"buy {round(amount * currentPrice,2)}$ or {round(amount,2)} of {ticker}", "info")
    return trade.id

async def __sell_stock(botname: str, ticker: str, 
        db: Session, amount: float = -1,
        amountInUSD: bool = False, short: bool = False):
    if ticker == "USD":
        raise HTTPException(status_code=400, detail="USD is not a stock")
    bot = db.query(Bot).filter(Bot.name == botname).first()
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    # if ticker not in ALLOWED_STOCKS:
    #     raise HTTPException(status_code=400, detail="Ticker not allowed")
    # get current price
    currentPrice = await __getCurrentPrice(ticker)
    # check if bot has enough stock
    if ticker not in bot.portfolio:
        raise HTTPException(status_code=404, detail="you do not own %s to sell. not in portfolio. portfolio is: " % ticker + str(bot.portfolio))
    if amount < 0 and amount != -1:
        raise HTTPException(status_code=400, detail="Amount cant be negative. is: " + str(amount))
    if amount == -1:
        amount = bot.portfolio[ticker]
    if bot.portfolio[ticker] == 0:
        raise HTTPException(status_code=400, detail="you do not own %s to sell. amount is 0. portfolio is %s" % (ticker, str(bot.portfolio))
    if amountInUSD:
        amount = amount / currentPrice * (1 - COMMISSION)
    if bot.portfolio[ticker] < 0 and not short:
        raise HTTPException(status_code=400, detail="This is a short. you need to enable short trading by passing short=True")
    if bot.portfolio[ticker] > 0 and short:
        raise HTTPException(status_code=400, detail="This is a long. you need to disable short trading by passing short=False")
    if (abs(bot.portfolio[ticker]) - abs(amount)) < 0:
        raise HTTPException(status_code=400, detail="Not enough stock. you wanted: %.2f, you have: %.2f" % (amount, bot.portfolio[ticker]))

    # add trade on bot
    if bot.portfolio[ticker] > 0:
        # long, is no short
        bot.portfolio[ticker] -= amount
        bot.portfolio["USD"] += amount * currentPrice * (1 - COMMISSION)
    elif bot.portfolio[ticker] < 0 and short:
        # short
        # we need to load the price from the db to calculate the profit
        theBuyTrade = db.query(Trade).filter(Trade.bot == botname).filter(Trade.ticker == ticker).filter(Trade.buy == True).filter(Trade.short == True).order_by(Trade.id.desc()).first()
        diff = theBuyTrade.price - currentPrice
        bot.portfolio["USD"] += (theBuyTrade.price + diff) * abs(amount) * (1 - COMMISSION)
        bot.portfolio[ticker] += abs(amount)
    else:
        raise ValueError("this really shouldnt happen... logic for short that is not implemted")
    
    db.commit()

    # then create trade object
    trade = Trade(
            bot = botname,
            ticker = ticker,
            buy = False,
            short = short,
            price = currentPrice,
            quantity = amount,
            live = bot.live
            )
    db.add(trade)
    db.commit()
    # and finally log 2 elastic, silently fails if not reachable
    logToElastic("tradingbot22_trades", {
            "botName" : bot.name, 
            "@timestamp" : datetime.utcnow(),
            "ticker": ticker,
            "buy": False,
            "short": short,
            "price": currentPrice,
            "quantity": amount
            })
    # if botname in ALERT_ON_BUY env var, send a slack message
    if bot.name in environ.get("ALERT_ON_BUY", "").split(","):
        sendToSlack(bot.name, f"sell {round(amount * currentPrice,2)}$ or {round(amount,2)} of {ticker}", "info")
    return trade.id

