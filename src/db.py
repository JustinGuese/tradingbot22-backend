import enum
from datetime import datetime
from os import environ
from typing import List

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.types import BigInteger

DATABASE_URL = "postgresql+psycopg2://" + environ.get(
    "PSQL_URL", "postgres:postgres@localhost:5432/postgres"
)  # user:password@postgresserver/db

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
    # echo=True # debugging
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
    name = Column(String, unique=True, primary_key=True, index=True)
    description = Column(String, default="no description yet")
    start_money = Column(Float, default=10000)
    portfolio = Column(MutableDict.as_mutable(JSON), default=lambda: {"USD": 10000})
    portfolio_worth = Column(Float, default=10000.0)
    live = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BotCreatePD(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str = "no description yet"
    portfolio: dict = {"USD": 10000}
    live: bool = False


class BotPD(BotCreatePD):
    model_config = ConfigDict(from_attributes=True)
    start_money: float = 10000.0
    portfolio_worth: float = 10000.0
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()


class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    bot = Column(String, ForeignKey("bots.name", ondelete="CASCADE"))
    ticker = Column(String, index=True)
    buy = Column(Boolean)
    short = Column(Boolean)
    price = Column(Float)
    quantity = Column(Float)
    live = Column(Boolean, default=False)


class Recommendation(Base):
    __tablename__ = "expert_recommendation"
    timestamp = Column(DateTime, primary_key=True, index=True)
    ticker = Column(String, primary_key=True, index=True)
    company = Column(String, primary_key=True, index=True)
    rating = Column(String)
    rating_before = Column(String)
    action = Column(String)


class EarningDates(Base):
    __tablename__ = "earning_dates"
    timestamp = Column(DateTime, primary_key=True, index=True)
    ticker = Column(String, primary_key=True, index=True)
    estimate = Column(Float)
    reported = Column(Float)
    surprise_pct = Column(Float)


class QuarterlyFinancials(Base):
    __tablename__ = "quarterly_financials"
    timestamp = Column(Date, primary_key=True, index=True)
    ticker = Column(String, primary_key=True, index=True)
    # the values
    research_development = Column(BigInteger, nullable=True)
    effect_of_accounting_charges = Column(BigInteger, nullable=True)
    income_before_tax = Column(BigInteger, nullable=True)
    minority_interest = Column(BigInteger, nullable=True)
    net_income = Column(BigInteger, nullable=True)
    selling_general_administrative = Column(BigInteger, nullable=True)
    gross_profit = Column(BigInteger, nullable=True)
    ebit = Column(BigInteger, nullable=True)
    operating_income = Column(BigInteger, nullable=True)
    other_operating_expenses = Column(BigInteger, nullable=True)
    interest_expense = Column(BigInteger, nullable=True)
    extraordinary_items = Column(BigInteger, nullable=True)
    non_recurring = Column(BigInteger, nullable=True)
    other_items = Column(BigInteger, nullable=True)
    income_tax_expense = Column(BigInteger, nullable=True)
    total_revenue = Column(BigInteger, nullable=True)
    total_operating_expenses = Column(BigInteger, nullable=True)
    cost_of_revenue = Column(BigInteger, nullable=True)
    total_other_income_expense_net = Column(BigInteger, nullable=True)
    discontinued_operations = Column(BigInteger, nullable=True)
    net_income_from_continuing_ops = Column(BigInteger, nullable=True)
    net_income_applicable_to_common_shares = Column(BigInteger, nullable=True)


class PortfolioWorths(Base):
    __tablename__ = "portfolio_worths"
    bot = Column(String, ForeignKey("bots.name", ondelete="CASCADE"))
    timestamp = Column(DateTime, primary_key=True, index=True, default=datetime.utcnow)
    portfolio = Column(MutableDict.as_mutable(JSON))
    worth = Column(Float)


class EarningRatings(Base):
    __tablename__ = "earning_ratings"
    ticker = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, primary_key=True, index=True)
    similar_stocks = Column(String)  # array in truth
    analyst_rating = Column(Float)
    pricetarget_low = Column(Float)
    pricetarget_average = Column(Float)
    pricetarget_high = Column(Float)
    pricetarget_current = Column(Float)
    current_performance = Column(
        Integer
    )  # -2 very much below, -1., 0 as expected, 1 better, 2 outperform


### alphavantage news


class AlphaGainerLoserType(enum.Enum):
    GAINER = "gainer"
    LOSER = "loser"
    MOST_ACTIVE = "most_active"


class AlphaGainersLosers(Base):
    __tablename__ = "alphavantage_gainerslosers"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticker = Column(String, index=True)
    day = Column(Date, index=True)
    category = Column(ENUM(AlphaGainerLoserType))
    price = Column(Float)
    change_amount = Column(Float)
    change_pct = Column(Float)
    volume = Column(BigInteger)


class AlphaSentimentArticle(Base):
    __tablename__ = "alphavantage_sentiment_article"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    author = Column(String, index=True)
    title = Column(String, index=True)
    summary = Column(String)
    category = Column(String)
    source = Column(String)
    tickers: Mapped[List["AlphaSentiment"]] = relationship()


class SentimentCategory(enum.Enum):
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class AlphaSentiment(Base):
    __tablename__ = "alphavantage_sentiment"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticker = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    article_id = mapped_column(ForeignKey("alphavantage_sentiment_article.id"))
    article = relationship("AlphaSentimentArticle", back_populates="tickers")
    article_relevance_score = Column(Float)
    article_sentiment_score = Column(Float)
    article_sentiment_category = Column(ENUM(SentimentCategory))


Base.metadata.create_all(bind=engine)
