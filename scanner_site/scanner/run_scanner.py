import pandas as pd
from pathlib import Path
from django.conf import settings
from .fetch_data import get_historical_stock_data
from .features import build_features

# -----------------------------
# PATHS
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
csv_path = BASE_DIR / "ALL_STOCK_LIST.csv"

DATA_DIR = settings.DATA_DIR
DATA_DIR.mkdir(parents=True, exist_ok=True)




def build_equity_ranking(df):

    df = df.copy()

    df["Date"] = pd.to_datetime(df["Date"])

    df = df.sort_values(
        ["TICKER", "Date"]
    )

    # =====================================
    # RETURNS
    # =====================================

    df["Return"] = (
        df.groupby("TICKER")["Close"]
        .pct_change()
    )

    spy = (
        df[df["TICKER"] == "^GSPC"][["Date", "Return"]]
        .rename(columns={
            "Return": "SPY_Return"
        })
    )

    df = df.merge(
        spy,
        on="Date",
        how="left"
    )

    # =====================================
    # DAILY RELATIVE STRENGTH
    # =====================================

    df["RS_Daily"] = (
        df["Return"] -
        df["SPY_Return"]
    )

    rmse = np.sqrt(
        np.mean(df["RS_Daily"] ** 2)
    )

    df["RS_Normalized"] = (
        df["RS_Daily"] / rmse
    )

    # =====================================
    # MULTI-TIMEFRAME RS
    # =====================================

    for period in [7, 21, 50, 100, 200]:

        df[f"RS_{period}"] = (
            df.groupby("TICKER")["RS_Normalized"]
            .transform(
                lambda x:
                x.rolling(period).mean()
            )
        )

    # =====================================
    # CUMULATIVE SCORE
    # =====================================

    df["Cumulative_Return"] = (
        df.groupby("TICKER")["RS_Normalized"]
        .cumsum()
    )

    # =====================================
    # LATEST SNAPSHOT
    # =====================================

    latest_date = df["Date"].max()

    latest_df = df[
        df["Date"] == latest_date
    ].copy()

    # =====================================
    # FINAL RS SCORE
    # =====================================

    latest_df["RS_SCORE"] = (
        0.30 * latest_df["RS_7"] +
        0.25 * latest_df["RS_21"] +
        0.20 * latest_df["RS_50"] +
        0.15 * latest_df["RS_100"] +
        0.10 * latest_df["RS_200"]
    )

    latest_df = latest_df.dropna(
        subset=[
            "RS_SCORE",
            "RS_7",
            "RS_21",
            "RS_50",
            "RS_100",
            "RS_200"
        ]
    )

    # =====================================
    # FINAL SORT DEFAULT
    # =====================================

    latest_df = latest_df.sort_values(
        "Cumulative_Return",
        ascending=False
    )

    return df, latest_df



# =========================================================
# BUILD FIB RETRACEMENT DATA
# =========================================================

def build_fib_retracement_data(df):

    df = df.copy()

    # =====================================================
    # CLEANING
    # =====================================================

    df["Date"] = pd.to_datetime(
        df["Date"]
    )

    df = df.sort_values(
        ["TICKER", "Date"]
    )

    # =====================================================
    # HIGH / LOW PER TICKER
    # =====================================================

    df["high_max"] = (
        df.groupby("TICKER")["High"]
        .transform("max")
    )

    df["low_min"] = (
        df.groupby("TICKER")["Low"]
        .transform("min")
    )

    # =====================================================
    # SAFE DENOMINATOR
    # =====================================================

    diff = (
        df["high_max"] - df["low_min"]
    ).replace(0, 1)

    # =====================================================
    # RETRACEMENT %
    # =====================================================

    df["retracement"] = (
        (df["high_max"] - df["Close"]) / diff
    ) * 100

    # =====================================================
    # FIB LEVELS
    # =====================================================

    df["fib_0"] = df["high_max"]

    df["fib_236"] = (
        df["high_max"] - 0.236 * diff
    )

    df["fib_382"] = (
        df["high_max"] - 0.382 * diff
    )

    df["fib_50"] = (
        df["high_max"] - 0.5 * diff
    )

    df["fib_618"] = (
        df["high_max"] - 0.618 * diff
    )

    # =====================================================
    # LATEST SNAPSHOT
    # =====================================================

    latest_df = (
        df.sort_values("Date")
        .groupby("TICKER")
        .tail(1)
        .copy()
    )

    # =====================================================
    # FINAL TABLE
    # =====================================================

    latest_df = latest_df[[
        "TICKER",
        "Close",
        "high_max",
        "low_min",
        "retracement",
        "fib_236",
        "fib_382",
        "fib_50",
        "fib_618"
    ]].copy()

    latest_df["tv_link"] = (
        "https://www.tradingview.com/chart/?symbol="
        + latest_df["TICKER"]
    )

    latest_df = latest_df.round(2)

    latest_df = latest_df.sort_values(
        "retracement",
        ascending=True
    )

    return df, latest_df


