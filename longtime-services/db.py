import enum
from os import environ
from typing import List

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
from sqlalchemy.orm import Mapped, mapped_column, relationship, sessionmaker

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


db = SessionLocal()

Base.metadata.create_all(bind=engine)
