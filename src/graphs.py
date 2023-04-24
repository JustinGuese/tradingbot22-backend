from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from sqlalchemy.orm import Session

from db import PortfolioWorths


async def getCurrentPortfolioGraph(db: Session):
    # just get last two weeks
    # define the start and end timestamps for the two-week period
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=14)
    # query the data from the database
    lastTwoWeeks = db.query(PortfolioWorths) \
                        .filter(PortfolioWorths.timestamp >= start_date) \
                        .order_by(PortfolioWorths.timestamp).all()
                        
    # initialize dictionary to store portfolio worth for each stock over time
    portfolio_worths = {}

    # iterate over data and update portfolio worth dictionary
    for row in lastTwoWeeks:
        timestamp = row.timestamp
        worth = row.worth
        botname = row.bot
        if botname not in portfolio_worths:
            portfolio_worths[botname] = {'timestamps': [], 'worths': []}
        portfolio_worths[botname]['timestamps'].append(timestamp)
        portfolio_worths[botname]['worths'].append(worth)

    # create line chart for portfolio worth for each stock over time
    fig = plt.figure()
    for stock, values in portfolio_worths.items():
        plt.plot(values['timestamps'], values['worths'], label=stock)
    plt.legend()
    # plt.show()
    return fig