import numpy as np
import pandas as pd

def build_turtle_soup_signals(df):

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["TICKER", "Date"])

    # =========================
    # STOCH
    # =========================

    df["pmin"] = df.groupby("TICKER")["Low"].transform(lambda x: x.rolling(7).min())
    df["pmax"] = df.groupby("TICKER")["High"].transform(lambda x: x.rolling(7).max())

    df["fast_stoch"] = 100 * ((df["Close"] - df["pmin"]) / (df["pmax"] - df["pmin"]))
    df["k"] = df.groupby("TICKER")["fast_stoch"].transform(lambda x: x.rolling(4).mean())
    df["d"] = df.groupby("TICKER")["k"].transform(lambda x: x.rolling(10).mean())

    df["K_slope"] = df.groupby("TICKER")["k"].diff()
    df["D_slope"] = df.groupby("TICKER")["d"].diff()

    # =========================
    # CORE LOGIC
    # =========================

    df["opposite_slope"] = (
        ((df["K_slope"] > 0) & (df["D_slope"] < 0)) |
        ((df["K_slope"] < 0) & (df["D_slope"] > 0))
    )

    df["opposite_3days"] = df.groupby("TICKER")["opposite_slope"].transform(
        lambda x: x.shift(1).rolling(3).sum() == 3
    )

    df["K_up_today"] = df["K_slope"] > 0
    df["K_down_yesterday"] = df.groupby("TICKER")["K_slope"].shift(1) < 0

    latest_date = df["Date"].max()
    today_df = df[df["Date"] == latest_date].copy()

    signal_df = today_df[
        (today_df["opposite_3days"]) &
        (today_df["K_up_today"]) &
        (today_df["K_down_yesterday"]) &
        (today_df["D_slope"] > 0)
    ].copy()

    return df, signal_df


def build_stochastic_short_signals(df):

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["TICKER", "Date"])

    df["pmin"] = df.groupby("TICKER")["Low"].transform(lambda x: x.rolling(7).min())
    df["pmax"] = df.groupby("TICKER")["High"].transform(lambda x: x.rolling(7).max())

    df["fast_stoch"] = 100 * ((df["Close"] - df["pmin"]) / (df["pmax"] - df["pmin"]))
    df["k"] = df.groupby("TICKER")["fast_stoch"].transform(lambda x: x.rolling(4).mean())
    df["d"] = df.groupby("TICKER")["k"].transform(lambda x: x.rolling(10).mean())

    df["K_slope"] = df.groupby("TICKER")["k"].diff()
    df["D_slope"] = df.groupby("TICKER")["d"].diff()

    df["opposite_slope"] = (
        ((df["K_slope"] > 0) & (df["D_slope"] < 0)) |
        ((df["K_slope"] < 0) & (df["D_slope"] > 0))
    )

    df["opposite_3days"] = df.groupby("TICKER")["opposite_slope"].transform(
        lambda x: x.shift(1).rolling(3).sum() == 3
    )

    df["K_up_today"] = df["K_slope"] > 0
    df["K_down_yesterday"] = df.groupby("TICKER")["K_slope"].shift(1) < 0

    latest_date = df["Date"].max()
    today_df = df[df["Date"] == latest_date].copy()

    signal_df = today_df[
        (today_df["opposite_3days"]) &
        (~today_df["K_up_today"]) &
        (~today_df["K_down_yesterday"]) &
        (today_df["D_slope"] < 0)
    ].copy()

    return df, signal_df


