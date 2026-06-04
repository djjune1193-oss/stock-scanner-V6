import pandas as pd
from pathlib import Path
from django.conf import settings
from .fetch_data import get_historical_stock_data
from .features import build_features
from datetime import datetime

# -----------------------------
# PATHS
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
csv_path = BASE_DIR / "ALL_STOCK_LIST.csv"

DATA_DIR = settings.DATA_DIR
DATA_DIR.mkdir(parents=True, exist_ok=True)




def build_equity_ranking(df):


    df["Date"] = pd.to_datetime(df["Date"])

    df = df.sort_values(
        ["TICKER", "Date"]
    )

    # =====================================
    # MULTI-TIMEFRAME RETURNS
    # =====================================

    periods = [7, 30, 90, 200]

    for period in periods:

        df[f"GAIN_{period}"] = (
            df.groupby("TICKER")["Close"]
            .transform(
                lambda x:
                (
                    x /
                    x.shift(period)
                    - 1
                ) * 100
            )
        )

    # =====================================
    # LATEST SNAPSHOT
    # =====================================

    latest_df = (
        df.groupby("TICKER")
        .tail(1)
        .copy()
    )

    # =====================================
    # RANKINGS
    # =====================================

    for period in periods:

        latest_df[f"RANK_{period}"] = (
            latest_df[f"GAIN_{period}"]
            .rank(
                ascending=False,
                method="min"
            )
            .astype("Int64")
        )

    # =====================================
    # DEFAULT VIEW
    # =====================================

    latest_df["RANKING"] = (
        latest_df["RANK_200"]
    )

    latest_df["CUMULATIVE_GAIN"] = (
        latest_df["GAIN_200"]
    )

    latest_df = latest_df.dropna(
        subset=[
            "GAIN_7",
            "GAIN_30",
            "GAIN_90",
            "GAIN_200"
        ]
    )

    latest_df = latest_df.sort_values(
        "RANKING"
    )

    return latest_df



# =========================================================
# BUILD FIB RETRACEMENT DATA
# =========================================================

def build_fib_retracement_data(df):


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
    # DISTANCE FROM EACH MA
    # =========================

    for ma in [10, 21, 34, 50, 100, 200]:

        latest_df[f"pct_from_ma{ma}"] = (
            (
                latest_df["Close"]
                - latest_df[f"MA_{ma}"]
            )
            / latest_df[f"MA_{ma}"]
        ) * 100

        latest_df[f"pct_from_ma{ma}"] = (
            latest_df[f"pct_from_ma{ma}"]
            .round(2)
        )


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


    # =====================================================
    # ENSURE DATETIME
    # =====================================================

    df["Date"] = pd.to_datetime(df["Date"])

    # =====================================================
    # SET DATETIME INDEX
    # =====================================================

    df = df.sort_values("Date")

    df = df.set_index("Date")

    # =====================================================
    # WEEKLY OHLCV
    # =====================================================

    weekly = df.resample("W").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    })

    # =====================================================
    # REMOVE EMPTY WEEKS
    # =====================================================

    weekly = weekly.dropna()

    # =====================================================
    # RESET INDEX BACK
    # =====================================================

    weekly = weekly.reset_index()

    return weekly

# -----------------------------
# MAIN SCANNER
# -----------------------------

