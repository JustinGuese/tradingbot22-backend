from datetime import datetime

import requests
from lxml import etree
from sqlalchemy.orm import Session

from db import EarningRatings

# from elastic import logError


# Scrape stock data from yahoo
async def __getYahooEarningsRatingsData(symbol, s: requests.Session) -> tuple:
    response = s.get(f'https://finance.yahoo.com/quote/{symbol}')
    source = response.text
    dom = etree.HTML(source)

    # Similar stocks
    similar_stocks = [stock.text for stock in dom.xpath('//*[@id="similar-by-symbol"]//tr//a')]

    # Analyst rating
    analyst_rating = dom.xpath('//span[contains(.,"Recommendation Rating")]/ancestor::section//div[@data-test="rec-rating-txt"]')[0].text

    # Selects the analyst price targets section
    analyst_price_targets = dom.xpath('//h2[contains(.,"Analyst Price Targets")]/ancestor::section')[0]

    # Searches the price targets section for required values
    pricetarget_low = analyst_price_targets.xpath('//span[contains(.,"Low")]/following-sibling::span[1]')[0].text
    pricetarget_average = analyst_price_targets.xpath('//span[contains(.,"Average")]/following-sibling::span[1]')[0].text
    pricetarget_high = analyst_price_targets.xpath('//span[contains(.,"High")]/following-sibling::span[1]')[0].text
    pricetarget_current = analyst_price_targets.xpath('//span[contains(.,"Current")]/following-sibling::span[1]')[0].text

    # Console outputs
    # print(f"Similar stocks: {similar_stocks}")
    # print(f"Analyst rating: {analyst_rating}")
    # print(f"Low: {pricetarget_low}, Average: {pricetarget_average}, High: {pricetarget_high}, Current: {pricetarget_current}")

    return similar_stocks, analyst_rating, pricetarget_low, pricetarget_average, pricetarget_high, pricetarget_current


async def updateYahooEarningsRatingsData(tickers: list, db: Session):
    s = requests.Session()
    for ticker in tickers:
        try:
            similar_stocks, analyst_rating, pricetarget_low, pricetarget_average, pricetarget_high, pricetarget_current = await __getYahooEarningsRatingsData(ticker, s)
            if pricetarget_current < pricetarget_low:
                current_performance = -2
            elif pricetarget_current < pricetarget_average and pricetarget_current > pricetarget_low:
                current_performance = -1
            elif pricetarget_current > pricetarget_average and pricetarget_current < pricetarget_high:
                current_performance = 1
            elif pricetarget_current > pricetarget_high:
                current_performance = 2
            else:
                current_performance = 0
            
            earningrObj = EarningRatings(
                ticker = ticker,
                timestamp = datetime.utcnow(),
                similar_stocks = ",".join(similar_stocks),
                analyst_rating = float(analyst_rating),
                pricetarget_low = float(pricetarget_low),
                pricetarget_average = float(pricetarget_average),
                pricetarget_high = float(pricetarget_high),
                pricetarget_current = float(pricetarget_current),
                current_performance = current_performance
            )
            db.add(earningrObj)
            db.commit()
        except Exception as e:
            # print("error in updateyahooearningsratings. could not update for ticker: " + ticker + " error: " + str(e))
            # logError(module = "updateyahooearningsratings", stock= ticker, error = str(e))
            pass
            # it just isnt there for some stocks :(