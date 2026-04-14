import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
from pathlib import Path
import numpy as np

# -----------------------------
# PATH SETUP
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = DATA_DIR / "finviz_fundamentals.parquet"
TICKER_FILE = BASE_DIR / "ALL_STOCK_LIST.csv"

# -----------------------------
# REQUIRED COLUMNS
# -----------------------------
REQUIRED_COLS = [
    "Market Cap", "Forward P/E", "Shs Float", "Income", "P/S", "Sales",
    "ROA", "Dividend Est", "Gross Margin", "Oper Margin", "ATR (14)",
    "Profit Margin", "RSI (14)", "EPS Q/Q", "SMA20", "Beta",
    "Sales Q/Q", "SMA50", "Rel Volume", "SMA200", "Change", "TICKER"
]

# -----------------------------
# LOAD TICKERS
# -----------------------------
df_symbols = pd.read_csv(TICKER_FILE)
stock_list = df_symbols["Ticker"].dropna().unique().tolist()


import numpy as np
import re

def parse_value(x):
    if pd.isna(x):
        return np.nan

    x = str(x).strip()

    if x in ["-", ""]:
        return np.nan

    # -----------------------------
    # Handle "1.00 (0.87%)"
    # -----------------------------
    if "(" in x and ")" in x:
        inside = re.search(r"\((.*?)\)", x)
        if inside:
            val = inside.group(1).replace("%", "")
            try:
                return float(val)
            except:
                pass  # fallback below

    # -----------------------------
    # Percent
    # -----------------------------
    if "%" in x:
        try:
            return float(x.replace("%", ""))
        except:
            return np.nan

    # -----------------------------
    # Billions / Millions
    # -----------------------------
    if "B" in x:
        return float(x.replace("B", "")) * 1e9
    if "M" in x:
        return float(x.replace("M", "")) * 1e6

    # -----------------------------
    # Remove commas
    # -----------------------------
    x = x.replace(",", "")

    try:
        return float(x)
    except:
        return np.nan





# -----------------------------
# SCRAPER FUNCTION
# -----------------------------
def get_finviz_stock_data(ticker):
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        print(f"Fetching {ticker}...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="snapshot-table2")

        if not table:
            print(f"❌ No table for {ticker}")
            return pd.DataFrame()

        data_dict = {}

        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            for i in range(0, len(cells), 2):
                key = cells[i].get_text(strip=True)
                value = cells[i + 1].get_text(strip=True)
                data_dict[key] = value

        df = pd.DataFrame([data_dict])
        return df

    except Exception as e:
        print(f"❌ Error for {ticker}: {e}")
        return pd.DataFrame()

# -----------------------------
# MAIN FUNCTION
# -----------------------------
def run_finviz():

    all_data = []

    for ticker in stock_list:

        # Avoid getting blocked
        time.sleep(1 + random.uniform(0.5, 1.5))

        df = get_finviz_stock_data(ticker)

        if not df.empty:
            df["TICKER"] = ticker

            # Clean column names
            df.columns = df.columns.str.replace(".", "", regex=False).str.strip()

            # Keep only required columns
            df = df[[col for col in REQUIRED_COLS if col in df.columns]]
            for col in df.columns:
                if col not in ["TICKER"]:
                    df[col] = df[col].apply(parse_value)

            all_data.append(df)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)

        # Add timestamp
        final_df["last_updated"] = pd.Timestamp.now()

        # Save parquet
        final_df.to_parquet(OUTPUT_FILE, index=False)

        print(f"\n✅ Saved Finviz data to: {OUTPUT_FILE}")
        print(f"Rows: {len(final_df)}")

    else:
        print("❌ No data collected.")


# -----------------------------
# ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    run_finviz()
