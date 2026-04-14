import pandas as pd

def calculate_macd(df, column="Close", fast=12, slow=26, signal=9):
    macd = pd.DataFrame(index=df.index)

    macd["EMA_fast"] = df[column].ewm(span=fast, adjust=False).mean()
    macd["EMA_slow"] = df[column].ewm(span=slow, adjust=False).mean()
    macd["MACD"] = macd["EMA_fast"] - macd["EMA_slow"]
    macd["Signal"] = macd["MACD"].ewm(span=signal, adjust=False).mean()
    macd["Histogram"] = macd["MACD"] - macd["Signal"]

    return macd


def calculate_bollinger_bands(df, period=20, std=2):
    bb = pd.DataFrame(index=df.index)

    bb["SMA"] = df["Close"].rolling(period).mean()
    bb["STD"] = df["Close"].rolling(period).std()
    bb["Upper"] = bb["SMA"] + std * bb["STD"]
    bb["Lower"] = bb["SMA"] - std * bb["STD"]

    return bb


import numpy as np

def calculate_adx(df, period=14):
    """
    Calculate ADX, +DI, -DI using Wilder's smoothing.
    Requires columns: High, Low, Close
    """

    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    # Directional movement
    plus_dm = high.diff()
    minus_dm = low.diff().abs()

    plus_dm = np.where(
        (plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0.0
    )
    minus_dm = np.where(
        (minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0.0
    )

    # True range
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Wilder smoothing
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean() / atr

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.ewm(alpha=1/period, adjust=False).mean()

    return pd.DataFrame({
        "ADX": adx,
        "PLUS_DI": plus_di,
        "MINUS_DI": minus_di
    })


def count_prev_lower_until_higher(close_series, open_series):
    counts = []

    for i in range(len(close_series)):
        current_close = close_series.iloc[i]
        count = 0

        # walk backwards
        for j in range(i - 1, -1, -1):
            prev_close = close_series.iloc[j]
            prev_open = open_series.iloc[j]

            # STOP if either Open OR Close is higher than current Close
            if (prev_close > current_close) or (prev_open > current_close):
                break

            count += 1

        counts.append(count)

    return pd.Series(counts, index=close_series.index)




def classify_candlestick(open_price, close_price, high_price, low_price, body_tolerance=0.01, wick_ratio_tolerance=0.1):
    """
    Classifies a single day's candlestick based on OHLC prices.
    
    Args:
        open_price (float): The opening price.
        close_price (float): The closing price.
        high_price (float): The highest price reached.
        low_price (float): The lowest price reached.
        body_tolerance (float): Percentage threshold to define a small body (e.g., 1% of the day's range).
        wick_ratio_tolerance (float): Ratio threshold to classify a Doji (e.g., body must be less than 10% of total range).
        
    Returns:
        str: The classified candlestick pattern name.
    """
    
    # Calculate key metrics
    price_range = high_price - low_price
    
    # Handle zero range to prevent division by zero (occurs in extremely low liquidity)
    if price_range == 0:
        return "No Movement (Zero Range)"
        
    body_size = abs(close_price - open_price)
    
    # Determine Color/Direction
    is_bullish = close_price > open_price
    
    # Calculate Wicks
    if is_bullish:
        upper_wick = high_price - close_price
        lower_wick = open_price - low_price
    else: # Bearish or Neutral (Close <= Open)
        upper_wick = high_price - open_price
        lower_wick = close_price - low_price

    # --- 1. Indecision/Neutral Patterns (Doji/Spinning Top) ---
    
    # Doji: Body is extremely small relative to the total range
    if body_size / price_range < wick_ratio_tolerance:
        # Check specific types of Doji
        if upper_wick / price_range < 0.1 and lower_wick / price_range < 0.1:
             return "Doji (Classic/Four Price)"
        elif lower_wick / price_range < 0.1 and upper_wick > 0.5 * price_range:
            return "Gravestone Doji" # Bearish reversal
        elif upper_wick / price_range < 0.1 and lower_wick > 0.5 * price_range:
            return "Dragonfly Doji" # Bullish reversal
        else:
            return "Long-Legged Doji" # High volatility indecision

    # Spinning Top/Bottom: Small body but larger than a Doji
    if body_size / price_range < body_tolerance:
        return "Spinning Top/Bottom" # Indecision with moderate wicks

    # --- 2. Strong Trend Patterns (Marubozu) ---

    # Threshold for body to be considered "full" (low/high are very close to open/close)
    is_marubozu = (lower_wick / price_range < wick_ratio_tolerance) and (upper_wick / price_range < wick_ratio_tolerance)

    if is_marubozu:
        if is_bullish:
            return "Bullish Marubozu (Strong Buy)" # Close == High, Open == Low
        else:
            return "Bearish Marubozu (Strong Sell)" # Open == High, Close == Low

    # --- 3. Mid-Range Patterns (Hammers, Shaven, etc.) ---

    # Hammer/Hanging Man: Small body, one wick is very long
    if body_size < (price_range / 5): # Small body threshold
        if lower_wick > 2 * body_size and upper_wick < body_size:
            # Lower wick is long, upper wick is short
            if is_bullish:
                return "Bullish Hammer" # Bullish Reversal
            else:
                return "Hanging Man" # Bearish Reversal
        elif upper_wick > 2 * body_size and lower_wick < body_size:
            # Upper wick is long, lower wick is short
            if is_bullish:
                return "Inverted Hammer" # Bullish Reversal
            else:
                return "Shooting Star" # Bearish Reversal
                
    # Basic Bullish/Bearish Candle (Default for everything else)
    if is_bullish:
        return "Standard Bullish Candle"
    else:
        return "Standard Bearish Candle"
