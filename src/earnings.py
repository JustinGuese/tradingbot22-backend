from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session
from tqdm import tqdm

from db import EarningDates, QuarterlyFinancials, QuarterlyFinancialsEffect
from elastic import logError


def createTicker(ticker: str) -> yf.Ticker:
    return yf.Ticker(ticker)

def writeEarningsDates(tickerobj: yf.Ticker, ticker: str, db: Session):
    calendar = tickerobj.calendar
    if len(calendar) == 0:
        print("could not get earnings calendar for ticker", ticker)
        return
    calendar = calendar.T
    calendar = calendar.set_index('Earnings Date')
    for dt, row in calendar.iterrows():
        # first check if in db
        if not db.query(EarningDates).filter(EarningDates.ticker == ticker, EarningDates.timestamp == dt).first():
            earnobj = EarningDates(
                timestamp = dt,
                ticker = ticker,
                earnings_avg = float(row['Earnings Average']), # only save millions
                earnings_low = float(row['Earnings Low']),
                earnings_high = float(row['Earnings High']),
                # rev
                revenue_avg = int(row['Revenue Average'])/1000000,
                revenue_low = int(row['Revenue Low'])/1000000,
                revenue_high = int(row['Revenue High'])/1000000,
            )
            db.add(earnobj)
    db.commit()
    
def bigIntFix(possibleint):
    try:
        return int(possibleint) / 1000000 # only save millions
    except: # quality code
        return None
    
def writeQuarterlyFinancials(tickerobj: yf.Ticker, ticker: str, db: Session):
    # quarterly financials
    quarter = tickerobj.quarterly_financials
    quarter = quarter.T
    for date, row in quarter.iterrows():
        # first check if in db
        if not db.query(QuarterlyFinancials).filter(QuarterlyFinancials.ticker == ticker, QuarterlyFinancials.timestamp == date).first():
            qfobj = QuarterlyFinancials(
                timestamp = date,
                ticker = ticker,
                research_development = bigIntFix( row['Research Development']),
                effect_of_accounting_charges = bigIntFix( row['Effect Of Accounting Charges']),
                income_before_tax = bigIntFix( row['Income Before Tax']),
                minority_interest = bigIntFix( row['Minority Interest']),
                net_income = bigIntFix( row['Net Income']),
                selling_general_administrative = bigIntFix( row['Selling General Administrative']),
                gross_profit = bigIntFix( row['Gross Profit']),
                ebit = bigIntFix( row['Ebit']),
                operating_income = bigIntFix( row['Operating Income']),
                other_operating_expenses = bigIntFix( row['Other Operating Expenses']),
                interest_expense = bigIntFix( row['Interest Expense']),
                extraordinary_items = bigIntFix( row['Extraordinary Items']),
                non_recurring = bigIntFix( row['Non Recurring']),
                other_items = bigIntFix( row['Other Items']),
                income_tax_expense = bigIntFix( row['Income Tax Expense']),
                total_revenue = bigIntFix( row['Total Revenue']),
                total_operating_expenses = bigIntFix( row['Total Operating Expenses']),
                cost_of_revenue = bigIntFix( row['Cost Of Revenue']),
                total_other_income_expense_net = bigIntFix( row['Total Other Income Expense Net']),
                discontinued_operations = bigIntFix( row['Discontinued Operations']),
                net_income_from_continuing_ops = bigIntFix( row['Net Income From Continuing Ops']),
                net_income_applicable_to_common_shares = bigIntFix( row['Net Income Applicable To Common Shares']),
            )
            db.add(qfobj)
    db.commit()
    
def updateEarnings(ticker: str, db: Session):
    tickerobj = createTicker(ticker)
    try:
        writeEarningsDates(tickerobj, ticker, db)
    except Exception as e:
        raise
    # next quarterly financials
    try:
        writeQuarterlyFinancials(tickerobj, ticker, db)
    except Exception as e:
        raise
    
def __quarterKeyErrorFix(quarter, closedata):
    try:
        _ = closedata.loc[quarter]["Close"]
        return quarter
    except KeyError:
        for i in range(len(closedata)):
            if closedata.index[i] >= quarter:
                return closedata.index[i]
