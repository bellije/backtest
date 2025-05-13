import pytest
import pandas as pd
from Backtester.Portfolio.Portfolio import Portfolio
from Backtester.Strategies.Strategy import StrategyOutput, StrategyOutputType, TradeInstruction

@pytest.fixture
def prices():
    return pd.DataFrame({"AAPL": [100, 110, 90], "MSFT": [200, 180, 210]}, index=pd.date_range("2023-01-01", periods=3))

@pytest.fixture
def portfolio():
    return Portfolio(1000)

def make_signal(ticker, type, weight=1.0):
    return StrategyOutput(StrategyOutputType.SIGNAL, {
        ticker: TradeInstruction(type=type, weight=weight)
    })

def make_rebalance(allocs):
    return StrategyOutput(StrategyOutputType.REBALANCE, {
        ticker: TradeInstruction(type=1, weight=weight)
        for ticker, weight in allocs.items()
    })

def test_long_then_close(portfolio, prices):
    # Long AAPL at 100
    portfolio.execute_orders(make_signal("AAPL", 1), prices.loc["2023-01-01", :], "2023-01-01")
    # Close AAPL at 110
    portfolio.execute_orders(make_signal("AAPL", 0), prices.loc["2023-01-02", :], "2023-01-02")
    assert round(portfolio.get_portfolio_values()["2023-01-02"], 2) == 1100
    assert portfolio.get_current_positions()["AAPL"] == 0

def test_short_then_close(portfolio, prices):
    portfolio.execute_orders(make_signal("AAPL", -1), prices.loc["2023-01-01", :], "2023-01-01")
    portfolio.execute_orders(make_signal("AAPL", 0), prices.loc["2023-01-02", :], "2023-01-02")
    assert round(portfolio.get_portfolio_values()["2023-01-02"], 2) == 900
    assert portfolio.get_current_positions()["AAPL"] == 0

def test_invalid_double_buy_ignored(portfolio, prices):
    portfolio.execute_orders(make_signal("AAPL", 1), prices.loc["2023-01-01", :], "2023-01-01")
    portfolio.execute_orders(make_signal("AAPL", 1), prices.loc["2023-01-02", :], "2023-01-02")  # Ignored
    orders = portfolio.get_orders()
    assert len(orders) == 1
    assert orders.iloc[0]["Price"] == 100

def test_invalid_double_short_ignored(portfolio, prices):
    portfolio.execute_orders(make_signal("AAPL", -1), prices.loc["2023-01-01", :], "2023-01-01")
    portfolio.execute_orders(make_signal("AAPL", -1), prices.loc["2023-01-02", :], "2023-01-02")  # Ignored
    orders = portfolio.get_orders()
    assert len(orders) == 1
    assert orders.iloc[0]["Type"] == "Sell"

def test_rebalance_allocates_correctly(prices):
    p = Portfolio(1000)
    p.execute_orders(make_rebalance({"AAPL": 0.5, "MSFT": 0.5}), prices.loc["2023-01-01", :], "2023-01-01")
    pos = p.get_current_positions()
    assert round(pos["AAPL"] * 100 + pos["MSFT"] * 200, 2) == 1000
    assert round(p.get_portfolio_values()["2023-01-01"], 2) == 1000

def test_close_all_positions_after_rebalance(prices):
    p = Portfolio(1000)
    p.execute_orders(make_rebalance({"AAPL": 0.5, "MSFT": 0.5}), prices.loc["2023-01-01", :], "2023-01-01")
    p.close_all_positions(prices.loc["2023-01-02", :], "2023-01-02")
    assert round(p.get_portfolio_values()["2023-01-01"], 2) == 1000
    assert p.get_current_positions()["AAPL"] == 0
    assert p.get_current_positions()["MSFT"] == 0
    assert round(p.get_orders().iloc[-2]["Price"], 2) == 110  # Sell AAPL
    assert round(p.get_orders().iloc[-1]["Price"], 2) == 180  # Sell MSFT

def test_portfolio_value_updates_correctly(prices):
    p = Portfolio(1000)
    p.execute_orders(make_signal("AAPL", 1), prices.loc["2023-01-01", :], "2023-01-01")
    p.execute_orders(StrategyOutput(StrategyOutputType.NONE, None), prices.loc["2023-01-02", :], "2023-01-02")
    assert round(p.get_portfolio_values()["2023-01-02"], 2) == 1100
