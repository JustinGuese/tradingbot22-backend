import warnings
from datetime import date, datetime, timedelta
from typing import List

import numpy as np
import pandas as pd
import uvicorn
import yfinance as yf
from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy import and_, extract, or_
from sqlalchemy.orm import Session
from ta import add_all_ta_features
from ta.utils import dropna
from tqdm import tqdm

from allowed_stocks import ALLOWED_STOCKS
from buysell import __buy_stock, __sell_stock
from check_open_stoploss import checkOpenStoplosses
from db import (TA_COLUMNS, Bot, BotPD, EarningDates, EarningDatesPD,
                EarningRatings, EarningRatingsPD, GetTradeDataPD, NewBotPD,
                PortfolioWorths, QuarterlyFinancials,
                QuarterlyFinancialsEffect, QuarterlyFinancialsEffectPD,
                QuarterlyFinancialsPD, StockData, TAType, TechnicalAnalysis,
                Trade, get_db)
from earnings import updateEarningEffect, updateEarnings
from elastic import logError, logToElastic
from graphs import getCurrentPortfolioGraph
from language import updateNews
from pricing_functions import __getCurrentPrice
from stoploss_takeprofit import __buy_stock_stoploss, __sell_stock_stoploss
from yahoo_extras import updateYahooEarningsRatingsData
from yfrecommendations import getRecommendations

app = FastAPI(title="Tradingbot22 API", description="API for the tradingbot22 project", version="0.1")

# CWEG.L = Amundi Index Solutions - Amundi MSCI World Energy UCITS ETF-C USD (CWEG.L)
# IWDA.AS = iShares Core MSCI World UCITS ETF USD (Acc)
# EEM = iShares MSCI Emerging Markets ETF (EEM)


async def __update(db: Session):
    print("updating data now")
    for ticker in tqdm(ALLOWED_STOCKS):
        try:
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
                        logError("stockdata_update_sql_insert", ticker, str(repr(e)))
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
                    logError("ta_update_sql_insert", ticker, str(repr(e)))
                    print(e)
            # grab earnings updates
            try:
                updateEarnings(ticker, db)
            except Exception as e:
                print("problem in earnings update: " + ticker)
                logError("earnings_update", ticker, str(repr(e)))
                print(e)
                    
            # next news sentiment update
            try:
                updateNews(ticker, db)
            except Exception as e:
                print("problem in news update: " + ticker)
                logError("news_update", ticker, str(repr(e)))
                print(e)
            # next get recommendation update
            try:
                getRecommendations(ticker, db)
            except Exception as e:
                print("problem in recommendation update: " + ticker)
                logError("analyst_update", ticker, str(repr(e)))
                print(e)
        except Exception as e:
            logError("update_function", ticker, str(repr(e)))
            print("problem in general update: " + ticker)
    # trigger the last update of earning ratings by analyst (custom yahoo data)
    await updateYahooEarningsRatingsData(ALLOWED_STOCKS, db)

@app.get("/update")
async def update(db: Session = Depends(get_db)):
    await __update(db)
    
@app.get("/update/earnings/")
async def updateEarningsRoot(ticker: str, db: Session = Depends(get_db)):
    updateEarnings(ticker, db)
    
@app.get("/update/earnings/ratings/")
async def updateEarningsRatings(db: Session = Depends(get_db)):
    await updateYahooEarningsRatingsData(ALLOWED_STOCKS, db)

    
@app.get("/update/portfolioworth")
async def update_portfolioworth(db: Session = Depends(get_db)):
    # first get all bots
    bots = db.query(Bot).all()
    for bot in bots:
        worth = await __portfolioWorth(bot.name, db)
        bot.portfolioWorth = worth
        db.commit()
        # and try to log 2 elastic if it's up (otherwise it will just skip)
        logToElastic("tradingbot22_portfolio_worth-" + datetime.now().strftime("%Y-%m"), {
            "botName" : bot.name, "portfolioWorth" : worth, 
            "@timestamp" : datetime.utcnow(),
            "pctPerYear" : round(calculatePctPerYear(worth, bot.created_at),2),
            "portfolio" : { k: round(v,2) for k,v in dict(bot.portfolio).items() }
            })
        pws = PortfolioWorths(
            bot = bot.name,
            timestamp = datetime.utcnow(),
            pctPerYear = calculatePctPerYear(worth, bot.created_at),
            worth = worth,
            portfolio = bot.portfolio,
        )
        db.add(pws)
    db.commit()
        
