from datetime import datetime

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from buysell import __buy_stock, __sell_stock
from db import StopLoss


async def __writeStoplossToDB(botname: str, ticker: str, db: Session, buy: bool,
        # stop loss specific
        close_if_below: float, 
        close_if_above: float,
        trade_id: int,
        close_if_below_hardlimit: float = None,
        maximum_date: datetime = None,
        amount: float = -1,
        amountInUSD: bool = False, short: bool = False,
        ):
    # then open stop loss to db
    stoploss = StopLoss(
            bot = botname,
            ticker = ticker,
            trade_id = trade_id,
            close_if_below = close_if_below,
            close_if_above = close_if_above,
            close_if_below_hardlimit = close_if_below_hardlimit,
            maximum_date = maximum_date,
            )
    db.add(stoploss)
    db.commit()
    return stoploss

async def __buy_stock_stoploss(botname: str, ticker: str, db: Session, 
        # stop loss specific
        close_if_below: float, close_if_above: float,
        close_if_below_hardlimit: float = None,
        maximum_date: datetime = None,
        amount: float = -1,
        amountInUSD: bool = False, short: bool = False,
        ):
    # execute buy as usual
    tradeid = await __buy_stock(botname, ticker, db, amount, amountInUSD, short)
    # then open stop loss to db
    stoplossobj = await __writeStoplossToDB(botname, ticker, db, True, close_if_below, close_if_above, tradeid, close_if_below_hardlimit, maximum_date, amount, amountInUSD, short)
    
async def __sell_stock_stoploss(botname: str, ticker: str, db: Session, 
        # stop loss specific
        close_if_below: float, close_if_above: float,
        close_if_below_hardlimit: float = None,
        maximum_date: datetime = None,
        amount: float = -1,
        amountInUSD: bool = False, short: bool = False,
        ):
    tradeid = await __sell_stock(botname, ticker, db, amount, amountInUSD, short)
    # then proceed to write it to DB 
    stoplossobj = await __writeStoplossToDB(botname, ticker, db, False, close_if_below, close_if_above, tradeid, close_if_below_hardlimit, maximum_date, amount, amountInUSD, short)