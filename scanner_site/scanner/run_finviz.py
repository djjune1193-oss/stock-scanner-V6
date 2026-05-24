from pathlib import Path

import yfinance as yf
import pandas as pd
import numpy as np


# ==========================================================
# PATH SETUP
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = DATA_DIR / "finviz_fundamentals.parquet"

TICKER_FILE = BASE_DIR / "ALL_STOCK_LIST.csv"


# ==========================================================
# LOAD TICKERS
# ==========================================================

df_symbols = pd.read_csv(TICKER_FILE)

TICKERS = (
    df_symbols["Ticker"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)


# ==========================================================
# HELPERS
# ==========================================================

def safe_get(df, row_name):

    try:

        if row_name in df.index:
            return df.loc[row_name]

    except:
        pass

    return None


def safe_round(value, digits=2):

    try:

        if pd.isna(value):
            return np.nan

        return round(float(value), digits)

    except:
        return np.nan


def billions(value):

    try:

        if pd.isna(value):
            return np.nan

        return round(float(value) / 1_000_000_000, 2)

    except:
        return np.nan


def millions(value):

    try:

        if pd.isna(value):
            return np.nan

        return round(float(value) / 1_000_000, 2)

    except:
        return np.nan


def qoq_change(current, previous):

    try:

        if pd.isna(current) or pd.isna(previous):
            return np.nan

        if previous == 0:
            return np.nan

        return (
            (current - previous)
            / abs(previous)
        ) * 100

    except:
        return np.nan


def latest_four(series):

    try:

        if series is None:
            return []

        series = series.dropna()

        values = []

        for value in series.iloc[:4]:

            values.append(float(value))

        return values

    except:
        return []


def build_qoq_progression(values):

    results = []

    try:

        if len(values) < 2:
            return results

        for i in range(len(values) - 1):

            current = values[i]
            previous = values[i + 1]

            change = qoq_change(
                current,
                previous
            )

            results.append(
                safe_round(change)
            )

    except:
        pass

    return results


def progression_string(values):

    try:

        cleaned = []

        for value in values:

            if pd.isna(value):
                continue

            cleaned.append(
                str(round(value, 2))
            )

        return ", ".join(cleaned)

    except:
        return ""


def billions_progression(values):

    try:

        cleaned = []

        for value in values:

            cleaned.append(
                str(
                    round(
                        value / 1_000_000_000,
                        2
                    )
                )
            )

        return ", ".join(cleaned)

    except:
        return ""


def eps_progression(values):

    try:

        cleaned = []

        for value in values:

            cleaned.append(
                str(round(value, 2))
            )

        return ", ".join(cleaned)

    except:
        return ""


# ==========================================================
# MAIN
# ==========================================================

def run_finviz():

    results = []

    for ticker_symbol in TICKERS:

        print(f"Processing {ticker_symbol}...")

        try:

            ticker = yf.Ticker(
                ticker_symbol
            )

            info = ticker.info

            # ==================================================
            # BASIC
            # ==================================================

            current_price = info.get(
                "currentPrice",
                np.nan
            )

            market_cap = info.get(
                "marketCap",
                np.nan
            )

            float_shares = info.get(
                "floatShares",
                np.nan
            )

            shares_outstanding = info.get(
                "sharesOutstanding",
                np.nan
            )

            # ==================================================
            # FLOAT ADJUSTED MARKET CAP
            # ==================================================

            float_market_cap = np.nan

            try:

                if (
                    not pd.isna(float_shares)
                    and not pd.isna(current_price)
                ):

                    float_market_cap = (
                        float_shares
                        * current_price
                    )

            except:
                pass

            # ==================================================
            # QUARTERLY FINANCIALS
            # ==================================================

            income_stmt = (
                ticker.quarterly_income_stmt
            )

            if income_stmt.empty:

                print(
                    f"No quarterly data for {ticker_symbol}"
                )

                continue

            # ==================================================
            # REVENUE
            # ==================================================

            revenue_series = safe_get(
                income_stmt,
                "Total Revenue"
            )

            if revenue_series is None:

                revenue_series = safe_get(
                    income_stmt,
                    "Operating Revenue"
                )

            revenue_values = latest_four(
                revenue_series
            )

            revenue_qoq_progress = (
                build_qoq_progression(
                    revenue_values
                )
            )

            # ==================================================
            # PROFIT
            # ==================================================

            profit_series = safe_get(
                income_stmt,
                "Net Income"
            )

            if profit_series is None:

                profit_series = safe_get(
                    income_stmt,
                    "Net Income Common Stockholders"
                )

            profit_values = latest_four(
                profit_series
            )

            profit_qoq_progress = (
                build_qoq_progression(
                    profit_values
                )
            )

            # ==================================================
            # OPERATING INCOME
            # ==================================================

            op_series = safe_get(
                income_stmt,
                "Operating Income"
            )

            op_values = latest_four(
                op_series
            )

            op_qoq_progress = (
                build_qoq_progression(
                    op_values
                )
            )

            # ==================================================
            # EPS
            # ==================================================

            eps_series = safe_get(
                income_stmt,
                "Diluted EPS"
            )

            eps_values = latest_four(
                eps_series
            )

            eps_qoq_progress = (
                build_qoq_progression(
                    eps_values
                )
            )

            # ==================================================
            # LATEST Q/Q
            # ==================================================

            latest_revenue_qoq = (
                revenue_qoq_progress[0]
                if len(revenue_qoq_progress) > 0
                else np.nan
            )

            latest_profit_qoq = (
                profit_qoq_progress[0]
                if len(profit_qoq_progress) > 0
                else np.nan
            )

            latest_op_qoq = (
                op_qoq_progress[0]
                if len(op_qoq_progress) > 0
                else np.nan
            )

            latest_eps_qoq = (
                eps_qoq_progress[0]
                if len(eps_qoq_progress) > 0
                else np.nan
            )

            # ==================================================
            # HISTORICAL Q/Q
            # ==================================================

            historical_revenue_qoq = (
                progression_string(
                    revenue_qoq_progress[1:]
                )
            )

            historical_profit_qoq = (
                progression_string(
                    profit_qoq_progress[1:]
                )
            )

            historical_op_qoq = (
                progression_string(
                    op_qoq_progress[1:]
                )
            )

            historical_eps_qoq = (
                progression_string(
                    eps_qoq_progress[1:]
                )
            )

            # ==================================================
            # VALUATION
            # ==================================================

            trailing_pe = info.get(
                "trailingPE",
                np.nan
            )

            forward_pe = info.get(
                "forwardPE",
                np.nan
            )

            price_to_book = info.get(
                "priceToBook",
                np.nan
            )

            peg_ratio = info.get(
                "pegRatio",
                np.nan
            )

            # ==================================================
            # P/S
            # ==================================================

            ps_ratio = np.nan

            try:

                if len(revenue_values) > 0:

                    annualized_revenue = (
                        revenue_values[0] * 4
                    )

                    if annualized_revenue > 0:

                        ps_ratio = (
                            market_cap
                            / annualized_revenue
                        )

            except:
                pass

            # ==================================================
            # QUALITY
            # ==================================================

            roe = info.get(
                "returnOnEquity",
                np.nan
            )

            roa = info.get(
                "returnOnAssets",
                np.nan
            )

            gross_margin = info.get(
                "grossMargins",
                np.nan
            )

            operating_margin = info.get(
                "operatingMargins",
                np.nan
            )

            profit_margin = info.get(
                "profitMargins",
                np.nan
            )

            # ==================================================
            # TRADING
            # ==================================================

            volume = info.get(
                "volume",
                np.nan
            )

            avg_volume = info.get(
                "averageVolume",
                np.nan
            )

            relative_volume = np.nan

            try:

                if (
                    not pd.isna(volume)
                    and not pd.isna(avg_volume)
                    and avg_volume != 0
                ):

                    relative_volume = (
                        volume / avg_volume
                    )

            except:
                pass

            beta = info.get(
                "beta",
                np.nan
            )

            short_percent_float = info.get(
                "shortPercentOfFloat",
                np.nan
            )

            # ==================================================
            # STORE RESULTS
            # ==================================================

            results.append({

                # ==================================================
                # BASIC
                # ==================================================

                "Ticker": ticker_symbol,

                "Price": safe_round(
                    current_price
                ),

                # ==================================================
                # MARKET STRUCTURE
                # ==================================================

                "Market Cap (B)": billions(
                    market_cap
                ),

                "Float Adj Market Cap (B)": billions(
                    float_market_cap
                ),

                "Float Shares (M)": millions(
                    float_shares
                ),

                "Shares Outstanding (B)": billions(
                    shares_outstanding
                ),

                # ==================================================
                # VALUATION
                # ==================================================

                "P/E": safe_round(
                    trailing_pe
                ),

                "Forward P/E": safe_round(
                    forward_pe
                ),

                "P/S": safe_round(
                    ps_ratio
                ),

                "P/B": safe_round(
                    price_to_book
                ),

                "PEG": safe_round(
                    peg_ratio
                ),

                # ==================================================
                # QUALITY
                # ==================================================

                "ROE %": safe_round(
                    roe * 100
                ) if not pd.isna(roe)
                else np.nan,

                "ROA %": safe_round(
                    roa * 100
                ) if not pd.isna(roa)
                else np.nan,

                "Gross Margin %": safe_round(
                    gross_margin * 100
                ) if not pd.isna(gross_margin)
                else np.nan,

                "Operating Margin %": safe_round(
                    operating_margin * 100
                ) if not pd.isna(operating_margin)
                else np.nan,

                "Profit Margin %": safe_round(
                    profit_margin * 100
                ) if not pd.isna(profit_margin)
                else np.nan,

                # ==================================================
                # TRADING
                # ==================================================

                "Volume (M)": millions(
                    volume
                ),

                "Avg Volume (M)": millions(
                    avg_volume
                ),

                "Relative Volume": safe_round(
                    relative_volume
                ),

                "Beta": safe_round(
                    beta
                ),

                "Short Float %": safe_round(
                    short_percent_float * 100
                ) if not pd.isna(short_percent_float)
                else np.nan,

                # ==================================================
                # QUARTERLY VALUES
                # ==================================================

                "Revenue Quarters (B)": (
                    billions_progression(
                        revenue_values
                    )
                ),

                "Profit Quarters (B)": (
                    billions_progression(
                        profit_values
                    )
                ),

                "Operating Income Quarters (B)": (
                    billions_progression(
                        op_values
                    )
                ),

                "EPS Quarters": (
                    eps_progression(
                        eps_values
                    )
                ),

                # ==================================================
                # LATEST Q/Q
                # ==================================================

                "Revenue Latest Q/Q %":
                    latest_revenue_qoq,

                "Profit Latest Q/Q %":
                    latest_profit_qoq,

                "Operating Income Latest Q/Q %":
                    latest_op_qoq,

                "EPS Latest Q/Q %":
                    latest_eps_qoq,

                # ==================================================
                # HISTORICAL Q/Q
                # ==================================================

                "Revenue Historical Q/Q %":
                    historical_revenue_qoq,

                "Profit Historical Q/Q %":
                    historical_profit_qoq,

                "Operating Income Historical Q/Q %":
                    historical_op_qoq,

                "EPS Historical Q/Q %":
                    historical_eps_qoq,

            })

        except Exception as e:

            print(
                f"ERROR {ticker_symbol}: {e}"
            )

    # ==========================================================
    # FINAL DATAFRAME
    # ==========================================================

    final_df = pd.DataFrame(results)

    # ==========================================================
    # SORT
    # ==========================================================

    if not final_df.empty:

        final_df = final_df.sort_values(
            by="Revenue Latest Q/Q %",
            ascending=False
        )

    # ==========================================================
    # SAVE PARQUET
    # ==========================================================

    final_df.to_parquet(
        OUTPUT_FILE,
        index=False
    )

    print("\nSaved:")
    print(OUTPUT_FILE)

    print("\nRows:")
    print(len(final_df))


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    run_finviz()
