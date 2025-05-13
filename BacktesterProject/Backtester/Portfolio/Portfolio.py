import pandas as pd
from ..Strategies.Strategy import StrategyOutputType

class Portfolio:

    # Builder
    def __init__(self, starting_amount):
        self.__cash = starting_amount
        self.__positions = {}
        self.__orders = []
        self.__portfolio_values = pd.Series(dtype=float)
        self.__strategy_type_handlers = {
            StrategyOutputType.REBALANCE: self.__handle_rebalance,
            StrategyOutputType.SIGNAL: self.__handle_trading_signals,
        }

    #####################################################
    ###################### Getters ######################
    #####################################################

    def get_orders(self):
        return pd.DataFrame(self.__orders)
    
    def get_portfolio_values(self):
        return self.__portfolio_values
    
    def get_current_positions(self):
        return self.__positions.copy()
    
    #####################################################
    ####################### Utils #######################
    #####################################################

    def __compute_portfolio_value(self, prices):
        return (pd.Series(self.__positions) * prices).sum()
    
    def __handle_rebalance(self, date, new_portfolio, prices):
        
        # First, we close all the former positions
        self.close_all_positions(prices, date)

        # Then, we build the new portfolio
        new_positions = {}
        total_weight = 0
        orders_to_add = []
        for ticker, trade_instruction in new_portfolio.items():

            if trade_instruction.type != 1:
                raise ValueError("For rebalancing, the strategy must be long only")
            
            new_positions[ticker] = (trade_instruction.weight * self.__cash) / prices[ticker]
            total_weight += trade_instruction.weight
            orders_to_add.append({"Date": date, "Type":"Buy", "Ticker": ticker, "Quantity": new_positions[ticker], "Price": prices[ticker]})
        
        if abs(total_weight - 1) > 1e-6:
            raise ValueError("Weights must sum to 1")
        
        self.__positions = new_positions
        self.__orders.extend(orders_to_add)
        self.__cash = 0

    def __handle_trading_signals(self, date, trading_signals, prices):
        
        for ticker, trade_instruction in trading_signals.items():
            # Selling out of long order
            if trade_instruction.type == 0 and self.__positions.get(ticker, 0) > 0:
                self.__cash += self.__positions[ticker] * prices[ticker]
                self.__orders.append({"Date": date, "Type": "Sell", "Ticker": ticker, "Quantity": self.__positions[ticker], "Price": prices[ticker]})
                self.__positions[ticker] = 0
            
            # Buying out of short order
            elif trade_instruction.type == 0 and self.__positions.get(ticker, 0) < 0:
                self.__cash += self.__positions[ticker] * prices[ticker]
                self.__orders.append({"Date": date, "Type": "Buy", "Ticker": ticker, "Quantity": -self.__positions[ticker], "Price": prices[ticker]})
                self.__positions[ticker] = 0

            # Long order
            elif trade_instruction.type == 1 and self.__positions.get(ticker, 0) == 0:
                quantity = (trade_instruction.weight * self.__cash) / prices[ticker]
                self.__positions[ticker] = quantity
                self.__cash -= quantity * prices[ticker]
                self.__orders.append({"Date": date, "Type": "Buy", "Ticker": ticker, "Quantity": quantity, "Price": prices[ticker]})

            # Short order
            elif trade_instruction.type == -1 and self.__positions.get(ticker, 0) == 0:
                quantity = (trade_instruction.weight * self.__cash) / prices[ticker]
                self.__positions[ticker] = -quantity
                self.__cash += quantity * prices[ticker]
                self.__orders.append({"Date": date, "Type": "Sell", "Ticker": ticker, "Quantity": quantity, "Price": prices[ticker]})
    
    #####################################################
    ##################### Execution #####################
    #####################################################

    def execute_orders(self, strategy_output, prices, date):

        # First, we compute the portfolio value
        self.__portfolio_values.loc[date] = self.__cash + self.__compute_portfolio_value(prices)

        # Then we act depending on the type of strategy_output
        if strategy_output.type is not StrategyOutputType.NONE:
            self.__strategy_type_handlers[strategy_output.type](date, strategy_output.data, prices)

    def close_all_positions(self, prices, date):
        for ticker, curr_position in self.__positions.items():
            if curr_position != 0:
                self.__cash += curr_position * prices[ticker]
                self.__positions[ticker] = 0
                self.__orders.append({"Date": date, "Type":"Buy" if curr_position < 0 else "Sell", "Ticker": ticker, "Quantity": abs(curr_position), "Price": prices[ticker]})