@app.get("/update/earningeffects")
async def update_earningeffects(db: Session = Depends(get_db)):
    print("starting earning effect update. can take some time...")
    updateEarningEffect(ALLOWED_STOCKS, db)

## account functions
@app.put("/bot/", tags = ["account"])
async def create_bot(bot: NewBotPD, request: Request, db: Session = Depends(get_db)):
    # check if bot already exists
    if db.query(Bot).filter(Bot.name == bot.name).first() is not None:
        raise HTTPException(status_code=400, detail="Bot already exists")
    botobj = Bot(**bot.dict())
    db.add(botobj)
    db.commit()

@app.get("/bot/", response_model=List[BotPD], tags = ["account"])
async def get_bots(request: Request, db: Session = Depends(get_db)):
    bots = db.query(Bot).all()
    bots = [BotPD.from_orm(bot) for bot in bots]
    bots = sorted(bots, key=lambda bot: bot.portfolioWorth, reverse=True)
    return bots

def calculatePctPerYear(portfolioWorth: float, start: datetime):
    end = datetime.now()
    months = (end.year - start.year) * 12 + (end.month - start.month)
    totalPct = (portfolioWorth - 10000) / 10000 # 10000 is the starting amount
    pctPerMonth = totalPct / months if months != 0 else 0
    pctPerYear = pctPerMonth * 12 * 100
    return round(pctPerYear)

@app.get("/bot/byWorth", tags = ["account"])
async def get_bots_byWorth(request: Request, db: Session = Depends(get_db)):
    bots = db.query(Bot).all()
    # TODO: sort by portfolio worth
    bots = [BotPD.from_orm(bot) for bot in bots]
    bots = sorted(bots, key=lambda bot: bot.portfolioWorth, reverse=True)
    # only keep name and worth
    bots = [{"name" : bot.name, "worth" : bot.portfolioWorth, 'pctPerYear': calculatePctPerYear(bot.portfolioWorth, bot.created_at)} for bot in bots]
    return bots

# get specific bot
@app.get("/bot/{botname}", response_model=BotPD, tags = ["account"])
async def get_bot(botname: str, request: Request, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.name == botname).first()
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot

async def __portfolioWorth(botname: str, db: Session):
    bot = db.query(Bot).filter(Bot.name == botname).first()
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    portfolio = bot.portfolio
    cleanedPortfolio = dict()
    worth = 0
    for ticker,amount in portfolio.items():
        if ticker == "USD":
            worth += amount
        else:
            # cleaned Portfolio
            if amount != 0:
                cleanedPortfolio[ticker] = amount
            # need to calculate short worth
            if amount == 0:
                continue
            elif amount > 0:
                # long
                worth += await __getCurrentPrice(ticker) * amount
            else:
                # short
                try:
                    crntPrice = await __getCurrentPrice(ticker)
                    theBuyTrade = db.query(Trade).filter(Trade.bot == botname).filter(Trade.ticker == ticker).filter(Trade.buy == True).filter(Trade.short == True).order_by(Trade.id.desc()).first()
                    if theBuyTrade is None:
                        # no buy trade found, so we can't calculate the worth
                        logError("portfolioworth", ticker, "No buy trade found for short position ", botname, " ", ticker)
                        raise ValueError("No buy trade found for short position ", botname, " ", ticker)
                    winSoFar = theBuyTrade.price - crntPrice
                    worth += (theBuyTrade.price + winSoFar) * abs(amount)
                except Exception as e:
                    # TODO: log
                    logError("portfolioworth", ticker,str(repr(e)))
                    print(e)
                    # at least assume it is a long
                    worth += await __getCurrentPrice(ticker) * abs(amount)
    bot.portfolio = cleanedPortfolio
    db.commit()
    return worth

# get portfolio worth
@app.get("/bot/{botname}/portfolioworth", tags = ["account"])
async def get_portfolio_worth(botname: str, request: Request, db: Session = Depends(get_db)):
    return await __portfolioWorth(botname, db)

# delete bot
@app.delete("/bot/{botname}", tags = ["account"])
async def delete_bot(botname: str, request: Request, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.name == botname).first()
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    db.delete(bot) # doesnt work yet due to dependencies... reset instead
    # bot.portfolio = {"USD":10000}
    db.commit()
# end account functions



## trade functions
@app.put("/buy/", tags = ["trades"])
async def buy_stock(botname: str, ticker: str, 
        db: Session = Depends(get_db), amount: float = -1,
        amountInUSD: bool = False, short: bool = False):
    try:
        return await __buy_stock(botname, ticker, db, amount, amountInUSD, short)
    except Exception as e:
        logError("buy", ticker, str(repr(e)), severity = "critical")
        raise

