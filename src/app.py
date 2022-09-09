from fastapi import (Depends, FastAPI, HTTPException, Query, Request, Response,
                     status)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import APIKeyCookie, OAuth2AuthorizationCodeBearer
from tqdm import tqdm
from sqlalchemy.orm import Session
import warnings


from ta import add_all_ta_features
from ta.utils import dropna

import pandas as pd

import yfinance as yf

from db import get_db, StockData, Bot, Trade, TechnicalAnalysis, \
        BotPD, StockDataPD, TradePD, TechnicalAnalysisPD, NewBotPD

app = FastAPI()

# CWEG.L = Amundi Index Solutions - Amundi MSCI World Energy UCITS ETF-C USD (CWEG.L)
# IWDA.AS = iShares Core MSCI World UCITS ETF USD (Acc)
# EEM = iShares MSCI Emerging Markets ETF (EEM)
ALLOWED_STOCKS = [
    "AAPL", "MSFT", "GOOG", "TSLA",  # stocks
    "CWEG.L", "IWDA.AS", "EEM", # etfs
    "BTC-USD", "ETH-USD", "AVAX-USD" # crypto
]
# interactive brokers 0.05% of Trade Value
COMMISSION = 0.0005

async def __update(db: Session):
    print("updating data now")
    for ticker in tqdm(ALLOWED_STOCKS):
        # first check if it's already in database
        if db.query(StockData).filter(StockData.ticker == ticker).first() is None:
            lookback = "5y"
        else:
            lookback = "201d"
        # if not, add complete history
        df = yf.download(ticker, interval = "1d", period=lookback, progress=False)
        # stockdataobjects = []
        if len(df) == 0:
            raise ValueError("No data for ticker " + ticker)
        for i in range(len(df)):
            if df.iloc[i].Volume > 0: # it is 0 if the day is not yet complete
                stockobj = StockData(
                        timestamp = pd.to_datetime(df.index[i]),
                        ticker = ticker,
                        open = float(df.iloc[i].Open),
                        high = float(df.iloc[i].High),
                        low = float(df.iloc[i].Low),
                        close = float(df.iloc[i].Close),
                        volume = int(df.iloc[i].Volume),
                        adj_close = float(df.iloc[i]["Adj Close"])
                        )
                try:
                    db.merge(stockobj)
                    db.commit()
                except Exception as e:
                    print("Stockdata SQL insert error with: " + ticker)
                    print(e)
        # next add technical indicators
        df = dropna(df)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df = add_all_ta_features(
                df, open="Open", high="High", low="Low", close="Close", volume="Volume", fillna=True)
        df["SMA_3"] = df["Close"].rolling(window=3).mean()
        df["SMA_10"] = df["Close"].rolling(window=10).mean()
        df["SMA_50"] = df["Close"].rolling(window=50).mean()
        df["SMA_200"] = df["Close"].rolling(window=200).mean()

        # fill zero values with the previous value
        # df format: earlier -> later, therefore we need to bfill to avoid taking future information
        df = df.replace(0, method="bfill")

        # drop standard shiet
        df = df.drop(columns=["Open", "High", "Low", "Close", "Volume", "Adj Close"])
        # then do the same
        for i in range(len(df)):
            rowdict = df.iloc[i].to_dict()
            rowdict["timestamp"] = pd.to_datetime(df.index[i])
            rowdict["ticker"] = ticker
            ta_obj = TechnicalAnalysis(**rowdict)
            try:
                db.merge(ta_obj)
                db.commit()
            except Exception as e:
                print("TA SQL insert error with: " + ticker)
                print(e)

@app.get("/update")
async def update(db: Session = Depends(get_db)):
    await __update(db)

## account functions
@app.put("/bot/", tags = ["account"])
async def create_bot(bot: NewBotPD, request: Request, db: Session = Depends(get_db)):
    # check if bot already exists
    if db.query(Bot).filter(Bot.name == bot.name).first() is not None:
        raise HTTPException(status_code=400, detail="Bot already exists")
    botobj = Bot(**bot.dict())
    db.add(botobj)
    db.commit()

@app.get("/bot/", response_model=list[BotPD], tags = ["account"])
async def get_bots(request: Request, db: Session = Depends(get_db)):
    bots = db.query(Bot).all()
    return bots

# get specific bot
@app.get("/bot/{botname}", response_model=BotPD, tags = ["account"])
async def get_bot(botname: int, request: Request, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.name == botname).first()
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot

# delete bot
@app.delete("/bot/{botname}", tags = ["account"])
async def delete_bot(botname: str, request: Request, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.name == botname).first()
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    db.delete(bot)
    db.commit()
# end account functions

## trade functions
@app.put("/buy/", tags = ["trades"])
async def buy_stock(botname: str, ticker: str, request: Request, db: Session = Depends(get_db), amount: float = -1):
    bot = db.query(Bot).filter(Bot.name == botname).first()
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    if ticker not in ALLOWED_STOCKS:
        raise HTTPException(status_code=400, detail="Ticker not allowed")
    # get current price
    currentPrice = yf.download(ticker, interval = "1d", period="1d", progress=False)["Close"].iloc[-1]
    # check if bot has enough money
    if bot.portfolio["USD"] < amount * currentPrice:
        raise HTTPException(status_code=400, detail="Not enough money")
    # add trade on bot
    # if amount == -1 then buy all we can
    if amount == -1:
        amount = bot.portfolio["USD"] / currentPrice * (1 - COMMISSION)
    if ticker in bot.portfolio:
        bot.portfolio[ticker] += amount
    else:
        bot.portfolio[ticker] = amount
    bot.portfolio["USD"] -= amount * currentPrice * (1 + COMMISSION)
    db.commit()
    # then create trade object
    trade = Trade(
            bot = botname,
            ticker = ticker,
            buy = True,
            price = currentPrice,
            quantity = amount)
    db.add(trade)
    db.commit()
    return bot.portfolio

@app.put("/sell/", tags = ["trades"])
async def sell_stock(botname: str, ticker: str, request: Request, db: Session = Depends(get_db), amount: float = -1):
    bot = db.query(Bot).filter(Bot.name == botname).first()
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    if ticker not in ALLOWED_STOCKS:
        raise HTTPException(status_code=400, detail="Ticker not allowed")
    # get current price
    currentPrice = yf.download(ticker, interval = "1d", period="1d", progress=False)["Close"].iloc[-1]
    # check if bot has enough stock
    if ticker not in bot.portfolio:
        raise HTTPException(status_code=404, detail="you do not own that stock to sell")
    if amount == -1:
        amount = bot.portfolio[ticker]
    if bot.portfolio[ticker] < amount:
        raise HTTPException(status_code=400, detail="Not enough stock. you wanted: %.2f, you have: %.2f" % (amount, bot.portfolio[ticker]))

    # add trade on bot
    bot.portfolio[ticker] -= amount
    bot.portfolio["USD"] += amount * currentPrice * (1 - COMMISSION)
    db.commit()

    # then create trade object
    trade = Trade(
            bot = botname,
            ticker = ticker,
            buy = False,
            price = currentPrice,
            quantity = amount)
    db.add(trade)
    db.commit()
    return bot.portfolio