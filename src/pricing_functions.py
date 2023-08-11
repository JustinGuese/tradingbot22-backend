from datetime import datetime, timedelta

import yfinance as yf

# interactive brokers 0.05% of Trade Value
COMMISSION = 0.0005

BUFFER = dict()

async def __getYFPrice(ticker: str) -> float:
    df = yf.download(ticker, interval = "1d", period="1d", progress=False)
    if len(df) == 0:
        df = yf.download(ticker, interval = "1d", period="5d", progress=False)
    if len(df) == 0:
        df = yf.download(ticker, interval = "1d", period="1mo", progress=False)
    assert len(df) > 0, "df is empty"
    return float(df["Close"].iloc[-1])


async def __getCurrentPrice(ticker: str) -> float:
    global BUFFER
    try:
        if not ticker in BUFFER or BUFFER.get(ticker, {}).get("updated", datetime(1970,1,1)) < datetime.utcnow() - timedelta(minutes=2):
            BUFFER[ticker] = { "price" : await __getYFPrice(ticker), "updated" : datetime.utcnow() }
        return BUFFER[ticker]["price"]
    except Exception as e:
        print("problem to get current price of: " + ticker)
        # TODO: log somehow
        return None