from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import Bot, BotCreatePD, BotPD, get_db
from logger import logger

router = APIRouter()


@router.get("/", response_model=List[BotPD])
def getBots(db: Session = Depends(get_db)):
    allBots = db.query(Bot).all()
    allBots = [BotPD.model_validate(bot) for bot in allBots]
    return allBots


@router.get("/{bot_name}", response_model=BotPD)
def getBot(bot_name: str, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.name == bot_name).first()
    if bot is None:
        logger.warning(f"Bot {bot_name} not found")
        raise HTTPException(status_code=404, detail="Bot not found")
    return BotPD.model_validate(bot)


@router.put("/")
def updateBot(bot: BotCreatePD, db: Session = Depends(get_db)):
    dbbot = db.query(Bot).filter(Bot.name == bot.name).first()
    if dbbot is None:
        # create new bot
        bot = Bot(**bot.model_dump())
        db.add(bot)
    else:
        # update
        dbbot.description = bot.description
        dbbot.portfolio = bot.portfolio
        dbbot.live = bot.live
        dbbot.name = bot.name
        db.merge(dbbot)
    db.commit()
    return BotPD.model_validate(bot)


@router.delete("/{bot_name}")
def deleteBot(bot_name: str, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.name == bot_name).first()
    if bot is None:
        logger.warning(f"Bot {bot_name} not found in delete route")
        raise HTTPException(status_code=404, detail="Bot not found")
    db.delete(bot)
    db.commit()
    return {"message": "Bot deleted"}
