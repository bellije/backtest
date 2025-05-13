from .Strategy import Strategy, StrategyOutput, StrategyOutputType, TradeInstruction

class RSIStrat(Strategy):

    def __init__(self, number_days, buy_limit, sell_limit):
        self.__period = number_days
        self.__buy_limit = buy_limit
        self.__sell_limit = sell_limit
        self.RSIs = {"Date":[], "RSI": []}

    def initiate_strategy(self, data):
            diffs = data.iloc[-(self.__period + 1):].diff().iloc[1:]
            self.__avg_gain = diffs.where(diffs > 0, 0).mean()
            self.__avg_loss = -diffs.where(diffs < 0, 0).mean()
            self.__last_prices = data.iloc[-1]

    def generate_signal(self, date, prices):

        last_change = (prices - self.__last_prices)
        self.__avg_gain = ((self.__avg_gain*(self.__period - 1)) + last_change.clip(lower=0))/self.__period
        self.__avg_loss = ((self.__avg_loss*(self.__period - 1)) - last_change.clip(upper=0))/self.__period

        RS = self.__avg_gain/self.__avg_loss
        if any(self.__avg_loss == 0):
            RS.loc[self.__avg_loss == 0] = 100

        RSI = 100 - (100/(1+RS))
        prev_RSI = self.RSIs["RSI"][-1] if len(self.RSIs["RSI"]) else RSI
        self.RSIs["Date"].append(date)
        self.RSIs["RSI"].append(RSI)

        # We update the last price
        self.__last_prices = prices

        # For each existing ticker, we create the signals
        for ticker, curr_rsi in RSI.items():
            if curr_rsi < self.__buy_limit:
                return StrategyOutput(StrategyOutputType.SIGNAL, {ticker: TradeInstruction(1, 1/len(prices))})

            if (prev_RSI[ticker] < 50 and curr_rsi > 50) or (prev_RSI[ticker] > 50 and curr_rsi < 50):
                return StrategyOutput(StrategyOutputType.SIGNAL, {ticker: TradeInstruction(0)})

            if curr_rsi > self.__sell_limit:
                return StrategyOutput(StrategyOutputType.SIGNAL, {ticker: TradeInstruction(-1, 1/len(prices))})
        
        return StrategyOutput(StrategyOutputType.NONE, None)