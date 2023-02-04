from os import environ

from alpaca.data import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest


class AlpacaInterface:
    def __init__(self):
        self.trading_client = TradingClient(environ["ALPACA_API_KEY"], environ["ALPACA_SECRET"], paper=True)
        self.stock_data_client = StockHistoricalDataClient(environ["ALPACA_API_KEY"], environ["ALPACA_SECRET"])
        self.account = self.trading_client.get_account()
        self.positions_list = []
        self.positions = self.trading_client.get_all_positions()
        self.open_orders_list = []
        self.orders = self.trading_client.get_orders()
        
    def getCash(self) -> float:
        return float(self.account.cash)
    
    def getCurrentPrice(self, ticker) -> float:
        request = StockLatestQuoteRequest(symbol_or_symbols=ticker)
        response = self.stock_data_client.get_stock_latest_quote(request)
        return float(response[ticker].ask_price)
        
    def buyLive(self, ticker, quantity):
            
        market_order_data = MarketOrderRequest(
                    symbol=ticker,
                    qty=quantity,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                    )

        # Market order
        market_order = self.trading_client.submit_order(
                        order_data=market_order_data
                    )
        return market_order
    
    def sellLive(self, ticker, quantity):
        market_order_data = MarketOrderRequest(
                    symbol=ticker,
                    qty=quantity,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY
                    )

        # Market order
        market_order = self.trading_client.submit_order(
                        order_data=market_order_data
                    )
        return market_order
    
    def getOrders(self):
        orders = self.trading_client.get_orders()
        orderinfo = []
        self.open_orders_list = []
        for order in orders:
            orderinfo.append([order.symbol, order.side.value, order.qty, order.status.value, order.submitted_at])
            self.open_orders_list.append(order.symbol)
        return orderinfo
    
    def getPositions(self):
        self.positions = self.trading_client.get_all_positions()
        for pos in self.positions:
            self.positions_list.append(pos.symbol)
        return self.positions
        
if __name__ == "__main__":
    alpaca = AlpacaInterface()
    print(alpaca.getPositions())
    # orders = alpaca.getOrders()
    # print(orders)
    # print(alpaca.getCurrentPrice("TQQQ"))
    # print(alpaca.buyLive("TQQQ", 1))