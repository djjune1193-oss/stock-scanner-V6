import pandas as pd
from pathlib import Path


def get_industry_relative_strength():

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)
    df["Date"] = pd.to_datetime(df["Date"])

    # -----------------------------
    # EXTRACT SPY (^GSPC)
    # -----------------------------
    spy = df[df["TICKER"] == "^GSPC"].copy()

    if spy.empty:
        raise ValueError("^GSPC not found in parquet")

    spy = spy.sort_values("Date")

    periods = [7, 21, 50, 100, 200]
    results = []

    # -----------------------------
    # STOCK LEVEL RS
    # -----------------------------
    for ticker, group in df.groupby("TICKER"):

        if ticker == "^GSPC":
            continue

        group = group.sort_values("Date")

        merged = pd.merge(
            group,
            spy[["Date", "Close"]],
            on="Date",
            how="inner",
            suffixes=("", "_spy")
        )

        if len(merged) < 200:
            continue

        row = {
            "TICKER": ticker,
            "Industry": group["Industry"].iloc[-1] if "Industry" in group.columns else None,
        }

        for p in periods:
            stock_ret = merged["Close"].pct_change(p)
            spy_ret = merged["Close_spy"].pct_change(p)

            rs = (1 + stock_ret) / (1 + spy_ret)
            row[f"RS_{p}"] = rs.iloc[-1]

        results.append(row)

    rs_df = pd.DataFrame(results)

    # -----------------------------
    # INDUSTRY LEVEL
    # -----------------------------
    industry_rs = (
        rs_df.groupby("Industry")[["RS_7", "RS_21", "RS_50", "RS_100", "RS_200"]]
        .mean()
        .reset_index()
    )

    # Remove ETF industries
    industry_rs = industry_rs[~industry_rs["Industry"].str.contains("ETF", na=False)]

    # -----------------------------
    # OVERALL RS SCORE (KEY PART)
    # -----------------------------
    industry_rs["RS_SCORE"] = (
        0.30 * industry_rs["RS_7"] +
        0.25 * industry_rs["RS_21"] +
        0.20 * industry_rs["RS_50"] +
        0.15 * industry_rs["RS_100"] +
        0.10 * industry_rs["RS_200"]
    )

    # Round for clean UI
    industry_rs = industry_rs.round(3)

    # -----------------------------
    # SORT BY SCORE
    # -----------------------------
    industry_rs = industry_rs.sort_values("RS_SCORE", ascending=False)

    return industry_rs