@app.put("/sell/", tags = ["trades"])
async def sell_stock(botname: str, ticker: str, 
        db: Session = Depends(get_db), amount: float = -1,
        amountInUSD: bool = False, short: bool = False):
    try:
        return await __sell_stock(botname, ticker, db, amount, amountInUSD, short)
    except Exception as e:
        logError("sell", ticker, str(repr(e)), severity = "critical")
        raise

@app.put("/buy/stoploss", tags = ["trades"])
async def buy_stock_stoploss(botname: str, ticker: str, 
        close_if_below: float, close_if_above: float,
        close_if_below_hardlimit: float = None,
        maximum_date: datetime = None,
        db: Session = Depends(get_db), amount: float = -1,
        amountInUSD: bool = False, short: bool = False, ):
    return await __buy_stock_stoploss(botname, ticker, db, close_if_below, close_if_above, close_if_below_hardlimit, maximum_date, amount, amountInUSD, short)

# @app.put("/sell/stoploss", tags = ["trades"])
# async def sell_stock_stoploss(botname: str, ticker: str, 
#         close_if_below: float, close_if_above: float,
#         maximum_date: datetime = None,
#         db: Session = Depends(get_db), amount: float = -1,
#         amountInUSD: bool = False, short: bool = False, ):
#     return await __sell_stock_stoploss(botname, ticker, db, close_if_below, close_if_above, maximum_date, amount, amountInUSD, short)

# stoploss check
@app.get("/stoplosscheck", tags = ["trades"])
async def stoploss_check(db: Session = Depends(get_db)):
    await checkOpenStoplosses(db)

## helper functions

@app.get('/data/tradeable-tickers', tags = ["data"], response_model=List[str])
async def getTradeableTickers():
    return ALLOWED_STOCKS

# data requests
@app.post("/data/")
async def get_data(GetData: GetTradeDataPD, request: Request, db: Session = Depends(get_db)):
    if GetData.ticker not in ALLOWED_STOCKS:
        raise HTTPException(status_code=400, detail="Ticker not allowed")
    stockdata = db.query(StockData).filter(StockData.ticker == GetData.ticker,
        StockData.timestamp >= GetData.start_date,
        StockData.timestamp <= GetData.end_date).all()
    if len(GetData.technical_analysis_columns) > 0:
        if "all" in GetData.technical_analysis_columns:
            # then grab all technical analysis columns available and replace "all" with them
            ta_columns = TA_COLUMNS + ["SMA_3", "SMA_10", "SMA_50", "SMA_100", "SMA_200"]
        else:
            ta_columns = [x.value for x in GetData.technical_analysis_columns]
        # make this a join query in the future
        sql = """SELECT stock_data."timestamp", stock_data.ticker, stock_data."open", stock_data.high, stock_data.low, stock_data."close", stock_data.volume, stock_data.adj_close %s
            FROM stock_data
            inner join technical_analysis ta on stock_data.ticker = ta.ticker and stock_data."timestamp"  = ta."timestamp" 
            WHERE stock_data.ticker = '%s' AND stock_data."timestamp" >= '%s' AND stock_data."timestamp" <= '%s'
            """
        tadditions = ""
        for col in ta_columns:
            tadditions += ', ta."%s"' % col
        sql = sql % (tadditions, GetData.ticker, GetData.start_date, GetData.end_date)
        # error: out of range float values are not json compatible
        df = pd.read_sql_query(sql, db.bind)
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(method="bfill")
        # nan is not json compatible
        df = df.fillna(method="ffill")
        df = df.fillna(0)
        stockdata = df.to_dict(orient="records")
    return stockdata

@app.get("/data/ta_options")
async def get_ta_options(request: Request):
    return [x.value for x in TAType]

@app.get("/data/current_price/{ticker}")
async def get_current_price(ticker: str, request: Request):
    if ticker not in ALLOWED_STOCKS:
        raise HTTPException(status_code=400, detail="Ticker not allowed")
    price = await __getCurrentPrice(ticker)
    return float(price)

@app.get("/healthz")
async def healthcheck():
    return "yo whattup?"

