from datetime import date, datetime
from os import environ
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import (JSON, Boolean, Column, Date, DateTime, Float, Integer,
                        String, create_engine, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import BigInteger

from pydantic_sqlalchemy import sqlalchemy_to_pydantic
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = "postgresql+psycopg2://" + environ["PSQL_URL"] # user:password@postgresserver/db

engine = create_engine(DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# class bot
class Bot(Base):
    __tablename__ = "bots"
    # id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, primary_key=True, index=True)
    description = Column(String, default = "no description yet")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class StockData(Base):
    __tablename__ = "stock_data"
    timestamp = Column(DateTime, primary_key=True, index=True)
    ticker = Column(String, primary_key=True, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)
    adj_close = Column(Float)

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    bot = Column(String, ForeignKey("bots.name"))
    ticker = Column(String, index=True)
    buy = Column(Boolean)
    price = Column(Float)
    quantity = Column(Integer)

BotPD = sqlalchemy_to_pydantic(Bot)
StockDataPD = sqlalchemy_to_pydantic(StockData)
TradePD = sqlalchemy_to_pydantic(Trade)

Base.metadata.create_all(engine)