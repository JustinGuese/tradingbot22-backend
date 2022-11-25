from datetime import datetime, timedelta

import yfinance as yf

# interactive brokers 0.05% of Trade Value
COMMISSION = 0.0005

BUFFER = dict()

async def __getCurrentPrice(ticker: str) -> float:
    global BUFFER
    try:
        if not ticker in BUFFER:
            df = yf.download(ticker, interval = "1d", period="1d", progress=False)
            BUFFER[ticker] = { "price" : float(df["Close"].iloc[-1]), "updated" : datetime.utcnow() }
        else:
            if BUFFER[ticker]["updated"] < datetime.utcnow() - timedelta(minutes=2):
                df = yf.download(ticker, interval = "1d", period="1d", progress=False)
                BUFFER[ticker] = { "price" : float(df["Close"].iloc[-1]), "updated" : datetime.utcnow() }
        return BUFFER[ticker]["price"]
    except Exception as e:
        print("problem with df: " + ticker)
        print(df)
        # TODO: log somehow
        return 0.