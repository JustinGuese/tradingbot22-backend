import yfinance as yf
from sqlalchemy.orm import Session

from db import EarningDates, QuarterlyFinancials


def createTicker(ticker: str) -> yf.Ticker:
    return yf.Ticker(ticker)

def writeEarningsDates(tickerobj: yf.Ticker, ticker: str, db: Session):
    calendar = tickerobj.calendar
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