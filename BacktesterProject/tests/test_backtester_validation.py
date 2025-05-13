import pytest
import pandas as pd
from datetime import datetime

from Backtester.Backtester import Backtester
from Backtester.Strategies.Strategy import Strategy


# -------- FIXTURES ----------

@pytest.fixture
def correct_price_data():
    """Simple price DataFrame with datetime index and valid format"""
    return pd.DataFrame({
        "AAPL": [100, 101, 102, 103],
        "MSFT": [200, 202, 204, 206]
    }, index=pd.date_range(start="2024-01-01", periods=4, freq="D"))


@pytest.fixture
def dummy_strategy():
    class DummyStrategy(Strategy):
        def initiate_strategy(self, data):
            pass

        def generate_signal(self, current_date, price_row):
            return None
    return DummyStrategy()


# -------- TESTS SUR L’INITIALISATION ----------

def test_backtester_data_none_raises():
    with pytest.raises(AttributeError):
        Backtester(None, init_days=2)


def test_backtester_data_not_dataframe():
    with pytest.raises(AttributeError):
        Backtester("not a DataFrame", init_days=2)


def test_backtester_data_too_short():
    df = pd.DataFrame({"AAPL": [100]}, index=pd.date_range("2024-01-01", periods=1))
    with pytest.raises(ValueError):
        Backtester(df, init_days=2)


def test_backtester_invalid_init_days(correct_price_data):
    with pytest.raises(ValueError):
        Backtester(correct_price_data, init_days=-1)

    with pytest.raises(ValueError):
        Backtester(correct_price_data, init_days=100)  # Too large


# -------- TESTS SUR LE BACKTEST ----------

def test_backtest_invalid_strategy_type(correct_price_data):
    bt = Backtester(correct_price_data, init_days=2)
    with pytest.raises(TypeError):
        bt.backtest(strat="not a strategy", initial_amount=1000)


def test_backtest_invalid_initial_amount_type(correct_price_data, dummy_strategy):
    bt = Backtester(correct_price_data, init_days=2)
    with pytest.raises(TypeError):
        bt.backtest(strat=dummy_strategy, initial_amount="a lot of money")

    with pytest.raises(ValueError):
        bt.backtest(strat=dummy_strategy, initial_amount=-500)


def test_backtest_missing_data_attribute(dummy_strategy):
    # Patch the backtester to simulate bad internal state
    from Backtester.Backtester import Backtester as RealBacktester
    bt = RealBacktester.__new__(RealBacktester)
    bt._Backtester__init_data = None
    bt._Backtester__backtest_data = None
    with pytest.raises(ValueError):
        bt.backtest(strat=dummy_strategy, initial_amount=1000)
