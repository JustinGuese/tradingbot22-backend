from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from buysell import __buy_stock, __sell_stock
from db import StopLoss, Trade
from elastic import logError
from pricing_functions import __getCurrentPrice


async def __closeTrade(trade: Trade, db:Session):
    # close trade
    print(f'{trade.bot} - Closing tradeid {trade.id}. {trade.ticker} {trade.quantity}')
    await __sell_stock(botname = trade.bot, ticker = trade.ticker, 
            db=db, amount = trade.quantity,
            amountInUSD = False, short= trade.short)
    db.delete(trade)
    db.commit()

async def checkOpenStoplosses(db: Session):
    # grab all open stoplosses from db
    allStoplosses = db.query(StopLoss).all()
    print("starting stoploss check for %d open trades" % len(allStoplosses))
    if len(allStoplosses) > 0:
        for stoploss in allStoplosses:
            try:
                # bot = Column(String, ForeignKey("bots.name", ondelete="CASCADE"))
                # ticker = Column(String, primary_key=True, index=True)
                # timestamp = Column(DateTime, primary_key=True, index=True, default = datetime.utcnow)
                # trade_id = Column(Integer, ForeignKey("trades.id", ondelete="CASCADE"))
                # # stop loss specific
                # close_if_below = Column(Float)
                # close_if_above = Column(Float)
                # maximum_date = Column(DateTime, nullable = True) # close it if this date is reached
                trade = db.query(Trade).filter(Trade.id == stoploss.trade_id).first()
                if trade is None:
                    raise HTTPException(status_code=404, detail="Trade not found. cant close trade stoploss")
                
                if stoploss.maximum_date is not None:
                    if stoploss.maximum_date < datetime.utcnow():
                        await __closeTrade(trade, db)
                # next grab the current mf price
                crntPrice = await __getCurrentPrice(trade.ticker)
                if not trade.short:
                    if stoploss.close_if_above < stoploss.close_if_below:
                        raise HTTPException(status_code=500, detail="close_if_above is lower than close_if_below for a long position. cant be")
                    # was a long order
                    if stoploss.close_if_below_hardlimit is not None:
                        if stoploss.close_if_below_hardlimit > stoploss.close_if_below:
                            raise HTTPException(status_code=500, detail="close_if_below_hardlimit is higher than close_if_below for a long position. cant be")
                        # we want to use this as a hard limit. so if below that one directly sell,
                        # otherwise if it is none, we want to treat close_if_below as this.
                        # otherwise if it is set, and we are abive it and between close_if_below do nothing,
                        # otherwise if we are below close_if_below and and we are above close_if_below, set close_if_below to close_if_below_hardlimit
                        # like a trailing stoploss
                        if crntPrice < stoploss.close_if_below_hardlimit:
                            print("hard stop loss")
                            await __closeTrade(trade, db)
                        elif crntPrice < stoploss.close_if_below:
                            # if we are inbetween close_if_below_hardlimit and close_if_below, do nothing
                            pass
                        elif crntPrice > stoploss.close_if_below and crntPrice < stoploss.close_if_above:
                            # adapt the stoploss trailing stoploss
                            stoploss.close_if_below_hardlimit = stoploss.close_if_below 
                            stoploss.close_if_below = crntPrice * 1.05
                            # write changes to db
                            db.add(stoploss)
                            db.commit()
                        elif crntPrice > stoploss.close_if_above:
                            print("take profit ")
                            await __closeTrade(trade, db)
                    else:
                        # there was no specific hard limit set, so treating close_if_below as hard limit
                        if crntPrice < stoploss.close_if_below:
                            print("stop loss")
                            await __closeTrade(trade, db)
                        elif crntPrice > stoploss.close_if_above:
                            print("take profit ")
                            await __closeTrade(trade, db)
                else:
                    # was a short
                    if stoploss.close_if_above > stoploss.close_if_below:
                        raise HTTPException(status_code=500, detail="close_if_above is lower than close_if_below for a short position. cant be")
                    # TODO: not really implemented yet
                    if crntPrice > stoploss.close_if_above:
                        print("stop loss")
                        await __closeTrade(trade, db)
                    elif crntPrice < stoploss.close_if_below:
                        print("take profit ")
                        await __closeTrade(trade, db)
            except Exception as e:
                print("problem with stoploss of: " + str(stoploss.ticker))
                logError("stoploss", str(stoploss.ticker), str(e), severity="critical")
                raise