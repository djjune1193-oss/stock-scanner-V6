import pandas as pd
import numpy as np
from .indicators import calculate_macd, calculate_bollinger_bands, calculate_adx, count_prev_lower_until_higher, classify_candlestick
from scipy.stats import linregress

import pandas as pd
import numpy as np
from scipy.stats import linregress

from .indicators import (
    calculate_macd,
    calculate_adx,
    calculate_bollinger_bands,
    count_prev_lower_until_higher,
    classify_candlestick
)

def build_features(data, tic, meta):

    df = data

    # =========================================================
    # DATE NORMALIZATION (CRITICAL FIX)
    # =========================================================
    if "Date" not in df.columns:
        df = df.reset_index()

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # remove timezone safely (fixes tz-aware vs naive errors)
    if getattr(df["Date"].dt, "tz", None) is not None:
        df["Date"] = df["Date"].dt.tz_localize(None)

    df["Date"] = df["Date"].dt.normalize()

    df.sort_values("Date", inplace=True, kind="mergesort")

    # =========================================================
    # METADATA (no copy)
    # =========================================================
    df["TICKER"] = tic
    df["Sector"] = meta["Sector"]
    df["Industry"] = meta["Industry"]

    # =========================================================
    # OHLCV (already in df, no re-copy from data)
    # =========================================================
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = df[col]

    # =========================================================
    # RETURNS
    # =========================================================
    df["perc_change"] = df["Close"].pct_change() * 100
    df["lower_count"] = count_prev_lower_until_higher(df["Close"], df["Open"])

    # =========================================================
    # MACD
    # =========================================================
    macd = calculate_macd(df, column="Close")
    df = pd.concat([df, macd], axis=1)

    # =========================================================
    # ATR
    # =========================================================
    high_low = df["High"] - df["Low"]
    high_prev_close = (df["High"] - df["Close"].shift(1)).abs()
    low_prev_close = (df["Low"] - df["Close"].shift(1)).abs()

    df["TR"] = pd.concat(
        [high_low, high_prev_close, low_prev_close],
        axis=1
    ).max(axis=1)

    df["ATR"] = df["TR"].ewm(span=21, adjust=False).mean()
    df["ATR_Pct"] = (df["ATR"] / df["Close"]) * 100
    df["Position_Size"] = (75 / df["ATR"]) * 1.5

    # =========================================================
    # MOVING AVERAGES
    # =========================================================
    ma_list = [5, 10, 13, 21, 34, 50, 100, 200]

    for p in ma_list:
        df[f"{p}ma"] = df["Close"].rolling(p).mean()
        df[f"{p}_ma_Bullish"] = (df["Close"] > df[f"{p}ma"]).astype(int)

    # =========================================================
    # ADX
    # =========================================================
    adx = calculate_adx(df, period=14)

    df["ADX"] = adx["ADX"]
    df["PLUS_DI"] = adx["PLUS_DI"]
    df["MINUS_DI"] = adx["MINUS_DI"]

    df["ADX_Strong_Trend"] = (df["ADX"] > 25).astype(int)
    df["ADX_Weak_Trend"] = (df["ADX"] < 20).astype(int)

    df["DI_Bullish"] = (df["PLUS_DI"] > df["MINUS_DI"]).astype(int)
    df["DI_Bearish"] = (df["MINUS_DI"] > df["PLUS_DI"]).astype(int)

    # =========================================================
    # STOCHASTIC
    # =========================================================
    df["pmin"] = df["Low"].rolling(7).min()
    df["pmax"] = df["High"].rolling(7).max()

    df["fast_stoch"] = 100 * (
        (df["Close"] - df["pmin"]) /
        (df["pmax"] - df["pmin"])
    )

    df["k"] = df["fast_stoch"].rolling(4).mean()
    df["d"] = df["k"].rolling(10).mean()

    df["K_slope"] = df["k"].diff()
    df["D_slope"] = df["d"].diff()

    df["opposite_slope"] = (
        ((df["K_slope"] > 0) & (df["D_slope"] < 0)) |
        ((df["K_slope"] < 0) & (df["D_slope"] > 0))
    )

    df["opposite_3days"] = (
        df["opposite_slope"].shift(1).rolling(3).sum() == 3
    )

    df["K_up_today"] = df["K_slope"] > 0
    df["K_down_today"] = df["K_slope"] < 0

    # =========================================================
    # SLOPES (SAFE)
    # =========================================================
    def slope(series, n):
        y = series.iloc[-n:]
        if len(y) < n or y.isna().any():
            return np.nan
        x = np.arange(n)
        return linregress(x, y.values).slope

    for col, n in [
        ("13ma", 5),
        ("21ma", 10),
        ("50ma", 10),
        ("100ma", 10),
        ("k", 5),
        ("d", 5)
    ]:
        df[f"slope_{col}"] = slope(df[col], n)

    # =========================================================
    # BOLLINGER BANDS
    # =========================================================
    bb = calculate_bollinger_bands(df)

    df["SMA"] = bb["SMA"]
    df["Upper"] = bb["Upper"]
    df["Lower"] = bb["Lower"]

    df["delta_upper"] = ((df["Upper"] - df["Close"]) / df["Close"]) * 100

    # =========================================================
    # CANDLE CLASSIFICATION
    # =========================================================
    df["Candle_Type"] = df.apply(
        lambda r: classify_candlestick(r.Open, r.Close, r.High, r.Low),
        axis=1
    )

    # =========================================================
    # OSCILLATOR
    # =========================================================
    df["ROC2"] = df["Close"] - df["Close"].shift(2)
    df["ROC_slope"] = df["ROC2"].diff()

    df["SMA3"] = df["Close"].rolling(3).mean()
    df["SMA10"] = df["Close"].rolling(10).mean()

    df["LBR_fast"] = df["SMA3"] - df["SMA10"]
    df["LBR_slow"] = df["LBR_fast"].rolling(16).mean()

    df["fast_slope"] = df["LBR_fast"].diff()
    df["slow_slope"] = df["LBR_slow"].diff()

    df["sell_day"] = (
        (df["ROC_slope"] > 0) &
        (df["fast_slope"] > 0) &
        (df["slow_slope"] > 0)
    )

    df["buy_day"] = (
        (df["ROC_slope"] < 0) &
        (df["fast_slope"] < 0) &
        (df["slow_slope"] < 0)
    )

    return df
