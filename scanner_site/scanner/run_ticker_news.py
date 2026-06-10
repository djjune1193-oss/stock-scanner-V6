import finnhub
import pandas as pd
from datetime import datetime, timedelta
import time
from pathlib import Path


def run_ticker_news_job():
    # ==========================================================
    # PATH SETUP
    # ==========================================================

    BASE_DIR = Path(__file__).resolve().parent.parent

    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    TICKER_FILE = BASE_DIR / "ALL_STOCK_LIST.csv"
    OUTPUT_FILE = DATA_DIR / "ticker_news.parquet"

    # ==========================================================
    # FINNHUB CLIENT
    # ==========================================================

    client = finnhub.Client(api_key="d8hlhn1r01qrn5ecpur0d8hlhn1r01qrn5ecpurg")

    # ==========================================================
    # LOAD TICKERS
    # ==========================================================

    tickers = pd.read_csv(TICKER_FILE)["Ticker"].dropna().unique()

    # ==========================================================
    # DATE RANGE
    # ==========================================================

    today = datetime.now().date()
    start = today - timedelta(days=7)

    results = []

    # ==========================================================
    # FETCH NEWS
    # ==========================================================

    for ticker in tickers:
        time.sleep(1.5)

        try:
            news = client.company_news(
                ticker,
                _from=start.strftime("%Y-%m-%d"),
                to=today.strftime("%Y-%m-%d")
            )

            if news:
                
                latest = sorted(
                    news,
                    key=lambda x: x.get("datetime", 0),
                    reverse=True
                )[0]
                print(latest)
                results.append({
                    "Ticker": ticker,
                    "headline": latest.get("headline"),
                    "source": latest.get("source"),
                    "datetime": pd.to_datetime(latest.get("datetime"), unit="s"),
                    "url": latest.get("url")
                })

            else:
                results.append({
                    "Ticker": ticker,
                    "headline": None,
                    "source": None,
                    "datetime": None,
                    "url": None
                })

        except Exception as e:
            print(f"{ticker}: {e}")

    # ==========================================================
    # SAVE OUTPUT
    # ==========================================================

    news_df = pd.DataFrame(results)

    news_df.to_parquet(
        OUTPUT_FILE,
        index=False
    )

    print(f"[NEWS JOB] Saved to: {OUTPUT_FILE}")

    return OUTPUT_FILE