def build_keltner_data(df):

    df = df.copy()

    df["prev_close"] = df.groupby("TICKER")["Close"].shift(1)

    # =============================
    # TRUE RANGE
    # =============================

    df["tr"] = np.maximum.reduce([
        df["High"] - df["Low"],
        abs(df["High"] - df["prev_close"]),
        abs(df["Low"] - df["prev_close"])
    ])

    # =============================
    # EMA + ATR
    # =============================

    df["ema20"] = (
        df.groupby("TICKER")["Close"]
        .transform(lambda x: x.ewm(span=20, adjust=False).mean())
    )

    df["atr20"] = (
        df.groupby("TICKER")["tr"]
        .transform(lambda x: x.ewm(alpha=1/20, adjust=False).mean())
    )

    # =============================
    # KELTNER CHANNELS
    # =============================

    df["kc_upper"] = df["ema20"] + 2.5 * df["atr20"]
    df["kc_lower"] = df["ema20"] - 2.5 * df["atr20"]

    # =============================
    # METRICS
    # =============================

    df["pct_above_ema"] = (
        (df["Close"] - df["ema20"]) / df["ema20"]
    ) * 100

    df["atr_pct"] = (
        df["atr20"] / df["Close"]
    ) * 100

    # =============================
    # DAYS ABOVE EMA
    # =============================

    days_col = []

    for ticker, g in df.groupby("TICKER"):

        count = 0

        for _, row in g.iterrows():

            if row["Close"] > row["ema20"]:
                count += 1
            else:
                count = 0

            days_col.append(count)

    df["days_above_ema"] = days_col

    return df


def build_ma_structure(df):

    df = df.copy()

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["TICKER", "Date"])

    # =========================
    # MOVING AVERAGES
    # =========================
    for ma in [10, 21, 34, 50, 100, 200]:
        df[f"MA_{ma}"] = df.groupby("TICKER")["Close"].transform(
            lambda x: x.rolling(ma).mean()
        )

    # =========================
    # CLASSIFIER
    # =========================
    def classify(row):

        ma10 = row["MA_10"]
        ma21 = row["MA_21"]
        ma34 = row["MA_34"]
        ma50 = row["MA_50"]
        ma100 = row["MA_100"]
        ma200 = row["MA_200"]

        if ma10 < ma200:
            return "MA10 < 200", ma200, "MA200"

        if ma10 < ma100:
            return "MA10: 100-200", ma200, "MA200"

        if ma10 < ma50:
            return "MA10: 50-100", ma100, "MA100"

        if ma10 < ma34:
            return "MA10: 34-50", ma50, "MA50"

        if ma10 < ma21:
            return "MA10: 21-34", ma34, "MA34"

        if ma10 >= ma21:
            if ma10 > ma21 > ma34 > ma50 > ma100 > ma200:
                return "MA10 > ALL (strong)", ma10, "MA10"
            return "MA10 > ALL (weak)", ma10, "MA10"

        return "MA10 < 200", ma200, "MA200"

    # =========================
    # APPLY CLASSIFICATION
    # =========================
    latest_date = df["Date"].max()

    latest_df = df[df["Date"] == latest_date].copy()
    prev_df = df[df["Date"] < latest_date].groupby("TICKER").tail(1).copy()

    latest_df[["group", "base_value", "base_label"]] = latest_df.apply(
        lambda r: pd.Series(classify(r)),
        axis=1
    )

    if not prev_df.empty:
        prev_df[["group", "_", "__"]] = prev_df.apply(
            lambda r: pd.Series(classify(r)),
            axis=1
        )

        prev_map = prev_df[["TICKER", "group"]].rename(columns={"group": "prev_group"})
        latest_df = latest_df.merge(prev_map, on="TICKER", how="left")
    else:
        latest_df["prev_group"] = latest_df["group"]

    latest_df["prev_group"] = latest_df["prev_group"].fillna(latest_df["group"])

    # =========================
    # RANK SYSTEM
    # =========================
    rank = {
        "MA10 > ALL (strong)": 7,
        "MA10 > ALL (weak)": 6,
        "MA10: 21-34": 5,
        "MA10: 34-50": 4,
        "MA10: 50-100": 3,
        "MA10: 100-200": 2,
        "MA10 < 200": 1
    }

    def movement(row):
        if row["group"] == row["prev_group"]:
            return ""
        return "⬆" if rank[row["group"]] > rank[row["prev_group"]] else "⬇"

    latest_df["move"] = latest_df.apply(movement, axis=1)

    # =========================
    # DISTANCE
    # =========================
    latest_df["pct_distance"] = (
        (latest_df["Close"] - latest_df["base_value"]) / latest_df["base_value"]
    ) * 100

    # =========================
    # SORTING
    # =========================
    group_order = {
        "MA10 > ALL (strong)": 0,
        "MA10 > ALL (weak)": 1,
        "MA10: 21-34": 2,
        "MA10: 34-50": 3,
        "MA10: 50-100": 4,
        "MA10: 100-200": 5,
        "MA10 < 200": 6
    }

    latest_df["group_rank"] = latest_df["group"].map(group_order)

    latest_df = latest_df.sort_values(
        ["group_rank", "pct_distance"],
        ascending=[True, False]
    )

    return df, latest_df

