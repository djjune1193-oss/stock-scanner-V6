import pandas as pd
from pathlib import Path


def scan_recent_20day_low_reversal():

    # Base directory
    BASE_DIR = Path(__file__).resolve().parents[3]

    # Input data
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    # Read full history
    df = pd.read_parquet(data_path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["TICKER", "Date"])

    # 20-day rolling low
    df["rolling_20_low"] = (
        df.groupby("TICKER")["Low"]
        .transform(lambda x: x.rolling(20, min_periods=20).min())
    )

    df["is_20_low"] = df["Low"] <= df["rolling_20_low"]

    # Previous 20-day low date
    df["prev_low_date"] = (
        df["Date"]
        .where(df["is_20_low"])
        .groupby(df["TICKER"])
        .shift(1)
    )

    df["days_since_prev_low"] = (df["Date"] - df["prev_low_date"]).dt.days

    # Next day close (today)
    df["next_close"] = df.groupby("TICKER")["Close"].shift(-1)

    df["bullish_follow"] = df["next_close"] > df["Close"]

    # --- identify today and yesterday ---
    today = df["Date"].max()
    yesterday = today - pd.Timedelta(days=1)

    # Apply conditions (yesterday signal confirmed today)
    result = df[
        (df["Date"] == yesterday) &
        (df["is_20_low"]) &
        (df["days_since_prev_low"] >= 4) &
        (df["bullish_follow"])
    ]

    return result[[
        "Date",
        "TICKER",
        "Close",
        "Low",
        "days_since_prev_low"
    ]]







