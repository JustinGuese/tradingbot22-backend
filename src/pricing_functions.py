import yfinance as yf

# interactive brokers 0.05% of Trade Value
COMMISSION = 0.0005

async def __getCurrentPrice(ticker: str) -> float:
    try:
        df = yf.download(ticker, interval = "1d", period="1d", progress=False)
        return df["Close"].iloc[-1]
    except Exception as e:
        print("problem with df: " + ticker)
        print(df)
        # TODO: log somehow
        return 0.