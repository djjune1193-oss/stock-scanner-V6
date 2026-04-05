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

# -----------------------------
# HELPER: DAILY → WEEKLY (CALENDAR)
# -----------------------------


import numpy as np


import numpy as np
import pandas as pd

import numpy as np
import pandas as pd

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


    if full_history:

        history_df = pd.concat(full_history, ignore_index=True).round(2)

        # SPY data (^GSPC)
        spy_df = history_df[history_df["TICKER"] == "^GSPC"][["Date", "Close"]].sort_values("Date")

        stock_df = history_df[history_df["TICKER"] != "^GSPC"].copy()

        rs_df = compute_relative_strength(stock_df, spy_df)

        # -----------------------------
        # SAVE MAIN RS DATA
        # -----------------------------
        rs_df.to_parquet(DATA_DIR / "industry_ticker_rs.parquet", index=False)

        # -----------------------------
        # INDUSTRY RS
        # -----------------------------
        industry_rs = (
            rs_df.groupby("Industry")["RS_SCORE"]
            .mean()
            .reset_index()
            .sort_values("RS_SCORE", ascending=False)
        )

        industry_rs.to_parquet(DATA_DIR / "industry_rs.parquet", index=False)

        # -----------------------------
        # RS ALIGNMENT PARQUET
        # -----------------------------
        alignment_cols = [
            "TICKER", "Industry", "Sector",
            "RS_7", "RS_21", "RS_50", "RS_100", "RS_200",
            "ALIGN_7", "ALIGN_21", "ALIGN_50", "ALIGN_100", "ALIGN_200",
            "RS_SCORE", "ALIGN_SCORE"
        ]

        alignment_cols = [c for c in alignment_cols if c in rs_df.columns]

        rs_alignment_df = rs_df[alignment_cols].copy()

        rs_alignment_df.to_parquet(
            DATA_DIR / "rs_alignment.parquet",
            index=False
        )

        

        

        

    # -----------------------------
    # SUMMARY
    # -----------------------------

    print("\nScanner completed:")
    print(f"Daily latest: {len(all_data)}")
    print(f"Daily history: {len(full_history)}")
    print(f"Weekly latest: {len(weekly_latest)}")
    print(f"Weekly history: {len(weekly_history)}")

    return results

