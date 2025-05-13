import pandas as pd

from .Portfolio.Portfolio import Portfolio
from .Strategies.Strategy import Strategy, StrategyOutput

class Backtester:

    def __init__(self, data, init_days):

        if type(data) != pd.DataFrame:
            raise AttributeError("Passed data should be a DataFrame")

        # Making sure the data is correctly indexed
        data = data.sort_index()

        # We split according to user demand
        if init_days >= data.shape[0]:
            raise ValueError("Cannot split the data: Init days is greater than Data length")
        if init_days < 0:
            raise ValueError("Init days must be positive or null")

        self.__init_data = data.iloc[:init_days, :]
        self.__backtest_data = data.iloc[init_days:, :]
        

    def backtest(self, strat: Strategy, initial_amount: int):

        # We ensure that the strat implements our interface
        if not isinstance(strat, Strategy):
            raise TypeError("The given strategy must be an instance of the Strategy class")
        # We ensure that we have data available
        if not ((self.__init_data is not None) and (self.__backtest_data is not None)):
            raise ValueError("The data has not been correctly initialized")
        if initial_amount <= 0:
            raise ValueError("Initial amount must be positive")

        ptf = Portfolio(initial_amount)
        strat.initiate_strategy(self.__init_data)

        # We iterate over all the prices
        for index, prices in self.__backtest_data.iterrows():

            # We pass the current price to the Strategy
            signal = strat.generate_signal(index, prices)

            if not isinstance(signal, StrategyOutput):
                return ValueError("Strategy must return an instance of StrategyOutput") 

            # We treat the order with the closing price
            ptf.execute_orders(signal, prices, index)

        ptf.close_all_positions(prices, index)
        return ptf.get_portfolio_values(), ptf.get_orders()