# =========================================================
# 21 DAY BREAKOUT SCANNER
# =========================================================

def build_breakout_21_signals(df):

    df = df.copy()

    # =========================================
    # CLEAN
    # =========================================

    df["Date"] = pd.to_datetime(df["Date"])

    df = df.sort_values(
        ["TICKER", "Date"]
    )

    results = []

    # =========================================
    # BREAKOUT LOGIC
    # =========================================

    for ticker, g in df.groupby("TICKER"):

        g = g.tail(60).copy()

        if len(g) < 25:
            continue

        # -------------------------------------
        # BASE STRUCTURE
        # -------------------------------------

        base = g.iloc[-22:-1]

        today = g.iloc[-1]

        base_high = base["High"].max()

        highs_near_top = base[
            base["High"] >= base_high * 0.98
        ]

        # Need at least 2 touches
        if len(highs_near_top) < 2:
            continue

        # -------------------------------------
        # VOLUME
        # -------------------------------------

        avg_vol = base["Volume"].mean()

        if pd.isna(avg_vol) or avg_vol <= 0:
            continue

        avg_vol = round(avg_vol)

        # -------------------------------------
        # CANDLE
        # -------------------------------------

        bullish_today = (
            today["Close"] > today["Open"]
        )

        # -------------------------------------
        # BREAKOUT
        # -------------------------------------

        breakout = (

            (today["High"] > base_high)

            and

            (
                today["Volume"]
                >= 1.5 * avg_vol
            )

            and

            bullish_today
        )

        if breakout:

            breakout_pct = round(

                (
                    (
                        today["Close"]
                        - base_high
                    )
                    / base_high
                ) * 100,

                2
            )

            volume_ratio = round(

                today["Volume"] / avg_vol,

                2
            )

            results.append({

                "Breakout_Date":
                    today["Date"].strftime("%Y-%m-%d"),

                "TICKER":
                    ticker,

                "Sector":
                    today.get("Sector"),

                "Industry":
                    today.get("Industry"),

                "Breakout_Price":
                    round(today["Close"], 2),

                "Base_High":
                    round(base_high, 2),

                "Breakout_%":
                    breakout_pct,

                "Volume":
                    int(today["Volume"]),

                "Avg_Volume":
                    int(avg_vol),

                "Vol_Ratio":
                    volume_ratio
            })

    # =========================================
    # FINAL DF
    # =========================================

    results_df = pd.DataFrame(results)

    if not results_df.empty:

        results_df = results_df.sort_values(
            "Breakout_%",
            ascending=False
        )

    return results_df


