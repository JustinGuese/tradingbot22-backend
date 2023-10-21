from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from bots import getBot
from db import Bot, get_db
from logger import logger
from portfolio import getPortfolioWorth
from pricing import getCurrentPrice

router = APIRouter()


@router.get("/portfolioworths")
def updatePortfolioWorths(db: Session = Depends(get_db)):
    bots = db.query(Bot).all()
    for bot in bots:
        # getPortfolioWorth automatically commits update to db
        _ = getPortfolioWorth(bot.name, db)
    return {"message": "success"}