def run_scanner():

    import numpy as np
    import pandas as pd

    symbols = pd.read_csv(csv_path)

    symbol_meta = (
        symbols.set_index("Ticker")[["Sector", "Industry"]]
        .to_dict("index")
    )

    stock_list = symbols["Ticker"].dropna().unique().tolist()

    keltner_latest_chunks = []
    fib_latest_chunks = []
    ma_latest_chunks = []
    turtle_signals = []
    stochastic_signals = []

    master = []

    print("\nStarting scanner...\n")

    # =====================================================
    # MAIN LOOP
    # =====================================================
    for i, ticker in enumerate(stock_list, 1):

        print(f"{i}/{len(stock_list)} {ticker}")

        try:
            df = get_historical_stock_data(ticker)

            if df is None or df.empty:
                continue

            meta = symbol_meta.get(
                ticker,
                {"Sector": "", "Industry": ""}
            )
            download_timestamp = pd.Timestamp.utcnow()
            print(download_timestamp)
            df = build_features(df, ticker, meta)
            df["download_timestamp"] = download_timestamp


            master.append(df)

            # ================= KELTNER =================
            df = build_keltner_data(df)
            keltner_latest_chunks.append(df.tail(1).copy())

            # ================= TURTLE =================
            df, ts_signals = build_turtle_soup_signals(df)
            if not ts_signals.empty:
                turtle_signals.append(ts_signals.copy())

            # ================= STOCH =================
            df, ss_signals = build_stochastic_short_signals(df)
            if not ss_signals.empty:
                stochastic_signals.append(ss_signals.copy())

            # ================= FIB =================
            df, fib_latest = build_fib_retracement_data(df)
            fib_latest_chunks.append(fib_latest.copy())

            # ================= MA =================
            df, ma_latest = build_ma_structure(df)
            ma_latest_chunks.append(ma_latest.copy())

        except Exception as e:
            print(f"{ticker} ❌ {e}")
            continue

    # =====================================================
    # FULL HISTORY (AFTER LOOP ONLY)
    # =====================================================
    full_history_df = pd.concat(master, ignore_index=True)
    full_history_df = full_history_df.sort_values(
        ["TICKER", "Date"]
    ).reset_index(drop=True)

    # =====================================================
    # SAVE FULL HISTORY
    # =====================================================

    full_history_df.to_parquet(
        DATA_DIR / "full_history.parquet",
        index=False
    )

    # =====================================================
    # SAVE KELTNER
    # =====================================================
    if keltner_latest_chunks:
        pd.concat(keltner_latest_chunks, ignore_index=True).to_parquet(
            DATA_DIR / "keltner_latest.parquet",
            index=False
        )

    # =====================================================
    # SAVE FIB
    # =====================================================
    if fib_latest_chunks:
        pd.concat(fib_latest_chunks, ignore_index=True).to_parquet(
            DATA_DIR / "fib_retracement_latest.parquet",
            index=False
        )

    # =====================================================
    # SAVE MA
    # =====================================================
    if ma_latest_chunks:
        pd.concat(ma_latest_chunks, ignore_index=True).to_parquet(
            DATA_DIR / "ma_structure_latest.parquet",
            index=False
        )

    # =====================================================
    # SAVE SIGNALS
    # =====================================================
    if turtle_signals:
        pd.concat(turtle_signals, ignore_index=True).to_parquet(
            DATA_DIR / "turtle_soup_signals.parquet",
            index=False
        )

    if stochastic_signals:
        pd.concat(stochastic_signals, ignore_index=True).to_parquet(
            DATA_DIR / "stochastic_short_signals.parquet",
            index=False
        )

    # =====================================================
    # BREAKOUT
    # =====================================================
    breakout_21_df = build_breakout_21_signals(full_history_df)
    breakout_21_df.to_parquet(DATA_DIR / "breakout_21.parquet", index=False)
    print("break out completed")

    # =====================================================
    # EQUITY RANKING
    # =====================================================
    ranking_latest = build_equity_ranking(full_history_df)
    ranking_latest.to_parquet(DATA_DIR / "equity_ranking_latest.parquet", index=False)
    print("rank completed")

    # =====================================================
    # RS SYSTEM
    # =====================================================
    spy_df = full_history_df[full_history_df["TICKER"] == "^GSPC"][["Date", "Close"]].sort_values("Date")
    stock_df = full_history_df[full_history_df["TICKER"] != "^GSPC"].copy()
    print("RS completed")

    rs_df = compute_relative_strength(stock_df, spy_df)

    rs_df.to_parquet(DATA_DIR / "industry_ticker_rs.parquet", index=False)

    industry_rs = (
        rs_df.groupby("Industry")["RS_SCORE"]
        .mean()
        .reset_index()
        .sort_values("RS_SCORE", ascending=False)
    )

    industry_rs.to_parquet(DATA_DIR / "industry_rs.parquet", index=False)

    # =====================================================
    # RS ALIGNMENT
    # =====================================================
    alignment_cols = [c for c in [
        "TICKER","Industry","Sector",
        "RS_7","RS_21","RS_50","RS_100","RS_200",
        "ALIGN_7","ALIGN_21","ALIGN_50","ALIGN_100","ALIGN_200",
        "RS_SCORE","ALIGN_SCORE"
    ] if c in rs_df.columns]

    rs_df[alignment_cols].to_parquet(
        DATA_DIR / "rs_alignment.parquet",
        index=False
    )
    print("RS Alignemnt completed")

    # =====================================================
    # WEEKLY
    # =====================================================
    weekly_frames = []

    for ticker, g in full_history_df.groupby("TICKER"):

        weekly = resample_to_weekly(g)

        meta = {
            "Sector": g["Sector"].iloc[-1],
            "Industry": g["Industry"].iloc[-1]
        }

        weekly_frames.append(
            build_features(weekly, ticker, meta)
        )

    weekly_history_df = pd.concat(weekly_frames, ignore_index=True)

    weekly_latest_df = (
        weekly_history_df
        .sort_values(["TICKER", "Date"])
        .groupby("TICKER")
        .tail(1)
        .reset_index(drop=True)
    )

    weekly_history_df.to_parquet(DATA_DIR / "weekly_history.parquet", index=False)
    weekly_latest_df.to_parquet(DATA_DIR / "weekly_latest.parquet", index=False)
    print("Weekly completed")

    print("\nSCANNER COMPLETED\n")

    return full_history_df
