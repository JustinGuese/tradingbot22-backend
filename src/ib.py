from ib_insync import *


# https://github.com/erdewit/ib_insync
class IBAPI:

    def __init__(self, url = "127.0.0.1", port = 4002, client_id = 11):
        self.ib = IB()
        self.ib.connect('127.0.0.1', 4002, clientId=11)
        
    def getPortfolio(self):
        return self.ib.portfolio()
    
    def getCash(self):
        accvals = [v for v in self.ib.accountValues() if v.tag == 'NetLiquidationByCurrency' and v.currency == 'BASE']
        return float(accvals[0].value) if accvals else 0

    def __createStockContract(self, symbol):
        contract = Stock(symbol, 'SMART', 'USD') # TODO: where base currency
        contractInfo = self.ib.reqContractDetails(contract)[0].__dict__
        return {
            "contract" : contract,
            "minSize" : contractInfo["minSize"],
            "sizeIncrement" : contractInfo["sizeIncrement"],
            "suggestedSizeIncrement" : contractInfo["suggestedSizeIncrement"],
        }
    
    def getContractInfo(self, symbol):
        contractInfo = self.__createStockContract(symbol)
        return contractInfo
    
    def getTrades(self):
        return self.ib.trades()
    
    def getOrders(self):
        return self.ib.orders()
    
    def buyLive(self, symbol, quantity):
        contractInfo = self.__createStockContract(symbol)
        order = MarketOrder("BUY", quantity)
        trade = self.ib.placeOrder(contractInfo["contract"], order)
        return trade
    
    def sellLive(self, symbol, quantity):
        contractInfo = self.__createStockContract(symbol)
        order = MarketOrder("SELL", quantity)
        trade = self.ib.placeOrder(contractInfo["contract"], order)
        return trade
        
    def getOpenTrades(self):
        return self.ib.openTrades()


ibapi = IBAPI()
print(ibapi.getContractInfo("TQQQ"))
print(ibapi.getPortfolio())
print(ibapi.getCash())
print(ibapi.getTrades())
print(ibapi.getOrders())
print("open trades: ", ibapi.getOpenTrades())
# buy
# trade = ibapi.buyLive("TQQQ", 0.1)
# print(trade)