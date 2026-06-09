import pandas as pd
from pathlib import Path
from django.conf import settings
from datetime import timedelta


import pandas as pd
import yfinance as yf

from pathlib import Path
import pandas as pd


def get_prev_close_from_parquet(ticker):

    BASE_DIR = Path(__file__).resolve().parents[1]
    data_path = BASE_DIR / "data" / "all_data.parquet"

    df = pd.read_parquet(data_path)

    df = df[df["TICKER"] == ticker].copy()

    if df.empty:
        return None

    df["Date"] = pd.to_datetime(df["Date"])

    latest_row = (
        df.sort_values("Date")
          .tail(1)
    )

    return float(latest_row["Close"].iloc[0])


def premarket_gap_tracker(ticker):

    # -----------------------------
    # 1. Previous Close
    # -----------------------------
    prev_close = get_prev_close_from_parquet(ticker)

    if prev_close is None:
        return None

    # -----------------------------
    # 2. Today's Premarket
    # -----------------------------
    df = yf.download(
        ticker,
        period="1d",
        interval="1h",
        prepost=True,
        progress=False,
        auto_adjust=False
    )

    if df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.index = df.index.tz_convert("US/Eastern")

    today = pd.Timestamp.now(tz="US/Eastern").date()

    premarket = df.between_time("04:00", "09:29")
    premarket = premarket[premarket.index.date == today]

    if premarket.empty:
        return None

    last_price = float(premarket["Close"].iloc[-1])
    high_price = float(premarket["High"].max())
    low_price = float(premarket["Low"].min())

    gap_now = (last_price - prev_close) / prev_close * 100
    gap_high = (high_price - prev_close) / prev_close * 100
    gap_low = (low_price - prev_close) / prev_close * 100

    return {
        "TICKER": ticker,
        "Prev_Close": round(prev_close, 2),
        "PM_Last": round(last_price, 2),
        "PM_High": round(high_price, 2),
        "PM_Low": round(low_price, 2),
        "Gap_Now_%": round(gap_now, 2),
        "Gap_High_%": round(gap_high, 2),
        "Gap_Low_%": round(gap_low, 2),
    }


def run_premarket_scan():

    # -----------------------------
    # Paths
    # -----------------------------
    BASE_DIR = Path(__file__).resolve().parent.parent
    csv_path = BASE_DIR / "ALL_STOCK_LIST.csv"
    output_path = settings.DATA_DIR / "premarket_scan.parquet"

    # -----------------------------
    # Load tickers
    # -----------------------------
    df = pd.read_csv(csv_path)

    tickers = (
        df["Ticker"]
        .dropna()
        .astype(str)
        .str.upper()
        .unique()
        .tolist()
    )
    results = []

    # -----------------------------
    # Loop tickers
    # -----------------------------
    for i, ticker in enumerate(tickers):

        print(ticker)

        try:
            res = premarket_gap_tracker(ticker)
            print(res)

            if res is not None:
                results.append(res)

        except Exception as e:
            print(f"{ticker} ❌ {e}")
            continue


    # -----------------------------
    # Save parquet
    # -----------------------------
    out_df = pd.DataFrame(results)

    if not out_df.empty:
        out_df["Abs_Gap"] = out_df["Gap_Now_%"].abs()
        out_df = out_df.sort_values("Abs_Gap", ascending=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(output_path, index=False)

    print("Saved:", output_path)

    return out_df