def compute_relative_strength(df, spy_df, periods=[7, 21, 50, 100, 200]):

    results = []

    spy_df = spy_df.sort_values("Date")

    for ticker, group in df.groupby("TICKER"):

        group = group.sort_values("Date")

        merged = pd.merge(
            group,
            spy_df[["Date", "Close"]],
            on="Date",
            how="inner",
            suffixes=("", "_spy")
        )

        if len(merged) < 200:
            continue

        # Ensure numeric
        merged["Close"] = pd.to_numeric(merged["Close"], errors="coerce")
        merged["Close_spy"] = pd.to_numeric(merged["Close_spy"], errors="coerce")

        row = {
            "TICKER": ticker,
            "Industry": group["Industry"].iloc[-1],
            "Sector": group["Sector"].iloc[-1],
        }

        alignment_scores = []

        # Precompute daily direction
        stock_dir = np.sign(merged["Close"].diff())
        spy_dir = np.sign(merged["Close_spy"].diff())

        same_dir_series = (stock_dir == spy_dir).astype(int)

        for p in periods:

            # -----------------------------
            # RELATIVE STRENGTH
            # -----------------------------
            stock_ret = merged["Close"].pct_change(p)
            spy_ret = merged["Close_spy"].pct_change(p)

            rs = (1 + stock_ret) / (1 + spy_ret)
            row[f"RS_{p}"] = rs.iloc[-1]

            # -----------------------------
            # ALIGNMENT (LAST p DAYS ONLY)
            # -----------------------------
            align_count = same_dir_series.iloc[-p:].sum()
            row[f"ALIGN_{p}"] = align_count

            # normalized alignment (0 → 1)
            alignment_scores.append(align_count / p)

        # -----------------------------
        # FINAL RS SCORE
        # -----------------------------
        row["RS_SCORE"] = (
            row["RS_7"] * 0.35 +
            row["RS_21"] * 0.25 +
            row["RS_50"] * 0.2 +
            row["RS_100"] * 0.1 +
            row["RS_200"] * 0.1
        )

        # -----------------------------
        # FINAL ALIGN SCORE
        # -----------------------------
        row["ALIGN_SCORE"] = np.mean(alignment_scores)

        results.append(row)

    return pd.DataFrame(results)



def resample_to_weekly(df):
    df = df.copy()
    df = df.sort_index()

    weekly = df.resample("W-FRI").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    }).dropna()

    return weekly

# -----------------------------
# MAIN SCANNER
# -----------------------------

