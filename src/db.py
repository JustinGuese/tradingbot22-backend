import enum
from datetime import date, datetime, timedelta
from os import environ
from typing import List, Optional

from pydantic import BaseModel
from pydantic_sqlalchemy import sqlalchemy_to_pydantic
from sqlalchemy import (JSON, BigInteger, Boolean, Column, Date, DateTime,
                        Enum, Float, ForeignKey, Integer, String,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.types import BigInteger

DATABASE_URL = "postgresql+psycopg2://" + environ.get("PSQL_URL", "postgres:postgres@192.168.178.36:31432/postgres") # user:password@postgresserver/db

engine = create_engine(DATABASE_URL,
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
    bot = Column(String, ForeignKey("bots.name", ondelete="CASCADE"))
    ticker = Column(String, index=True)
    buy = Column(Boolean)
    short = Column(Boolean)
    price = Column(Float)
    quantity = Column(Float)

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

class TAType(str, enum.Enum):
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
    
## news
    
class News(Base):
    __tablename__ = "news"
    uuid = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    ticker = Column(String, index=True)
    title = Column(String)
    total_score = Column(Float)
    pos_score = Column(Float)
    neg_score = Column(Float)
    
## recommendations / analyst ratings
    
class Recommendation(Base):
    __tablename__ = "expert_recommendation"
    timestamp = Column(DateTime, primary_key=True, index=True)
    ticker = Column(String, primary_key=True, index=True)
    company = Column(String, primary_key=True, index=True)
    rating = Column(String)
    rating_before = Column(String)
    action = Column(String)

## earnings

class EarningDates(Base):
    __tablename__ = "earning_dates"
    timestamp = Column(DateTime, primary_key=True, index=True)
    ticker = Column(String, primary_key=True, index=True)
    earnings_avg = Column(Float)
    earnings_low = Column(Float)
    earnings_high = Column(Float)
    # rev
    revenue_avg = Column(BigInteger) # might need bigint
    revenue_low = Column(BigInteger)
    revenue_high = Column(BigInteger)

class QuarterlyFinancials(Base):
    __tablename__ = "quarterly_financials"
    timestamp = Column(Date, primary_key=True, index=True)
    ticker = Column(String, primary_key=True, index=True)
    # the values
    research_development  = Column(BigInteger, nullable=True)
    effect_of_accounting_charges  = Column(BigInteger, nullable=True)
    income_before_tax  = Column(BigInteger, nullable=True)
    minority_interest  = Column(BigInteger, nullable=True)
    net_income  = Column(BigInteger, nullable=True)
    selling_general_administrative  = Column(BigInteger, nullable=True)
    gross_profit  = Column(BigInteger, nullable=True)
    ebit  = Column(BigInteger, nullable=True)
    operating_income  = Column(BigInteger, nullable=True)
    other_operating_expenses  = Column(BigInteger, nullable=True)
    interest_expense  = Column(BigInteger, nullable=True)
    extraordinary_items  = Column(BigInteger, nullable=True)
    non_recurring  = Column(BigInteger, nullable=True)
    other_items  = Column(BigInteger, nullable=True)
    income_tax_expense  = Column(BigInteger, nullable=True)
    total_revenue  = Column(BigInteger, nullable=True)
    total_operating_expenses  = Column(BigInteger, nullable=True)
    cost_of_revenue  = Column(BigInteger, nullable=True)
    total_other_income_expense_net  = Column(BigInteger, nullable=True)
    discontinued_operations  = Column(BigInteger, nullable=True)
    net_income_from_continuing_ops  = Column(BigInteger, nullable=True)
    net_income_applicable_to_common_shares  = Column(BigInteger, nullable=True)

# quarterly financial effect storage
class QuarterlyFinancialsEffect(Base):
    __tablename__ = "quarterly_financials_effect"
    ticker = Column(String, primary_key=True, index=True, unique=True)
    medchange = Column(Float)
    medvariance = Column(Float)
    all_changes_list = Column(String)
    best = Column(MutableDict.as_mutable(JSON))

## stop loss take profit object
class StopLoss(Base):
    __tablename__ = "open_stoplosses"
    bot = Column(String, ForeignKey("bots.name", ondelete="CASCADE"))
    ticker = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, primary_key=True, index=True, default = datetime.utcnow)
    trade_id = Column(Integer, ForeignKey("trades.id", ondelete="CASCADE"))
    # stop loss specific
    close_if_below = Column(Float)
    close_if_above = Column(Float)
    maximum_date = Column(DateTime, nullable = True) # close it if this date is reached"

class EarningRatings(Base):
    __tablename__ = "earning_ratings"
    ticker = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, primary_key=True, index=True)
    similar_stocks = Column(String) # array in truth
    analyst_rating = Column(Float)
    pricetarget_low = Column(Float)
    pricetarget_average = Column(Float)
    pricetarget_high = Column(Float)
    pricetarget_current = Column(Float)
    current_performance = Column(Integer) #-2 very much below, -1., 0 as expected, 1 better, 2 outperform 

## pydantic #########

BotPD = sqlalchemy_to_pydantic(Bot)
StockDataPD = sqlalchemy_to_pydantic(StockData)
TradePD = sqlalchemy_to_pydantic(Trade)
TechnicalAnalysisPD = sqlalchemy_to_pydantic(TechnicalAnalysis)
EarningDatesPD = sqlalchemy_to_pydantic(EarningDates)
QuarterlyFinancialsPD = sqlalchemy_to_pydantic(QuarterlyFinancials)
QuarterlyFinancialsEffectPD = sqlalchemy_to_pydantic(QuarterlyFinancialsEffect)
# EarningRatingsPD = sqlalchemy_to_pydantic(EarningRatings)

# custom pydantic
class NewBotPD(BaseModel):
    name: str
    description: str

class GetTradeDataPD(BaseModel):
    ticker: str
    start_date: date = (datetime.utcnow() - timedelta(7)).date()
    end_date: date = datetime.utcnow().date()
    technical_analysis_columns: List[TAType] = []
    
class EarningRatingsPD(BaseModel):
    ticker: str
    timestamp: datetime
    similar_stocks: List[str] # array in truth
    analyst_rating: float
    pricetarget_low: float
    pricetarget_average: float
    pricetarget_high: float
    pricetarget_current: float
    current_performance: int

Base.metadata.create_all(engine)
