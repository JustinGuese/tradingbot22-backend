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
        BotPD, StockDataPD, TradePD, TechnicalAnalysisPD

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