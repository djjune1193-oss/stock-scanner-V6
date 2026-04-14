import pandas as pd
import numpy as np
from .indicators import calculate_macd, calculate_bollinger_bands, calculate_adx, count_prev_lower_until_higher, classify_candlestick
from scipy.stats import linregress

def build_features(data, tic, meta):



    # 1️Base dataframe (index-first, meta-first)

    
    df = pd.DataFrame(index=data.index)
    df["Date"] = df.index.date
    df["TICKER"] = tic
    df["Sector"] = meta["Sector"]
    df["Industry"] = meta["Industry"]
   



    # 2️Attach OHLCV
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = data[col]

    df['perc_change'] = ((df['Close'] - df['Close'].shift(1))/df['Close'].shift(1))*100
    df["lower_count"] = count_prev_lower_until_higher(df["Close"],df["Open"])

    # =========================================================
    # 3️MACD (ADD columns, do NOT create DF from it)
    # =========================================================
    macd = calculate_macd(data, column="Close")

    for col in macd.columns:
        df[col] = macd[col]

 

    # =========================================================
    # 4️ATR
    # =========================================================
    high_low = df["High"] - df["Low"]
    high_prev_close = (df["High"] - df["Close"].shift(1)).abs()
    low_prev_close = (df["Low"] - df["Close"].shift(1)).abs()

    df["TR"] = pd.concat(
        [high_low, high_prev_close, low_prev_close], axis=1
    ).max(axis=1)

    df["ATR"] = df["TR"].ewm(span=21, adjust=False).mean()
    df['ATR_Pct'] = (df['ATR'] / df['Close'])*100
    df["Position_Size"] = 75 / df["ATR"] * 1.5

    # =========================================================
    # 5️Moving averages
    # =========================================================
    for p in [5, 10, 13, 21, 34, 50, 100, 200]:
        df[f"{p}ma"] = df["Close"].rolling(p).mean()
        df[f"{p}_ma_Bullish"] = (df["Close"] > df[f"{p}ma"]).astype(int)



    # =========================================================
    #  ADX
    # =========================================================
    adx_df = calculate_adx(df, period=14)

    df["ADX"] = adx_df["ADX"]
    df["PLUS_DI"] = adx_df["PLUS_DI"]
    df["MINUS_DI"] = adx_df["MINUS_DI"]

    # Trend regime helpers (very useful for scanners)
    df["ADX_Strong_Trend"] = (df["ADX"] > 25).astype(int)
    df["ADX_Weak_Trend"] = (df["ADX"] < 20).astype(int)

    df["DI_Bullish"] = (df["PLUS_DI"] > df["MINUS_DI"]).astype(int)
    df["DI_Bearish"] = (df["MINUS_DI"] > df["PLUS_DI"]).astype(int)


    
    # =========================================================
    # ️STOCHASTIC (same as your original)
    # =========================================================
    df["pmin"] = df["Low"].rolling(7).min()
    df["pmax"] = df["High"].rolling(7).max()

    df["fast_stoch"] = 100 * (
        (df["Close"] - df["pmin"]) / (df["pmax"] - df["pmin"])
    )

    df["k"] = df["fast_stoch"].rolling(4).mean()
    df["d"] = df["k"].rolling(10).mean()

    
    df["K_slope"] = df["k"].diff()
    df["D_slope"] = df["d"].diff()

    # Opposing slope condition
    df["opposite_slope"] = (
            ((df["K_slope"] > 0) & (df["D_slope"] < 0)) |
            ((df["K_slope"] < 0) & (df["D_slope"] > 0))
    )

    # Last 3 days (before today) must have opposing slopes
    df["opposite_3days"] = (df["opposite_slope"].shift(1).rolling(3).sum() == 3)

    # %K turns up today
    df["K_up_today"] = df["K_slope"] > 0



    

    # =========================================================
    # ️Slopes (utility)
    # =========================================================
    def slope(series, n):
        y = series.iloc[-n:]
        if len(y) < n or y.isna().any():
            return np.nan
        x = np.arange(len(y))
        return linregress(x, y.values).slope

    df["slope_13"] = slope(df["13ma"], 5)
    df["slope_21"] = slope(df["21ma"], 10)
    df["slope_50"] = slope(df["50ma"], 10)
    df["slope_100"] = slope(df["100ma"], 10)
    df["slope_k"] = slope(df["k"], 5)
    df["slope_d"] = slope(df["d"], 5)

    # =========================================================
    # ️Bollinger Bands
    # =========================================================
    bb = calculate_bollinger_bands(data)

    df["SMA"] = bb["SMA"]
    df["Upper"] = bb["Upper"]
    df["Lower"] = bb["Lower"]

    df["slope_Upper"] = slope(df["Upper"], 5)
    df["slope_Lower"] = slope(df["Lower"], 5)


    df["delta_upper"] = ((df["Upper"] - df["Close"])/ df["Close"])*100

    # =========================================================
    # Candlestick classification
    # =========================================================
    df["Candle_Type"] = df.apply(
        lambda r: classify_candlestick(
            r.Open, r.Close, r.High, r.Low
        ),
        axis=1
    )

    
    # -----------------------------
    # OSCILLATOR
    # -----------------------------
    df["ROC2"] = df["Close"] - df["Close"].shift(2)
    df["ROC_slope"] = df["ROC2"].diff()

    df["SMA3"] = df["Close"].rolling(3).mean()
    df["SMA10"] = df["Close"].rolling(10).mean()

    df["LBR_fast"] = df["SMA3"] - df["SMA10"]
    df["LBR_slow"] = df["LBR_fast"].rolling(16).mean()

    df["fast_slope"] = df["LBR_fast"].diff()
    df["slow_slope"] = df["LBR_slow"].diff()

    # Signals
    df["buy_day"] = (
        (df["ROC_slope"] > 0) &
        (df["fast_slope"] > 0) &
        (df["slow_slope"] > 0)
    )

    df["sell_day"] = (
        (df["ROC_slope"] < 0) &
        (df["fast_slope"] < 0) &
        (df["slow_slope"] < 0)
    )


    
   
    return df

