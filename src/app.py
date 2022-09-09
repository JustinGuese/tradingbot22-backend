from fastapi import (Depends, FastAPI, HTTPException, Query, Request, Response,
                     status)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import APIKeyCookie, OAuth2AuthorizationCodeBearer
from tqdm import tqdm
from sqlalchemy.orm import Session

import pandas as pd

import yfinance as yf

from db import get_db, StockData, Bot, Trade, \
        BotPD, StockDataPD, TradePD

app = FastAPI()

# CWEG.L = Amundi Index Solutions - Amundi MSCI World Energy UCITS ETF-C USD (CWEG.L)
# IWDA.AS = iShares Core MSCI World UCITS ETF USD (Acc)
# EEM = iShares MSCI Emerging Markets ETF (EEM)
ALLOWED_STOCKS = [
    "AAPL", "MSFT", "GOOG", "TSLA",  # stocks
    "CWEG.L", "IWDA.AS", "EEM", # etfs
    "BTC-USD", "ETH-USD", "AVAX-USD" # crypto
]

async def __update(db: Session):
    print("updating data now")
    for ticker in tqdm(ALLOWED_STOCKS):
        # first check if it's already in database
        if db.query(StockData).filter(StockData.ticker == ticker).first() is None:
            lookback = "5y"
        else:
            lookback = "2d"
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
                    print("SQL insert error with: " + ticker)
                    print(e)
        

@app.get("/update")
async def update(db: Session = Depends(get_db)):
    await __update(db)