## preparation for tradingbot
# this one is expected to be triggered monthly, updates the price effect of latest earnings
def updateEarningEffect(STOCKS: list, db: Session):
    quarterlies = []
    for stock in tqdm(STOCKS):
        yobj = yf.Ticker(stock)
        quarterdata = yobj.quarterly_financials
        if len(quarterdata) == 0:
            print("cant get financials for stock. skipping: ", stock)
            continue
        quarterdata = quarterdata.T
        quarterdata = quarterdata.pct_change() 
        wins = [0]
        signals = [0]
        for i in range(len(quarterdata)):
            if i == 0:
                continue
            quarter = quarterdata.index[i]
            if not isinstance(quarter, datetime):
                print("quarter is not datetime, skip. is: ", str(quarter))
                continue
            start = quarter - timedelta(days=92)
            end = quarter + timedelta(days=15)
            # print(stock, start, end)
            closedata = yf.download(stock, start = start, end = end, progress= False)
            
            quarter = __quarterKeyErrorFix(quarter, closedata)
            
            winInQuarter = closedata.loc[quarter]["Close"] - closedata.iloc[0]["Close"]
            pctWinInQuarter = winInQuarter / closedata.iloc[0]["Close"]
            # print("the quarter ending on the " + str(quarter) + " had a " + str(pctWinInQuarter) + " pct win")
            
            wins.append(pctWinInQuarter)
            # check what happens in the next days
            winAfterPublish = closedata.iloc[-1]["Close"] - closedata.loc[quarter]["Close"]
            # try to aim for the highest or lowest price in these 15 days
            risenUp = winAfterPublish > 0
            targetCol = "High" if risenUp else "Low"
            winAfterPublish = closedata.iloc[-1][targetCol] - closedata.loc[quarter]["Close"]
            pctWinAfterPublish = winAfterPublish / closedata.loc[quarter][targetCol]
            signals.append(pctWinAfterPublish)
        quarterdata["ticker"] = stock
        quarterdata["win"] = wins
        quarterdata["signal"] = signals
        quarterdata = quarterdata.iloc[1:]
        quarterlies.append(quarterdata)
    # merge
    quarterlies = pd.concat(quarterlies, axis=0)
    # drop where all are none
    quarterlies = quarterlies.dropna(how="all", axis=1)
    quarterlies = quarterlies.fillna(0)
    corrs = quarterlies.corr(numeric_only = True)
    corrs["signal"].sort_values(ascending=False)
    
    # grab the highest correlation value
    highest = dict()

    for stock in STOCKS:
        try:
            subset = quarterlies[quarterlies["ticker"] == stock]
            subset = subset.fillna(0)
            corrs = subset.corr()
            corrs = corrs["signal"].sort_values(ascending=False)
            
            # delete nans out of the dict
            corrs = corrs.dropna()
            if "signal" not in list(subset.columns):
                print("didnt get data for stock. will skeip: ", stock)
                continue
            # somehow it happens that signal is still in there...
            corrs = corrs.drop(["signal"])
            
            # get the usual drop or rise
            medchange = subset["win"].median()
            medvariance = subset["win"].std()

            best = {
                corrs.index[0]: round(corrs.iloc[0],2),
                corrs.index[1]: round(corrs.iloc[1],2),
                corrs.index[-2] : round(corrs.iloc[-2],2),
                corrs.index[-1] : round(corrs.iloc[-1],2)
            }
            highest[stock] = {
                "medchange" : round(medchange, 2),
                "medvariance" : round(medvariance, 2),
                "all_changes" : subset["win"].to_list(),
                "best" : best
            }
        except Exception as e:
            logError("update_earning_effect", stock, str(repr(e)))
        
    # with open("earnings_results.json", "w") as f:
    #     json.dump(highest, f, indent=4)
    for ticker, values in highest.items():
        qfeObj = QuarterlyFinancialsEffect(
            ticker = ticker,
            medchange = values["medchange"],
            medvariance =  values["medvariance"],
            all_changes_list = str(values["all_changes"]),
            best = values["best"]
        )
        db.merge(qfeObj)
    db.commit()