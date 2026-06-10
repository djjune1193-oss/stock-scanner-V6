import requests
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def fetch_top_headlines():

    API_KEY = "d8hlhn1r01qrn5ecpur0d8hlhn1r01qrn5ecpurg"

    OUTPUT_FILE = DATA_DIR / "top_headlines.parquet"

    url = (
        f"https://finnhub.io/api/v1/news"
        f"?category=general"
        f"&token={API_KEY}"
    )

    try:
        news = requests.get(
            url,
            timeout=30
        ).json()

    except Exception as e:
        print(f"Headline fetch failed: {e}")
        return

    rows = []

    for item in news[:40]:

        rows.append({
            "datetime": pd.to_datetime(
                item.get("datetime"),
                unit="s"
            ),
            "headline": item.get("headline", ""),
            "source": item.get("source", ""),
            "url": item.get("url", ""),
            "category": item.get("category", ""),
            "image": item.get("image", ""),
            "related": item.get("related", ""),
            "summary": item.get("summary", "")
        })

    df = pd.DataFrame(rows)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_parquet(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Saved {len(df)} headlines -> {OUTPUT_FILE}"
    )
