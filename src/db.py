from datetime import date, datetime, timedelta
from enum import Enum
from os import environ
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_sqlalchemy import sqlalchemy_to_pydantic
from sqlalchemy import (JSON, Boolean, Column, Date, DateTime, Float,
                        ForeignKey, Integer, String, create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.types import BigInteger

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
        
class Stock(Base):
    __tablename__ = "stocks"
    ticker = Column(String, primary_key=True)

# class bot
class Bot(Base):
    __tablename__ = "bots"
    # id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, primary_key=True, index=True)
    description = Column(String, default = "no description yet")
    startMoney = Column(Float, default = 10000)
    portfolio = Column(MutableDict.as_mutable(JSON), default = lambda: {"USD": 10000})
    portfolioWorth = Column(Float, default = 10000.)
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

# ta
# all ta columns
TA_COLUMNS = [
    'volume_adi','volume_obv', 'volume_cmf', 'volume_fi', 'volume_em', 'volume_sma_em',
    'volume_vpt', 'volume_vwap', 'volume_mfi', 'volume_nvi',
    'volatility_bbm', 'volatility_bbh', 'volatility_bbl', 'volatility_bbw',
    'volatility_bbp', 'volatility_bbhi', 'volatility_bbli',
    'volatility_kcc', 'volatility_kch', 'volatility_kcl', 'volatility_kcw',
    'volatility_kcp', 'volatility_kchi', 'volatility_kcli',
    'volatility_dcl', 'volatility_dch', 'volatility_dcm', 'volatility_dcw',
    'volatility_dcp', 'volatility_atr', 'volatility_ui', 'trend_macd',
    'trend_macd_signal', 'trend_macd_diff', 'trend_sma_fast',
    'trend_sma_slow', 'trend_ema_fast', 'trend_ema_slow',
    'trend_vortex_ind_pos', 'trend_vortex_ind_neg', 'trend_vortex_ind_diff',
    'trend_trix', 'trend_mass_index', 'trend_dpo', 'trend_kst',
    'trend_kst_sig', 'trend_kst_diff', 'trend_ichimoku_conv',
    'trend_ichimoku_base', 'trend_ichimoku_a', 'trend_ichimoku_b',
    'trend_stc', 'trend_adx', 'trend_adx_pos', 'trend_adx_neg', 'trend_cci',
    'trend_visual_ichimoku_a', 'trend_visual_ichimoku_b', 'trend_aroon_up',
    'trend_aroon_down', 'trend_aroon_ind', 'trend_psar_up',
    'trend_psar_down', 'trend_psar_up_indicator',
    'trend_psar_down_indicator', 'momentum_rsi', 'momentum_stoch_rsi',
    'momentum_stoch_rsi_k', 'momentum_stoch_rsi_d', 'momentum_tsi',
    'momentum_uo', 'momentum_stoch', 'momentum_stoch_signal', 'momentum_wr',
    'momentum_ao', 'momentum_roc', 'momentum_ppo', 'momentum_ppo_signal',
    'momentum_ppo_hist', 'momentum_pvo', 'momentum_pvo_signal',
    'momentum_pvo_hist', 'momentum_kama', 'others_dr', 'others_dlr',
    'others_cr'
]

class TAType(str, Enum):
    volume_adi = "volume_adi"
    volume_obv = "volume_obv"
    volume_cmf = "volume_cmf"
    volume_fi = "volume_fi"
    volume_em = "volume_em"
    volume_sma_em = "volume_sma_em"
    volume_vpt = "volume_vpt"
    volume_vwap = "volume_vwap"
    volume_mfi = "volume_mfi"
    volume_nvi = "volume_nvi"
    volatility_bbm = "volatility_bbm"
    volatility_bbh = "volatility_bbh"
    volatility_bbl = "volatility_bbl"
    volatility_bbw = "volatility_bbw"
    volatility_bbp = "volatility_bbp"
    volatility_bbhi = "volatility_bbhi"
    volatility_bbli = "volatility_bbli"
    volatility_kcc = "volatility_kcc"
    volatility_kch = "volatility_kch"
    volatility_kcl = "volatility_kcl"
    volatility_kcw = "volatility_kcw"
    volatility_kcp = "volatility_kcp"
    volatility_kchi = "volatility_kchi"
    volatility_kcli = "volatility_kcli"
    volatility_dcl = "volatility_dcl"
    volatility_dch = "volatility_dch"
    volatility_dcm = "volatility_dcm"
    volatility_dcw = "volatility_dcw"
    volatility_dcp = "volatility_dcp"
    volatility_atr = "volatility_atr"
    volatility_ui = "volatility_ui"
    trend_macd = "trend_macd"
    trend_macd_signal = "trend_macd_signal"
    trend_macd_diff = "trend_macd_diff"
    trend_sma_fast = "trend_sma_fast"
    trend_sma_slow = "trend_sma_slow"
    trend_ema_fast = "trend_ema_fast"
    trend_ema_slow = "trend_ema_slow"
    trend_vortex_ind_pos = "trend_vortex_ind_pos"
    trend_vortex_ind_neg = "trend_vortex_ind_neg"
    trend_vortex_ind_diff = "trend_vortex_ind_diff"
    trend_trix = "trend_trix"
    trend_mass_index = "trend_mass_index"
    trend_dpo = "trend_dpo"
    trend_kst = "trend_kst"
    trend_kst_sig = "trend_kst_sig"
    trend_kst_diff = "trend_kst_diff"
    trend_ichimoku_conv = "trend_ichimoku_conv"
    trend_ichimoku_base = "trend_ichimoku_base"
    trend_ichimoku_a = "trend_ichimoku_a"
    trend_ichimoku_b = "trend_ichimoku_b"
    trend_stc = "trend_stc"
    trend_adx = "trend_adx"
    trend_adx_pos = "trend_adx_pos"
    trend_adx_neg = "trend_adx_neg"
    trend_cci = "trend_cci"
    trend_visual_ichimoku_a = "trend_visual_ichimoku_a"
    trend_visual_ichimoku_b = "trend_visual_ichimoku_b"
    trend_aroon_up = "trend_aroon_up"
    trend_aroon_down = "trend_aroon_down"
    trend_aroon_ind = "trend_aroon_ind"
    trend_psar_up = "trend_psar_up"
    trend_psar_down = "trend_psar_down"
    trend_psar_up_indicator = "trend_psar_up_indicator"
    trend_psar_down_indicator = "trend_psar_down_indicator"
    momentum_rsi = "momentum_rsi"
    momentum_stoch_rsi = "momentum_stoch_rsi"
    momentum_stoch_rsi_k = "momentum_stoch_rsi_k"
    momentum_stoch_rsi_d = "momentum_stoch_rsi_d"
    momentum_tsi = "momentum_tsi"
    momentum_uo = "momentum_uo"
    momentum_stoch = "momentum_stoch"
    momentum_stoch_signal = "momentum_stoch_signal"
    momentum_wr = "momentum_wr"
    momentum_ao = "momentum_ao"
    momentum_roc = "momentum_roc"
    momentum_ppo = "momentum_ppo"
    momentum_ppo_signal = "momentum_ppo_signal"
    momentum_ppo_hist = "momentum_ppo_hist"
    momentum_pvo = "momentum_pvo"
    momentum_pvo_signal = "momentum_pvo_signal"
    momentum_pvo_hist = "momentum_pvo_hist"
    momentum_kama = "momentum_kama"
    others_dr = "others_dr"
    others_dlr = "others_dlr"
    others_cr = "others_cr"
    # smas
    SMA_3 = "SMA_3"
    SMA_10 = "SMA_10"
    SMA_50 = "SMA_50"
    SMA_100 = "SMA_100"
    SMA_200 = "SMA_200"
    # all
    all = "all"


class TechnicalAnalysis(Base):
    __tablename__ = "technical_analysis"
    timestamp = Column(DateTime, primary_key=True, index=True)
    ticker = Column(String, primary_key=True, index=True)
    volume_adi = Column(Float)
    volume_obv = Column(Float)
    volume_cmf = Column(Float)
    volume_fi = Column(Float)
    volume_em = Column(Float)
    volume_sma_em = Column(Float)
    volume_vpt = Column(Float)
    volume_vwap = Column(Float)
    volume_mfi = Column(Float)
    volume_nvi = Column(Float)
    volatility_bbm = Column(Float)
    volatility_bbh = Column(Float)
    volatility_bbl = Column(Float)
    volatility_bbw = Column(Float)
    volatility_bbp = Column(Float)
    volatility_bbhi = Column(Float)
    volatility_bbli = Column(Float)
    volatility_kcc = Column(Float)
    volatility_kch = Column(Float)
    volatility_kcl = Column(Float)
    volatility_kcw = Column(Float)
    volatility_kcp = Column(Float)
    volatility_kchi = Column(Float)
    volatility_kcli = Column(Float)
    volatility_dcl = Column(Float)
    volatility_dch = Column(Float)
    volatility_dcm = Column(Float)
    volatility_dcw = Column(Float)
    volatility_dcp = Column(Float)
    volatility_atr = Column(Float)
    volatility_ui = Column(Float)
    trend_macd = Column(Float)
    trend_macd_signal = Column(Float)
    trend_macd_diff = Column(Float)
    trend_sma_fast = Column(Float)
    trend_sma_slow = Column(Float)
    trend_ema_fast = Column(Float)
    trend_ema_slow = Column(Float)
    trend_vortex_ind_pos = Column(Float)
    trend_vortex_ind_neg = Column(Float)
    trend_vortex_ind_diff = Column(Float)
    trend_trix = Column(Float)
    trend_mass_index = Column(Float)
    trend_dpo = Column(Float)
    trend_kst = Column(Float)
    trend_kst_sig = Column(Float)
    trend_kst_diff = Column(Float)
    trend_ichimoku_conv = Column(Float)
    trend_ichimoku_base = Column(Float)
    trend_ichimoku_a = Column(Float)
    trend_ichimoku_b = Column(Float)
    trend_stc = Column(Float)
    trend_adx = Column(Float)
    trend_adx_pos = Column(Float)
    trend_adx_neg = Column(Float)
    trend_cci = Column(Float)
    trend_visual_ichimoku_a = Column(Float)
    trend_visual_ichimoku_b = Column(Float)
    trend_aroon_up = Column(Float)
    trend_aroon_down = Column(Float)
    trend_aroon_ind = Column(Float)
    trend_psar_up = Column(Float)
    trend_psar_down = Column(Float)
    trend_psar_up_indicator = Column(Float)
    trend_psar_down_indicator = Column(Float)
    momentum_rsi = Column(Float)
    momentum_stoch_rsi = Column(Float)
    momentum_stoch_rsi_k = Column(Float)
    momentum_stoch_rsi_d = Column(Float)
    momentum_tsi = Column(Float)
    momentum_uo = Column(Float)
    momentum_stoch = Column(Float)
    momentum_stoch_signal = Column(Float)
    momentum_wr = Column(Float)
    momentum_ao = Column(Float)
    momentum_roc = Column(Float)
    momentum_ppo = Column(Float)
    momentum_ppo_signal = Column(Float)
    momentum_ppo_hist = Column(Float)
    momentum_pvo = Column(Float)
    momentum_pvo_signal = Column(Float)
    momentum_pvo_hist = Column(Float)
    momentum_kama = Column(Float)
    others_dr = Column(Float)
    others_dlr = Column(Float)
    others_cr = Column(Float)
    # manually added later on
    SMA_3 = Column(Float)
    SMA_10 = Column(Float)
    SMA_50 = Column(Float)
    SMA_100 = Column(Float)
    SMA_200 = Column(Float)

BotPD = sqlalchemy_to_pydantic(Bot)
StockDataPD = sqlalchemy_to_pydantic(StockData)
TradePD = sqlalchemy_to_pydantic(Trade)
TechnicalAnalysisPD = sqlalchemy_to_pydantic(TechnicalAnalysis)

# custom pydantic
class NewBotPD(BaseModel):
    name: str
    description: str

class GetTradeDataPD(BaseModel):
    ticker: str
    start_date: date = (datetime.utcnow() - timedelta(7)).date()
    end_date: date = datetime.utcnow().date()
    technical_analysis_columns: List[TAType] = []

Base.metadata.create_all(engine)
