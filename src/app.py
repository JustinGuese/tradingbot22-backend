import traceback

from fastapi import Depends, FastAPI, HTTPException, Request
from starlette.exceptions import HTTPException as StarletteHTTPException

from alphavantage import router as alphavantage_router
from bots import router as bots_router
from buysell import router as buysell_router
from logger import logger
from portfolio import router as portfolio_router
from pricing import router as pricing_router
from ratings import router as ratings_router
from update import router as update_router

app = FastAPI(title="tradingbot api 2.0")
app.include_router(bots_router, prefix="/bots", tags=["bots"])
app.include_router(buysell_router, prefix="/buysell", tags=["buysell"])
app.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
app.include_router(pricing_router, prefix="/pricing", tags=["pricing"])
app.include_router(update_router, prefix="/update", tags=["update"])
app.include_router(ratings_router, prefix="/ratings", tags=["ratings"])
app.include_router(
    alphavantage_router, prefix="/update/alphavantage", tags=["alphavantage"]
)


@app.exception_handler(Exception)
async def handle_normal_excp(request, exception):
    logger.error(traceback.format_exc())
    raise exception
