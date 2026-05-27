from datetime import datetime, date
import pandas as pd
import yfinance as yf
from datetime import timedelta

def get_historical_stock_data(ticker_symbol, start_date=None, end_date=None, interval="1d"):
    today = pd.Timestamp.today().date()
    lookback_days = 3

    if start_date is None:
        start_date = today - timedelta(days=lookback_days)
    if end_date is None:
        end_date = today + timedelta(days=1)

    # Convert to string for yfinance

    ticker = yf.Ticker(ticker_symbol)
    try:
        df = ticker.history(start=start_date, end=end_date, interval=interval)
        if df.empty:
            print(f"No data found for {ticker_symbol}")
            return None
        return df
    except Exception as e:
        print(f"Error fetching {ticker_symbol}: {e}")
        return None