## earning calendar routes
@app.get("/data/earnings/calendar", tags = ["data", "earnings"], response_model = List[EarningDatesPD])
async def getEarningsCalendar(now: bool = True, db: Session = Depends(get_db)):
    FROM = datetime.now() - timedelta(days=1)
    TO = datetime.now() + timedelta(days=1)
    if now:
        allEarnings = db.query(EarningDates).filter(FROM <= EarningDates.timestamp).filter(EarningDates.timestamp <= TO).all()
    else:
        allEarnings = db.query(EarningDates).order_by(EarningDates.timestamp).all()
    if len(allEarnings) == 0:
        return []
    else:
        return allEarnings
    
@app.get("/data/earnings/calendar-previous", tags = ["data", "earnings"])
async def getEarningsCalendarPrevious(custom_date: date = date.today(), db: Session = Depends(get_db)):
    # cool sqlalchemy usage btw with extract
    TODAY = custom_date
    previousEarnings = db.query(QuarterlyFinancials.ticker, QuarterlyFinancials.timestamp).filter(
        or_(
            QuarterlyFinancials.timestamp == TODAY,
            QuarterlyFinancials.timestamp == TODAY - timedelta(days=365),
            QuarterlyFinancials.timestamp == TODAY - timedelta(days=365*2),
        )
    ).order_by(QuarterlyFinancials.timestamp.desc()).all()
    return previousEarnings
    
@app.get("/data/earnings/financials", tags = ["data", "earnings"], response_model = List[QuarterlyFinancialsPD])
async def getEarningsFinancials(ticker: str, now: bool = True, db: Session = Depends(get_db)):
    if now:
        allFinancials = db.query(QuarterlyFinancials).filter(QuarterlyFinancials.ticker == ticker).order_by(QuarterlyFinancials.timestamp.desc()).first()
        if allFinancials is not None:
            allFinancials = [allFinancials]
        else:
            allFinancials = []
    else:
        allFinancials = db.query(QuarterlyFinancials).filter(QuarterlyFinancials.ticker == ticker).order_by(QuarterlyFinancials.timestamp.desc()).all()
    return allFinancials

@app.get("/data/earnings/effect", tags = ["data", "earnings"], response_model = QuarterlyFinancialsEffectPD)
async def getEarningsEffect(ticker: str, db: Session = Depends(get_db)):
    effect = db.query(QuarterlyFinancialsEffect).filter(QuarterlyFinancialsEffect.ticker == ticker).first()
    if effect is None:
        raise HTTPException(404, "ticker not found in quarterly financials effect table")
    return effect

## yahoo extra data
@app.get("/data/earnings/ratings", tags = ["data", "earnings"], response_model = EarningRatingsPD)
async def getEarningsRatings(ticker: str, db: Session = Depends(get_db)):
    # ticker = Column(String, primary_key=True, index=True)
    # timestamp = Column(DateTime, primary_key=True, index=True)
    # analyst_rating = Column(Float)
    # pricetarget_low = Column(Float)
    # pricetarget_average = Column(Float)
    # pricetarget_high = Column(Float)
    # pricetarget_current = Column(Float)
    # current_performance = Column(Integer) #
    if ticker not in ALLOWED_STOCKS:
        raise HTTPException(status_code=400, detail="Ticker not allowed")
    
    # try to get them from db
    results = db.query(EarningRatings).filter(EarningRatings.ticker == ticker).order_by(EarningRatings.timestamp.desc()).first()
    if results is None:
        raise HTTPException(404, "ticker data not found in earnings ratings table")
    # convert to pydantic
    results.similar_stocks =results.similar_stocks.split(",")
    earnRatObj = EarningRatingsPD(**results.__dict__)
    return earnRatObj

@app.get("/data/earnings/ratings/all", tags = ["data", "earnings"], response_model = List[EarningRatingsPD])
async def getAllEarningsRatings(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1.5)
    results = db.query(EarningRatings).filter(EarningRatings.timestamp <= now).filter(EarningRatings.timestamp >= yesterday).all()
    if len(results) == 0 or results is None:
        logError("getAllEarningsRatings", "all", "cant get any  data for earnings ratings...")
        raise HTTPException(500, "cant get any  data for earnings ratings...")
    response = []
    alreadyHave = []
    for res in results:
        if res.ticker not in alreadyHave:
            res.similar_stocks =res.similar_stocks.split(",")
            earnRatObj = EarningRatingsPD(**res.__dict__)
            response.append(earnRatObj)
            alreadyHave.append(res.ticker)
    return response


## graph plot
@app.get("/plot/portfolioworths", tags = ["data", "plot"])
async def getPlotPortfolio(db: Session = Depends(get_db)):
    figure = await getCurrentPortfolioGraph(db)
    return figure

if __name__ == "__main__":
    uvicorn.run(app)