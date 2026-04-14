import pandas as pd
from pathlib import Path

MACRO_TICKERS = [
    "^GSPC", "^DJI", "^NYA", "^IXIC", "^RUT", "^VIX", "^TNX", "^TYX"
]

BASE_DIR = Path(__file__).resolve().parents[3]
HISTORY_PATH = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"


def build_market_health_indicator():
    """
    Returns:
        dict {
            score: int (0–100),
            components: dict,
            date: str
        }
    """

    if not HISTORY_PATH.exists():
        return {"score": 0, "error": "History parquet not found"}

    df = pd.read_parquet(HISTORY_PATH)

    # Ensure datetime
    df["Date"] = pd.to_datetime(df["Date"])

    # Keep only macro tickers
    df = df[df["TICKER"].isin(MACRO_TICKERS)]

    if df.empty:
        return {"score": 0, "error": "No macro ticker data"}

    # Latest date snapshot
    latest_date = df["Date"].max()
    df_latest = df[df["Date"] == latest_date]

    # --- Helper functions ---
    def above_ma(row, ma):
        return row["Close"] > row.get(ma, row["Close"])

    # =========================
    # 1️⃣ Market Trend (30)
    # =========================
    trend_tickers = ["^GSPC", "^DJI", "^NYA"]
    trend_df = df_latest[df_latest["TICKER"].isin(trend_tickers)]

    trend_score = 0
    if len(trend_df) == 3:
        count = sum(
            (trend_df["Close"] > trend_df["50ma"]) &
            (trend_df["50ma"] > trend_df["200ma"])
        )
        trend_score = {3: 30, 2: 20, 1: 10}.get(count, 0)

    # =========================
    # 2️⃣ Breadth (15)
    # =========================
    breadth_score = 0
    try:
        nya = df_latest[df_latest["TICKER"] == "^NYA"].iloc[0]
        spx = df_latest[df_latest["TICKER"] == "^GSPC"].iloc[0]

        if nya["Close"] > spx["Close"]:
            breadth_score = 15
        elif abs(nya["Close"] - spx["Close"]) / spx["Close"] < 0.01:
            breadth_score = 8
    except Exception:
        pass

    # =========================
    # 3️⃣ Risk Appetite (20)
    # =========================
    risk_score = 0
    try:
        ixic = df_latest[df_latest["TICKER"] == "^IXIC"].iloc[0]
        rut = df_latest[df_latest["TICKER"] == "^RUT"].iloc[0]
        spx = df_latest[df_latest["TICKER"] == "^GSPC"].iloc[0]

        ixic_lead = ixic["Close"] > spx["Close"]
        rut_lead = rut["Close"] > spx["Close"]

        if ixic_lead and rut_lead:
            risk_score = 20
        elif ixic_lead:
            risk_score = 12
        elif rut_lead:
            risk_score = 8
    except Exception:
        pass

    # =========================
    # 4️⃣ Volatility (15)
    # =========================
    vol_score = 0
    try:
        vix = df_latest[df_latest["TICKER"] == "^VIX"].iloc[0]["Close"]

        if vix < 15:
            vol_score = 15
        elif vix < 20:
            vol_score = 10
        elif vix < 30:
            vol_score = 5
    except Exception:
        pass

    # =========================
    # 5️⃣ Rates (10)
    # =========================
    rate_score = 0
    try:
        tnx = df_latest[df_latest["TICKER"] == "^TNX"].iloc[0]["Close"]
        tyx = df_latest[df_latest["TICKER"] == "^TYX"].iloc[0]["Close"]

        if tnx < 5 and tyx < 6:
            rate_score = 10
        elif tnx < 5.5:
            rate_score = 6
        else:
            rate_score = 3
    except Exception:
        pass

    # =========================
    # 6️⃣ Alignment (10)
    # =========================
    align_score = 0
    risk_indices = ["^GSPC", "^DJI", "^NYA", "^IXIC", "^RUT"]
    greens = 0

    for t in risk_indices:
        row = df_latest[df_latest["TICKER"] == t]
        if not row.empty and row.iloc[0]["Close"] > row.iloc[0]["50ma"]:
            greens += 1

    align_score = {5: 10, 4: 7, 3: 4}.get(greens, 0)

    # =========================
    # FINAL SCORE
    # =========================
    total = (
        trend_score +
        breadth_score +
        risk_score +
        vol_score +
        rate_score +
        align_score
    )

    return {
        "score": min(max(int(total), 0), 100),
        "date": latest_date.strftime("%Y-%m-%d"),
        "components": {
            "trend": trend_score,
            "breadth": breadth_score,
            "risk": risk_score,
            "volatility": vol_score,
            "rates": rate_score,
            "alignment": align_score,
        }
    }
