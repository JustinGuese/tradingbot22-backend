from datetime import datetime, timedelta
from typing import Dict

import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from bots import getBot
from db import get_db
from logger import logger

router = APIRouter()

PRICE_CACHE_MINS = 30
PRICE_MEMORY = dict()


def getCurrentPrice(ticker: str) -> float:
    global PRICE_MEMORY
    refresh = True
    if ticker in PRICE_MEMORY:
        if datetime.utcnow() < PRICE_MEMORY[ticker]["expiry"]:
            refresh = False
    if refresh:
        try:
            ticker = yf.Ticker(ticker)
            PRICE_MEMORY[ticker] = {
                "price": ticker.history(period="1d")["Close"][0],
                "expiry": datetime.utcnow() + timedelta(minutes=PRICE_CACHE_MINS),
            }
        except Exception as e:
            logger.error("could not get price data for " + ticker)
    return PRICE_MEMORY[ticker]["price"]


@router.get("/{ticker}")
def getPrice(ticker: str) -> float:
    try:
        price = getCurrentPrice(ticker)
    except Exception as e:
        raise HTTPException(
            status_code=404, detail="could not get price data for ticekr"
        )
    return price