def run_scanner():

    df_symbols = pd.read_csv(csv_path)

    symbol_meta = df_symbols.set_index("Ticker")[["Sector", "Industry"]].to_dict("index")
    stock_list = df_symbols["Ticker"].to_list()

    # DAILY
    all_data = []
    full_history = []

    # WEEKLY
    weekly_latest = []
    weekly_history = []

    for i, tic in enumerate(stock_list, 1):

        data = get_historical_stock_data(tic, interval="1d")

        if data is None or len(data) < 150:
            continue

        if tic not in symbol_meta:
            continue

        try:
            # -----------------------------
            # DAILY FEATURES
            # -----------------------------

            daily_df = build_features(data, tic, symbol_meta[tic])

            if daily_df is None or daily_df.empty:
                continue

            full_history.append(daily_df)
            all_data.append(daily_df.tail(1))

            # -----------------------------
            # WEEKLY DATA (6 MONTHS)
            # -----------------------------

            weekly_raw = resample_to_weekly(data)

            # Keep last ~6 months (~26 weeks)
            weekly_raw = weekly_raw.tail(26)

            if len(weekly_raw) < 10:
                continue

            weekly_df = build_features(weekly_raw, tic, symbol_meta[tic])

            if weekly_df is not None and not weekly_df.empty:
                weekly_history.append(weekly_df)
                weekly_latest.append(weekly_df.tail(1))

            print(f"{i}/{len(stock_list)} ✔ {tic}")

        except Exception as e:
            print(f"{tic} ❌ {e}")

    results = {}

    # -----------------------------
    # SAVE DAILY
    # -----------------------------

    if all_data:
        latest_df = pd.concat(all_data, ignore_index=True).round(2)
        latest_df.to_parquet(DATA_DIR / "all_data.parquet", index=False)
        results["latest"] = latest_df

    if full_history:
        history_df = pd.concat(full_history, ignore_index=True).round(2)
        history_df.to_parquet(DATA_DIR / "full_history.parquet", index=False)
        results["history"] = history_df

    # -----------------------------
    # SAVE WEEKLY
    # -----------------------------

    if weekly_latest:
        weekly_latest_df = pd.concat(weekly_latest, ignore_index=True).round(2)
        weekly_latest_df.to_parquet(DATA_DIR / "weekly_latest.parquet", index=False)
        results["weekly_latest"] = weekly_latest_df

    if weekly_history:
        weekly_history_df = pd.concat(weekly_history, ignore_index=True).round(2)
        weekly_history_df.to_parquet(DATA_DIR / "weekly_history.parquet", index=False)
        results["weekly_history"] = weekly_history_df


    # =====================================
    # MASTER HISTORY BUILD
    # =====================================

    if full_history:

        history_df = (
            pd.concat(full_history, ignore_index=True)
            .round(2)
            .sort_values(["TICKER", "Date"])
            .reset_index(drop=True)
        )

        # =========================================================
        # KELTNER CHANNELS
        # =========================================================

        history_df = build_keltner_data(history_df)

        latest_keltner = (
            history_df.groupby("TICKER").tail(1).reset_index(drop=True)
        )

        latest_keltner.to_parquet(
            DATA_DIR / "keltner_latest.parquet",
            index=False
        )

        print("Keltner finished")

        # =========================================================
        # TURTLE SOUP
        # =========================================================

        history_df, ts_signals = build_turtle_soup_signals(history_df)

        ts_signals.to_parquet(
            DATA_DIR / "turtle_soup_signals.parquet",
            index=False
        )

        print("Turtle Soup finished")

        # =========================================================
        # STOCHASTIC SHORT
        # =========================================================

        history_df, ss_signals = build_stochastic_short_signals(history_df)

        ss_signals.to_parquet(
            DATA_DIR / "stochastic_short_signals.parquet",
            index=False
        )

        print("Stochastic Short finished")

        # =========================================================
        # FIB RETRACEMENT
        # =========================================================

        history_df, fib_latest = build_fib_retracement_data(history_df)

        fib_latest.to_parquet(
            DATA_DIR / "fib_retracement_latest.parquet",
            index=False
        )

        print("Fib finished")

        # =========================================================
        # EQUITY RANKING
        # =========================================================

        ranking_history, ranking_latest = build_equity_ranking(history_df)

        ranking_latest.to_parquet(
            DATA_DIR / "equity_ranking_latest.parquet",
            index=False
        )

        # =========================================================
        # MA STRUCTURE
        # =========================================================

        history_df, ma_latest = build_ma_structure(history_df)

        ma_latest.to_parquet(
            DATA_DIR / "ma_structure_latest.parquet",
            index=False
        )

        # =========================================================
        # BREAKOUT 21 (no history dependency change)
        # =========================================================

        breakout_21_df = build_breakout_21_signals(history_df)

        breakout_21_df.to_parquet(
            DATA_DIR / "breakout_21.parquet",
            index=False
        )

        print("21 Day Breakout finished")

        # =========================================================
        # RS SYSTEM
        # =========================================================

        spy_df = (
            history_df[history_df["TICKER"] == "^GSPC"][["Date", "Close"]]
            .sort_values("Date")
        )

        stock_df = history_df[history_df["TICKER"] != "^GSPC"].copy()

        rs_df = compute_relative_strength(stock_df, spy_df)

        rs_df.to_parquet(
            DATA_DIR / "industry_ticker_rs.parquet",
            index=False
        )

        industry_rs = (
            rs_df.groupby("Industry")["RS_SCORE"]
            .mean()
            .reset_index()
            .sort_values("RS_SCORE", ascending=False)
        )

        industry_rs.to_parquet(
            DATA_DIR / "industry_rs.parquet",
            index=False
        )

        rs_alignment_df = rs_df[[
            c for c in [
                "TICKER", "Industry", "Sector",
                "RS_7", "RS_21", "RS_50", "RS_100", "RS_200",
                "ALIGN_7", "ALIGN_21", "ALIGN_50", "ALIGN_100", "ALIGN_200",
                "RS_SCORE", "ALIGN_SCORE"
            ] if c in rs_df.columns
        ]]

        rs_alignment_df.to_parquet(
            DATA_DIR / "rs_alignment.parquet",
            index=False
        )

        # =========================================================
        # FINAL MASTER SAVE (ONLY ONE HISTORY FILE)
        # =========================================================

        history_df.to_parquet(
            DATA_DIR / "full_history.parquet",
            index=False
        )

        print("MASTER full_history.parquet saved with all indicators")

    return results
