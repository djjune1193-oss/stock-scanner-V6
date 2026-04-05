import pandas as pd
import numpy as np
from django.shortcuts import render
from pathlib import Path
from django.conf import settings



from .services.market_health import build_market_health_indicator
from .services.scan_status import get_scan_status

def home(request):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "all_data.parquet"

    df = pd.read_parquet(data_path)

    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
    today = df["Date"].max()

    today_df = df[df["Date"] == today].copy()

    # ---------- Market Health ----------
    mhi = build_market_health_indicator()
    scanner_status = get_scan_status()

    # ---------- Market Breadth ----------
    up_count = (today_df["perc_change"] > 0).sum()
    down_count = (today_df["perc_change"] < 0).sum()
    flat_count = (today_df["perc_change"] == 0).sum()

    # ---------- Index Values + % Change ----------
    index_tickers = ["^IXIC", "^GSPC", "^RUT", "^VIX"]

    index_df = today_df[today_df["TICKER"].isin(index_tickers)]

    index_values = {}

    for _, row in index_df.iterrows():
        t = row["TICKER"]

        if t == "^IXIC":
            key = "IXIC"
        elif t == "^GSPC":
            key = "GSPC"
        elif t == "^RUT":
            key = "RUT"
        elif t == "^VIX":
            key = "VIX"

        index_values[key] = {
            "close": round(row["Close"], 2),
            "pct": round(row["perc_change"], 2)
        }

    # ---------- Scanner Table ----------
    selected_columns = [
        "Date","TICKER","perc_change","Sector","Industry",
        "Close","Open","High","Low","Volume"
    ]

    table_df = today_df[selected_columns].sort_values("Volume", ascending=False)

    tic_remove = ["^GSPC", "^DJI","^NYA","^RUT","^VIX","^TNX","^TYX","^IXIC"]
    mask = ~table_df['TICKER'].isin(tic_remove)
    table_df = table_df.loc[mask]
    table_df["Date"] = table_df["Date"].dt.date

    return render(
        request,
        "scanner_dashboard/home.html",
        
        {   "scanner_status": scanner_status,
            "columns": table_df.columns.tolist(),
            "rows": table_df.values.tolist(),
            "mhi": mhi,
            "index_values": index_values,
            "up_count": int(up_count),
            "down_count": int(down_count),
            "flat_count": int(flat_count),
        }
    )



def scanner_view(request):
    BASE_DIR = Path(__file__).resolve().parents[2]  # project root
    data_path = BASE_DIR  /"scanner_site"/ "data" / "all_data.parquet"
    df = pd.read_parquet(data_path)
    df = df.reset_index()

    # Define scanner condition
    target_values = ['Bullish Hammer', 'Bullish Marubozu (Strong Buy)', 'Standard Bullish Candle']

    row_condition = (
        (df["Candle_Type"].isin(target_values)) &
        (df["21ma"] > df["50ma"]) &
        (df["Close"] > df["200ma"]) &
        (df["slope_50"] > 0) &
        (
            (
                (df["Low"] < df["21ma"]) &
                (df["Close"] > df["21ma"])
            ) |
            (
                (df["Low"] < df["34ma"]) &
                (df["Close"] > df["34ma"])
            )
        ) &
        (df["slope_d"] > 0) &
        (df["lower_count"] > 0)
    )

    scanner_df = df[row_condition].copy()
    selected_columns = ["Date","TICKER","perc_change","Sector","Industry", "Close", "Open", "High", "Low", "Volume",  "Candle_Type","slope_50","lower_count","Position_Size"]
    scanner_df = scanner_df[selected_columns]

    return render(
        request,
        "scanner_dashboard/scanner.html",
        {
            "columns": scanner_df.columns.tolist(),
            "rows": scanner_df.values.tolist()
        }
    )


def flat_bollinger_view(request):
    BASE_DIR = Path(__file__).resolve().parents[2]  # project root
    data_path = BASE_DIR  /"scanner_site"/ "data" / "all_data.parquet"
    df = pd.read_parquet(data_path)
    df = df.reset_index()

    # Define scanner condition
    target_values = ['Bullish Hammer', 'Bullish Marubozu (Strong Buy)', 'Standard Bullish Candle']    
    row_condition = (
        (df["Candle_Type"].isin(target_values)) &
        (df["Close"] > df["200ma"])&
        (df["Close"] > df["50ma"])&
        (df["Close"] < df["SMA"])&
        (df["34ma"] > df["50ma"]) &
        (df["slope_Lower"] > 0)&
        (df["slope_d"] > 0) &
        (df["lower_count"] > 0)
    )



    bollinger_df = df[row_condition].copy()
    selected_columns = ["Date","TICKER","perc_change","Sector","Industry", "Close", "Open", "High", "Low", "Volume",  "Candle_Type","slope_Lower", "delta_upper", "lower_count","Position_Size" ]
    bollinger_df  = bollinger_df [selected_columns]

    return render(
        request,
        "scanner_dashboard/Bollinger.html",
        {
            "columns": bollinger_df.columns.tolist(),
            "rows": bollinger_df.values.tolist(), 
        }
    )


def hot_ten_day_view(request):
    BASE_DIR = Path(__file__).resolve().parents[2]  # project root
    data_path = BASE_DIR  /"scanner_site"/ "data" / "all_data.parquet"
    df = pd.read_parquet(data_path)
    df = df.reset_index()

    # Define scanner condition
    target_values = ['Bullish Hammer', 'Bullish Marubozu (Strong Buy)', 'Standard Bullish Candle']    
    row_condition = (
        (df["Candle_Type"].isin(target_values)) &
        (df["Close"] > df["200ma"])&
        (df["21ma"] > df["50ma"]) &
        (df["slope_50"] > 0) &
        (
            (
                (df["Low"] < df["10ma"]) &
                (df["Close"] > df["10ma"])
            ) |
            (
                (df["Low"] < df["13ma"]) &
                (df["Close"] > df["13ma"])
            )
        ) &
        (df["slope_d"] > 0) &
        (df["lower_count"] > 0)
    )


    hot_ten_day = df[row_condition].copy()
    selected_columns = ["Date","TICKER","perc_change","Sector","Industry", "Close", "Open", "High", "Low", "Volume",  "Candle_Type","slope_Lower", "delta_upper", "lower_count","Position_Size" ]
    hot_ten_day  = hot_ten_day[selected_columns]

    return render(
        request,
        "scanner_dashboard/hot_ten_day.html",
        {
            "columns": hot_ten_day.columns.tolist(),
            "rows": hot_ten_day.values.tolist(), 
        }
    )


def sector_view(request):
    
    BASE_DIR = Path(__file__).resolve().parents[2]  # project root
    data_path = BASE_DIR  /"scanner_site"/ "data" / "all_data.parquet"
    df = pd.read_parquet(data_path)
    df = df.reset_index()

    selected_columns = ["Date","TICKER","perc_change","Sector","Industry", "Close", "Open", "High", "Low", "Volume"]
    df = df[selected_columns]
    context = {}

    row_condition = (
        (df['Industry'].str.contains('ETF', na=False))  
    )

    sector_df = df[row_condition].copy()
    today = pd.Timestamp("today").normalize()
    sector_df["Date"] = pd.to_datetime(sector_df["Date"]).dt.normalize()  # normalize to remove time part
    sector_df = sector_df.sort_values("perc_change", ascending=False).reset_index(drop=True)
    sector_df["Date"] = sector_df["Date"].dt.date
    
    return render(
        request,
        "scanner_dashboard/sector.html",
        {
            "columns": sector_df.columns.tolist(),
            "rows": sector_df.values.tolist()
        }
    )



def double_bottom_view(request):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "double_bottom_signals.parquet"

    new_order = [
        "signal_date","TICKER","close_price","neckline_price",
        "neckline_date","L1_low","L2_low","L1_date","L2_date",
        "LHS","RHS","Symmetry"
    ]

    df = pd.DataFrame()

    try:
        if data_path.exists():
            df = pd.read_parquet(data_path)

            if not df.empty:
                # Keep only available columns
                available_cols = [c for c in new_order if c in df.columns]
                df = df[available_cols]

    except Exception as e:
        print("Double bottom load error:", e)
        df = pd.DataFrame(columns=new_order)

    return render(
        request,
        "scanner_dashboard/double_bottom.html",
        {
            "columns": df.columns.tolist(),
            "rows": df.values.tolist(),
        }
    )



def turtle_soup_view(request):
    BASE_DIR = Path(__file__).resolve().parents[2]  # project root
    data_path = BASE_DIR  /"scanner_site"/ "data" / "all_data.parquet"
    df = pd.read_parquet(data_path)
    df = df.reset_index()

    # Define scanner condition  
    row_condition = (
            (df["opposite_3days"] == True) &
            (df["K_up_today"] == True) &
            (df["Close"] > df["50ma"])&
            (df["D_slope"] > 0)
        )

    scanner_df = df[row_condition].copy()
    selected_columns = ["Date","TICKER","perc_change","Sector","Industry", "Close", "Open", "High", "Low", "Volume",  "Candle_Type","slope_50","lower_count","Position_Size"]
    scanner_df = scanner_df[selected_columns]

    return render(
        request,
        "scanner_dashboard/turtle_soup.html",
        {
            "columns": scanner_df.columns.tolist(),
            "rows": scanner_df.values.tolist()
        }
    )



from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.http import HttpResponse
import threading

from .services.scanner_runner import run_full_scan
from .services.scan_status import set_scan_running

@require_POST
def refresh_scanner(request):
    try:
        set_scan_running(True)

        def background_job():
            try:
                run_full_scan()
            finally:
                set_scan_running(False)
                
        set_scan_running(True)
        threading.Thread(target=background_job, daemon=True).start()
        return redirect("home")

    except Exception as e:
        return HttpResponse(f"Error running scanner: {e}", status=500)






def equity_chart(request, ticker):

    BASE_DIR = Path(__file__).resolve().parents[2]
    DATA_PATH = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"
    if not DATA_PATH.exists():
        return render(request, "scanner_dashboard/chart_error.html")

    df = pd.read_parquet(DATA_PATH)
    df = df[df["TICKER"] == ticker].sort_values("Date")

    if df.empty:
        return render(request, "scanner_dashboard/chart_error.html", {"ticker": ticker})

    # Convert for JS
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    context = {
        "ticker": ticker,
        "dates": df["Date"].tolist(),
        "open": df["Open"].tolist(),
        "high": df["High"].tolist(),
        "low": df["Low"].tolist(),
        "close": df["Close"].tolist(),
        "volume": df["Volume"].tolist(),
    }

    return render(request, "scanner_dashboard/chart.html", context)



import plotly.graph_objects as go

def sector_ma_chart(request):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["TICKER", "Date"])

    sector_tickers = [
        "XLF","XLK","XLV","XLE","XLI",
        "XLY","XLP","XLB","XLRE","XLU","XLC"
    ]

    df = df[df["TICKER"].isin(sector_tickers)]

    # 21 day moving average (better for 1 year dataset)
    df["MA21"] = (
        df.groupby("TICKER")["Close"]
        .transform(lambda x: x.rolling(21).mean())
    )

    df = df.dropna(subset=["MA21"])

    # Normalize to 100 at first value
    df["normalized"] = (
        df.groupby("TICKER")["MA21"]
        .transform(lambda x: x / x.iloc[0] * 100)
    )

    fig = go.Figure()

    for ticker, g in df.groupby("TICKER"):
        fig.add_trace(
            go.Scatter(
                x=g["Date"],
                y=g["normalized"],
                mode="lines",
                name=ticker
            )
        )

    fig.update_layout(
        title="Sector Relative Strength (21D MA Normalized)",
        template="plotly_dark",
        height=700,
        xaxis_title="Date",
        yaxis_title="Relative Strength"
    )

    chart = fig.to_html(full_html=False)

    return render(
        request,
        "scanner_dashboard/sector_chart.html",
        {"chart": chart}
    )



def get_industry_ranking(request):
    """
    Returns a DataFrame with industry ranking vs SPY including:
    - Cumulative normalized return
    - Rank
    - Positions climbed in last 7 and 21 days
    """
    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["TICKER", "Date"])

    # Daily returns
    df["Return"] = df.groupby("TICKER")["Close"].pct_change()

    # SPY returns
    spy_returns = df[df["TICKER"] == "^GSPC"][["Date", "Return"]].rename(columns={"Return": "SPY_Return"})
    df = df.merge(spy_returns, on="Date", how="left")

    # Normalized return
    df["Norm_Return_Raw"] = df["Return"] - df["SPY_Return"]

    # Step 2: Calculate RMSE per TICKER (industry-level or overall)
    rmse = np.sqrt(np.mean(df["Norm_Return_Raw"] ** 2))

    # Step 3: Normalize by RMSE
    df["Norm_Return"] = df["Norm_Return_Raw"] / rmse

    # Aggregate at industry level
    industry_daily = df.groupby(["Date", "Industry"])["Norm_Return"].mean().reset_index()

    # Pivot for rolling calculations
    industry_pivot = industry_daily.pivot(index="Date", columns="Industry", values="Norm_Return").fillna(0)

    # Rolling cumulative returns
    rolling_cum_7 = industry_pivot.rolling(window=7, min_periods=1).sum()
    rolling_cum_21 = industry_pivot.rolling(window=21, min_periods=1).sum()

    # Current cumulative return and rank
    current_cum = industry_pivot.cumsum().iloc[-1]
    current_rank = current_cum.rank(ascending=False, method="min")

    # Safe way to get ranks 7 and 21 days ago
    last_date = industry_pivot.index.max()
    
    def get_closest_date(target_date):
        """Return the closest existing date in the pivot index <= target_date"""
        return industry_pivot.index[industry_pivot.index.get_indexer([target_date], method="ffill")[0]]
    
    date_7d_ago = get_closest_date(last_date - pd.Timedelta(days=7))
    date_21d_ago = get_closest_date(last_date - pd.Timedelta(days=21))

    rank_7d_ago = rolling_cum_7.loc[date_7d_ago].rank(ascending=False, method="min")
    rank_21d_ago = rolling_cum_21.loc[date_21d_ago].rank(ascending=False, method="min")

    # Build final table
    industry_cum = pd.DataFrame({
        "Industry": current_cum.index,
        "Cumulative_Return": current_cum.values,
        "Rank": current_rank.values,
        "Pos_Climbed_7d": rank_7d_ago.values - current_rank.values,
        "Pos_Climbed_21d": rank_21d_ago.values - current_rank.values
    })

    industry_cum = industry_cum.sort_values("Rank")

    ranking_list = industry_cum.to_dict(orient="records")
    return render(
        request,
        "scanner_dashboard/industry_ranking.html",
        {"ranking_list": ranking_list}
    )




def get_equity_ranking(request):
    """
    Returns equity-level ranking vs SPY including:
    - Cumulative normalized return
    - Rank
    - Positions climbed in last 7 and 21 days
    """
    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["TICKER", "Date"])

    # Calculate daily returns
    df["Return"] = df.groupby("TICKER")["Close"].pct_change()

    # Merge SPY returns
    spy_returns = df[df["TICKER"] == "^GSPC"][["Date", "Return"]].rename(columns={"Return": "SPY_Return"})
    df = df.merge(spy_returns, on="Date", how="left")

    # Raw normalized return vs SPY
    df["Norm_Return_Raw"] = df["Return"] - df["SPY_Return"]

    # RMSE normalization (global)
    rmse = np.sqrt(np.mean(df["Norm_Return_Raw"] ** 2))
    df["Norm_Return"] = df["Norm_Return_Raw"] / rmse

    # Pivot to wide format for rolling calculations
    equity_pivot = df.pivot(index="Date", columns="TICKER", values="Norm_Return").fillna(0)

    # Rolling cumulative sums
    rolling_cum_7 = equity_pivot.rolling(window=7, min_periods=1).sum()
    rolling_cum_21 = equity_pivot.rolling(window=21, min_periods=1).sum()

    # Current cumulative return and rank
    current_cum = equity_pivot.cumsum().iloc[-1]
    current_rank = current_cum.rank(ascending=False, method="min")

    last_date = equity_pivot.index.max()
    # Helper to find closest existing date (handles weekends/holidays)
    def get_closest_date(target_date):
        return equity_pivot.index[equity_pivot.index.get_indexer([target_date], method="ffill")[0]]

    date_7d_ago = get_closest_date(last_date - pd.Timedelta(days=7))
    date_21d_ago = get_closest_date(last_date - pd.Timedelta(days=21))

    rank_7d_ago = rolling_cum_7.loc[date_7d_ago].rank(ascending=False, method="min")
    rank_21d_ago = rolling_cum_21.loc[date_21d_ago].rank(ascending=False, method="min")

    # Build final table
    equity_cum = pd.DataFrame({
        "Ticker": current_cum.index,
        "Cumulative_Return": current_cum.values,
        "Rank": current_rank.values,
        "Pos_Climbed_7d": rank_7d_ago.values - current_rank.values,
        "Pos_Climbed_21d": rank_21d_ago.values - current_rank.values
    })

    equity_cum = equity_cum.sort_values("Rank")

    ranking_list = equity_cum.to_dict(orient="records")
    return render(
        request,
        "scanner_dashboard/equity_ranking.html",
        {"ranking_list": ranking_list}
    )


def metrics_view(request):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "all_data.parquet"

    df = pd.read_parquet(data_path)

    # -----------------------------
    # CLEAN COLUMNS
    # -----------------------------
    df.columns = df.columns.str.strip()

    # Normalize ticker column
    if "Ticker" in df.columns:
        df.rename(columns={"Ticker": "TICKER"}, inplace=True)
    elif "ticker" in df.columns:
        df.rename(columns={"ticker": "TICKER"}, inplace=True)

    # -----------------------------
    # FEATURE ENGINEERING
    # -----------------------------
    if "Upper" in df.columns and "Close" in df.columns:
        df["Delta Upper BBand"] = (
            ((df["Upper"] - df["Close"]) / df["Close"]) * 100
        ).round(2)

    if "Lower" in df.columns and "Close" in df.columns:
        df["Delta Lower BBand"] = (
            ((df["Close"] - df["Lower"]) / df["Lower"]) * 100
        ).round(2)

    # -----------------------------
    # COLUMN ORDER (KEEP TICKER FIRST)
    # -----------------------------
    selected_columns = [
        "Date", "TICKER", "perc_change", "Sector", "Industry",
        "ATR_Pct", "Delta Upper BBand", "Delta Lower BBand",
        "slope_k", "slope_d", "ADX", "PLUS_DI", "MINUS_DI",
        "Candle_Type"
    ]

    # keep only available columns safely
    selected_columns = [c for c in selected_columns if c in df.columns]

    df = df[selected_columns]

    # -----------------------------
    # SORTING
    # -----------------------------
    sort_col = request.GET.get("sort")

    if sort_col and sort_col in df.columns:
        df = df.sort_values(by=sort_col, ascending=False)

    # default sort
    else:
        if "PLUS_DI" in df.columns:
            df = df.sort_values(by="PLUS_DI", ascending=False)

    # -----------------------------
    # SEARCH (Ticker)
    # -----------------------------
    search_query = request.GET.get("search")
    highlight_index = None

    if search_query:
        search_query = search_query.upper().strip()

        if "TICKER" in df.columns:
            matches = df[df["TICKER"] == search_query]

            if not matches.empty:
                highlight_index = matches.index[0]

    # -----------------------------
    # FINAL CLEANUP
    # -----------------------------
    df = df.reset_index(drop=True)

    return render(
        request,
        "scanner_dashboard/metrics.html",
        {
            "columns": df.columns.tolist(),
            "rows": df.to_dict(orient="records"),
            "highlight_index": highlight_index,
            "search_query": search_query or ""
        }
    )

def calculate_momentum_strength(request):
    """
    Calculates:
    1. 3-day momentum: 100 * (Current Close / Close 3 days ago)
    2. Intraday strength: ((High - Open) + (Close - Low)) / (2 * (High - Low))

    Returns:
        DataFrame with ticker, date, momentum_3d, intraday_strength
    """
    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"


    df = pd.read_parquet(data_path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["TICKER", "Date"])

    # Close 3 days ago
    df["close_3d"] = df.groupby("TICKER")["Close"].shift(3)

    # Metric 1: 3-day momentum
    df["Momentum_3D"] = 100 * ((df["Close"] / df["close_3d"])) .round(2)

    # Metric 2: Intraday strength
    df["Intraday_Strength"] = (
        ((df["High"] - df["Open"]) + (df["Close"] - df["Low"])) /
        (2 * (df["High"] - df["Low"]))
    ).round(2)

    # Latest date snapshot
    latest_date = df["Date"].max()
    df_latest = df[df["Date"] == latest_date].copy()

    # Remove invalid rows
    df_latest = df_latest.dropna(subset=["Momentum_3D", "Intraday_Strength"])

    # Sort strongest first
    df_latest = df_latest.sort_values("Momentum_3D", ascending=False)

    # Select columns to display
    df_latest = df_latest[
        ["Date","TICKER","Sector","Industry", "Momentum_3D", "Intraday_Strength", "Close", "Volume"]
        
    ].sort_values("Intraday_Strength", ascending=False)
    

    return render(
        request,
        "scanner_dashboard/momentum_strength.html",
        {
            "columns": df_latest.columns.tolist(),
            "rows": df_latest.values.tolist()
        }
    )

def base_breakout_scanner(request):


    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["TICKER", "Date"])    

    df["prev_close"] = df.groupby("TICKER")["Close"].shift(1)

    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - df["prev_close"]).abs()
    tr3 = (df["Low"] - df["prev_close"]).abs()

    df["TR"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # -----------------------------
    # ATR(15)
    # -----------------------------
    df["ATR_15"] = (
        df.groupby("TICKER")["TR"]
        .transform(lambda x: x.rolling(15, min_periods=15).mean())
    )

    # -----------------------------
    # 14 BAR HIGH / LOW
    # -----------------------------
    df["low_14"] = (
        df.groupby("TICKER")["Low"]
        .transform(lambda x: x.rolling(14, min_periods=14).min())
    )

    df["high_14"] = (
        df.groupby("TICKER")["High"]
        .transform(lambda x: x.rolling(14, min_periods=14).max())
    )

    # -----------------------------
    # WAVE LEVELS
    # -----------------------------
    df["up_wave"] = (df["low_14"] + 3 * df["ATR_15"]).round(2)
    df["down_wave"] = (df["high_14"] - 3 * df["ATR_15"]).round(2)

    # -----------------------------
    # CROSS CONDITIONS
    # -----------------------------
    prev_close = df.groupby("TICKER")["Close"].shift(1)

    df["up_wave_trigger"] = (
        (df["Close"] >= df["up_wave"]) &
        (prev_close < df["up_wave"])
    )

    df["down_wave_trigger"] = (
        (df["Close"] <= df["down_wave"]) &
        (prev_close > df["down_wave"])
    )

    # -----------------------------
    # WAVE TYPE
    # -----------------------------
    df["wave_type"] = None
    df.loc[df["up_wave_trigger"], "wave_type"] = "Up-Wave"
    df.loc[df["down_wave_trigger"], "wave_type"] = "Down-Wave"

    # -----------------------------
    # KEEP ONLY TRIGGERS
    # -----------------------------
    trigger_rows = df[df["wave_type"].notna()]

    # -----------------------------
    # LAST 3 MONTHS
    # -----------------------------
    last_3_months = df["Date"].max() - pd.Timedelta(days=1)

    result = trigger_rows[trigger_rows["Date"] >= last_3_months]

    result = result[
        ["Date", "TICKER","Close", "up_wave", "down_wave", "wave_type"]
    ]

    result = result.sort_values(["wave_type"])

    return render(
        request,
        "scanner_dashboard/base_breakout_scanner.html",
        {
            "columns": result.columns.tolist(),
            "rows": result.values.tolist(),
        },
    )


def breakout_21_view(request):
    
    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["TICKER", "Date"])

    results = []

    for ticker, g in df.groupby("TICKER"):

        g = g.tail(60).copy()  # small optimization

        if len(g) < 25:
            continue

        base = g.iloc[-22:-1]  # 21-day base
        today = g.iloc[-1]

        base_high = base["High"].max()

        # highs within 2% of base high
        highs_near_top = base[base["High"] >= base_high * 0.98]

        if len(highs_near_top) < 2:
            continue

        avg_vol = base["Volume"].mean()

        breakout = (
            (today["High"] > base_high) and
            (today["Volume"] >= 1.5 * avg_vol)
        )

        if breakout:

            results.append({
                "Breakout_Date": today["Date"],
                "TICKER": ticker,
                "Sector": today.get("Sector"),
                "Industry": today.get("Industry"),
                "Breakout_Price": today["Close"],
                "Base_High": base_high,
                "Volume": today["Volume"],
                "Avg_Volume": avg_vol
            })

    results_df = pd.DataFrame(results)

    return render(
        request,
        "scanner_dashboard/breakout_21.html",
        {
            "columns": results_df.columns.tolist(),
            "rows": results_df.values.tolist(),
        },
    )



def industry_weekly_view(request):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "weekly_latest.parquet"

    # ✅ Load latest weekly data (your saved output)
    df = pd.read_parquet(data_path)

    df = df[["Date", "TICKER", "perc_change", "Industry"]]

    df = df[~df["Industry"].str.contains("ETF", na=False)].copy()

    # Ensure clean datetime
    df["Date"] = pd.to_datetime(df["Date"])

    # ✅ Direction logic
    df["direction"] = df["perc_change"].apply(lambda x: "UP" if x > 0 else "DOWN")

    # ✅ Industry aggregation
    grouped = (
        df.groupby(["Industry", "direction"])
        .size()
        .unstack(fill_value=0)
    )

    # Ensure columns exist
    grouped["UP"] = grouped.get("UP", 0)
    grouped["DOWN"] = grouped.get("DOWN", 0)

    # Metrics
    grouped["TOTAL"] = grouped["UP"] + grouped["DOWN"]
    grouped["RATIO"] = grouped["UP"] / grouped["TOTAL"]

    # Sort strongest → weakest industries
    grouped = grouped.sort_values("RATIO", ascending=False).reset_index()

    return render(
        request,
        "scanner_dashboard/industry_weekly.html",
        {
            "data": grouped.to_dict(orient="records")
        }
    )


import pandas as pd
from pathlib import Path
from django.shortcuts import render

def industry_detail_view_change(request, industry_name):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "weekly_history.parquet"

    df = pd.read_parquet(data_path)

    df = df[[
        "Date", "TICKER", "perc_change",
        "Volume", "Industry"
    ]]

    df["Date"] = pd.to_datetime(df["Date"])

    # ----------------------------
    # FILTER INDUSTRY
    # ----------------------------
    df = df[df["Industry"] == industry_name].copy()

    # ----------------------------
    # GET LAST 2 WEEKS
    # ----------------------------
    dates = sorted(df["Date"].unique())

    if len(dates) < 2:
        return render(request, "scanner_dashboard/industry_detail.html", {
            "industry": industry_name,
            "rows": []
        })

    latest_date = dates[-1]
    prev_date = dates[-2]

    current_week = df[df["Date"] == latest_date].copy()
    prev_week = df[df["Date"] == prev_date].copy()

    # ----------------------------
    # CURRENT WEEK DATA
    # ----------------------------
    current_perf = current_week[[
        "TICKER", "perc_change", "Volume"
    ]].copy()

    current_perf = current_perf.rename(columns={
        "perc_change": "weekly_return",
        "Volume": "current_volume"
    })

    # ----------------------------
    # PREVIOUS WEEK DATA
    # ----------------------------
    prev_perf = prev_week[[
        "TICKER", "Volume"
    ]].copy()

    prev_perf = prev_perf.rename(columns={
        "Volume": "prev_volume"
    })

    # ----------------------------
    # MERGE CURRENT + PREVIOUS
    # ----------------------------
    final_df = current_perf.merge(prev_perf, on="TICKER", how="left")

    final_df["prev_volume"] = final_df["prev_volume"].fillna(0)

    # ----------------------------
    # VOLUME CHANGE
    # ----------------------------
    final_df["volume_change"] = (
        final_df["current_volume"] - final_df["prev_volume"]
    )

    final_df["volume_pct_change"] = (
        final_df["volume_change"] /
        final_df["prev_volume"].replace(0, 1)
    ) * 100

    # ----------------------------
    # OPTIONAL (for UI consistency)
    # ----------------------------
    final_df["avg_volume"] = final_df["current_volume"]
    final_df["total_volume"] = final_df["current_volume"]

    # ----------------------------
    # SORT
    # ----------------------------
    final_df = final_df.sort_values("weekly_return", ascending=False)

    # ----------------------------
    # RETURN
    # ----------------------------
    return render(
        request,
        "scanner_dashboard/industry_detail.html",
        {
            "industry": industry_name,
            "rows": final_df.to_dict(orient="records")
        }
    )


###FUNDAMENTALS

import pandas as pd
from pathlib import Path
from django.shortcuts import render


def format_human(x):
    if pd.isna(x):
        return "-"

    abs_x = abs(x)

    if abs_x >= 1e9:
        return f"{x/1e9:.2f}B"
    elif abs_x >= 1e6:
        return f"{x/1e6:.2f}M"
    elif abs_x >= 1e3:
        return f"{x/1e3:.2f}K"
    else:
        return f"{x:.2f}"



def fundamentals_view(request):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "finviz_fundamentals.parquet"

    df = pd.read_parquet(data_path)

    # -----------------------------
    # CLEAN COLUMNS
    # -----------------------------
    df.columns = df.columns.str.strip()

    # Normalize ticker column
    if "Ticker" in df.columns:
        df.rename(columns={"Ticker": "TICKER"}, inplace=True)
    elif "ticker" in df.columns:
        df.rename(columns={"ticker": "TICKER"}, inplace=True)

    # -----------------------------
    # MOVE TICKER FIRST
    # -----------------------------
    columns = df.columns.tolist()
    if "TICKER" in columns:
        columns.remove("TICKER")
        columns.insert(0, "TICKER")

    df = df[columns]

    # -----------------------------
    # SORTING
    # -----------------------------
    sort_col = request.GET.get("sort")

    if sort_col and sort_col in df.columns:
        df = df.sort_values(by=sort_col, ascending=False)

    # -----------------------------
    # SEARCH (Ticker)
    # -----------------------------
    search_query = request.GET.get("search")  # keep consistent with HTML
    highlight_index = None

    if search_query:
        search_query = search_query.upper().strip()

        if "TICKER" in df.columns:
            matches = df[df["TICKER"] == search_query]

            if not matches.empty:
                highlight_index = matches.index[0]

    # -----------------------------
    # FINAL CLEANUP
    # -----------------------------
    df = df.reset_index(drop=True)
    display_df = df.copy()

    cols_to_format = ["Market Cap", "Income", "Sales", "Shs Float"]

    for col in cols_to_format:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_human)

    return render(
        request,
        "scanner_dashboard/fundamentals.html",
        {
            "columns": display_df.columns.tolist(),
            "rows": display_df.to_dict(orient="records"),
            "highlight_index": highlight_index,
            "search_query": search_query or ""
        }
    )


###RELATIVE STRENGTH PLOT




def industry_rs_view(request):

    df = pd.read_parquet(settings.DATA_DIR / "industry_rs.parquet")

    # -----------------------------
    # REMOVE ETF INDUSTRIES
    # -----------------------------
    df = df[~df["Industry"].str.contains("ETF", case=False, na=False)]

    df = df.sort_values("RS_SCORE", ascending=False)

    return render(
        request,
        "scanner_dashboard/industry_rs.html",
        {
            "columns": df.columns.tolist(),
            "rows": df.to_dict("records")
        }
    )



#INDUSTRY DETAILED


from scanner.relative_strength import get_industry_relative_strength

from pathlib import Path
import pandas as pd


import pandas as pd
from pathlib import Path
from django.shortcuts import render
from urllib.parse import unquote


def industry_detail_view(request, industry_name):

    industry_name = unquote(industry_name)

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "industry_ticker_rs.parquet"

    df = pd.read_parquet(data_path)

    # filter industry
    df = df[df["Industry"] == industry_name].copy()

    # safety check
    if "RS_SCORE" not in df.columns:
        raise Exception("RS_SCORE missing. Re-run scanner pipeline.")

    # sort by strength
    df = df.sort_values("RS_SCORE", ascending=False)

    columns = [
        "TICKER",
        "RS_7",
        "RS_21",
        "RS_50",
        "RS_100",
        "RS_200",
        "RS_SCORE"
    ]

    # keep only existing columns
    columns = [c for c in columns if c in df.columns]

    return render(
        request,
        "scanner_dashboard/industry_detail_rs.html",
        {
            "industry": industry_name,
            "columns": columns,
            "rows": df[columns].to_dict("records")
        }
    )

import plotly.express as px

def rs_alignment_dashboard(request):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "rs_alignment.parquet"

    df = pd.read_parquet(data_path)

    # -----------------------------
    # REMOVE INDEX / MACRO SECTORS
    # -----------------------------
    remove_sectors = [
        "Momentum ",
        "DOW JONES",
        "NASDAQ",
        "NYSE",
        "IWM",
        "VOLATILITY",
        "10 YEAR TREASURY",
        "FEAR INDEX"
    ]

    df = df[~df["Sector"].isin(remove_sectors)]

    sector_list = df["Sector"].unique()

    color_palette = px.colors.qualitative.Dark24  # best built-in for many categories

    # Map sectors → colors
    color_map = {
        sector: color_palette[i % len(color_palette)]
        for i, sector in enumerate(sector_list)
}

    # -----------------------------
    # DEFAULT TIMEFRAME = 21
    # -----------------------------
    period = int(request.GET.get("period", 21))

    rs_col = f"RS_{period}"
    align_col = f"ALIGN_{period}"

    # drop missing
    df = df.dropna(subset=[rs_col, align_col])

    fig = px.scatter(
        df,
        x=rs_col,
        y=align_col,
        color="Sector",
        color_discrete_map=color_map,   # 👈 KEY LINE
        hover_name="TICKER",
        hover_data=["Industry"],
        title=f"RS vs Alignment ({period}-Day)",
        width=1200,
        height=800
    )

    # reference lines
    fig.add_vline(x=1, line_dash="dash")
    fig.add_hline(y=period/2, line_dash="dash")

    fig.update_traces(marker=dict(size=8, opacity=0.75))

    chart = fig.to_html(full_html=False)

    return render(request, "scanner_dashboard/rs_alignment_dashboard.html", {
        "chart": chart,
        "period": period
    })

#LBR

def sector_lbr_view(request):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)
    df["Date"] = pd.to_datetime(df["Date"])

    # -----------------------------
    # SECTOR ETFs ONLY
    # -----------------------------
    SECTOR_ETFS = [
        "^GSPC","XLK","XLV","XLF","XLY","XLP",
        "XLE","XLI","XLB","XLRE","XLU","XLC"
    ]

    df = df[df["TICKER"].isin(SECTOR_ETFS)].copy()

    # -----------------------------
    # SELECT ETF
    # -----------------------------
    selected_etf = request.GET.get("etf", "^GSPC")

    df = df[df["TICKER"] == selected_etf].copy()
    df = df.sort_values("Date")

    # -----------------------------
    # LAST N DAYS
    # -----------------------------
    days = int(request.GET.get("days", 60))
    df = df.tail(days)

    # -----------------------------
    # PLOT
    # -----------------------------
    fig = go.Figure()

    # ROC line
    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["ROC2"],
        mode="lines",
        name="ROC(2)",
        line=dict(color="black", width=2)
    ))

    # BUY (blue)
    fig.add_trace(go.Scatter(
        x=df.loc[df["buy_day"], "Date"],
        y=df.loc[df["buy_day"], "ROC2"],
        mode="markers",
        name="Sell Signal",
        marker=dict(
            size=10,
            color="blue",
            symbol="circle"
        )
    ))

    # SELL (pink)
    fig.add_trace(go.Scatter(
        x=df.loc[df["sell_day"], "Date"],
        y=df.loc[df["sell_day"], "ROC2"],
        mode="markers",
        name="Buy Signal",
        marker=dict(
            size=10,
            color="hotpink",
            symbol="circle"
        )
    ))

    # zero line
    fig.add_hline(y=0, line_dash="dash")

    fig.update_layout(
        title=f"{selected_etf} - ROC(2) + LBR Signals",
        xaxis_title="Date",
        yaxis_title="ROC(2)",
        height=700
    )

    chart = fig.to_html(full_html=False)

    return render(request, "scanner_dashboard/sector_lbr.html", {
        "chart": chart,
        "etfs": SECTOR_ETFS,
        "selected_etf": selected_etf,
        "days": days
    })



from pathlib import Path
import pandas as pd
from django.shortcuts import render


def industry_today_detail(request, industry_name):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)

    df = df[[
        "Date", "TICKER", "perc_change",
        "Volume", "Industry"
    ]]

    df["Date"] = pd.to_datetime(df["Date"])

    # ----------------------------
    # FILTER INDUSTRY
    # ----------------------------
    df = df[df["Industry"] == industry_name].copy()

    # ----------------------------
    # GET LAST 2 DAYS
    # ----------------------------
    dates = sorted(df["Date"].unique())

    if len(dates) < 2:
        return render(request, "scanner_dashboard/industry_detail.html", {
            "industry": industry_name,
            "rows": []
        })

    latest_date = dates[-1]
    prev_date = dates[-2]

    today_df = df[df["Date"] == latest_date].copy()
    prev_df = df[df["Date"] == prev_date].copy()

    # ----------------------------
    # TODAY DATA
    # ----------------------------
    current_perf = today_df[[
        "TICKER", "perc_change", "Volume"
    ]].copy()

    current_perf = current_perf.rename(columns={
        "perc_change": "daily_return",
        "Volume": "current_volume"
    })

    # ----------------------------
    # PREVIOUS DAY DATA
    # ----------------------------
    prev_perf = prev_df[[
        "TICKER", "Volume"
    ]].copy()

    prev_perf = prev_perf.rename(columns={
        "Volume": "prev_volume"
    })

    # ----------------------------
    # MERGE
    # ----------------------------
    final_df = current_perf.merge(prev_perf, on="TICKER", how="left")

    final_df["prev_volume"] = final_df["prev_volume"].fillna(0)

    # ----------------------------
    # VOLUME CHANGE
    # ----------------------------
    final_df["volume_change"] = (
        final_df["current_volume"] - final_df["prev_volume"]
    )

    final_df["volume_pct_change"] = (
        final_df["volume_change"] /
        final_df["prev_volume"].replace(0, 1)
    ) * 100

    # ----------------------------
    # UI CONSISTENCY (same as weekly)
    # ----------------------------
    final_df["avg_volume"] = final_df["current_volume"]
    final_df["total_volume"] = final_df["current_volume"]

    # ----------------------------
    # SORT
    # ----------------------------
    final_df = final_df.sort_values("daily_return", ascending=False)

    # ----------------------------
    # RETURN
    # ----------------------------
    return render(
        request,
        "scanner_dashboard/industry_today_detail.html",
        {
            "industry": industry_name,
            "rows": final_df.to_dict(orient="records"),
            "date": latest_date
        }
    )

# views.py

from pathlib import Path
import pandas as pd
from django.shortcuts import render


def industry_today_view(request):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)

    df = df[["Date", "TICKER", "perc_change", "Industry"]]

    # Remove ETFs (same as weekly)
    df = df[~df["Industry"].str.contains("ETF", na=False)].copy()

    # Ensure datetime
    df["Date"] = pd.to_datetime(df["Date"])

    # ----------------------------
    # GET LATEST DATE ONLY
    # ----------------------------
    latest_date = df["Date"].max()
    df = df[df["Date"] == latest_date]

    # ----------------------------
    # UP / DOWN LOGIC
    # ----------------------------
    df["direction"] = df["perc_change"].apply(
        lambda x: "UP" if x > 0 else "DOWN"
    )

    # ----------------------------
    # INDUSTRY AGGREGATION
    # ----------------------------
    grouped = (
        df.groupby(["Industry", "direction"])
        .size()
        .unstack(fill_value=0)
    )

    # Ensure columns exist
    grouped["UP"] = grouped.get("UP", 0)
    grouped["DOWN"] = grouped.get("DOWN", 0)

    # ----------------------------
    # METRICS
    # ----------------------------
    grouped["TOTAL"] = grouped["UP"] + grouped["DOWN"]
    grouped["RATIO"] = grouped["UP"] / grouped["TOTAL"].replace(0, 1)

    # Sort strongest → weakest
    grouped = grouped.sort_values("RATIO", ascending=False).reset_index()

    return render(
        request,
        "scanner_dashboard/industry_today.html",
        {
            "data": grouped.to_dict(orient="records"),
            "date": latest_date
        }
    )




from pathlib import Path
import pandas as pd
from django.shortcuts import render


def ma_structure_view(request):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)

    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df = df.sort_values(["TICKER", "Date"])

    # ----------------------------
    # MOVING AVERAGES (FULL HISTORY)
    # ----------------------------
    for ma in [10, 21, 34, 50, 100, 200]:
        df[f"MA_{ma}"] = df.groupby("TICKER")["Close"].transform(
            lambda x: x.rolling(ma).mean()
        )

    # ----------------------------
    # LATEST + PREVIOUS SNAPSHOT
    # ----------------------------
    all_dates = sorted(df["Date"].unique())

    latest_date = all_dates[-1]
    prev_date = all_dates[-2] if len(all_dates) > 1 else None

    latest_df = df[df["Date"] == latest_date].copy()
    prev_df = df[df["Date"] == prev_date].copy() if prev_date else pd.DataFrame()

    # ----------------------------
    # CLEAN LATEST DATA
    # ----------------------------
    latest_df = latest_df.dropna(subset=[
        "MA_10", "MA_21", "MA_34", "MA_50", "MA_100", "MA_200"
    ])

    # ----------------------------
    # CLASSIFICATION LOGIC
    # ----------------------------
    def classify(row):
        ma10 = row["MA_10"]
        ma21 = row["MA_21"]
        ma34 = row["MA_34"]
        ma50 = row["MA_50"]
        ma100 = row["MA_100"]
        ma200 = row["MA_200"]

        if ma10 > ma21 > ma34 > ma50 > ma100 > ma200:
            return "MA10 > ALL", ma21, "MA21"

        elif ma21 >= ma10 > ma34:
            return "MA10: 21–34", ma34, "MA34"

        elif ma34 >= ma10 > ma50:
            return "MA10: 34–50", ma50, "MA50"

        elif ma50 >= ma10 > ma100:
            return "MA10: 50–100", ma100, "MA100"

        elif ma100 >= ma10 > ma200:
            return "MA10: 100–200", ma200, "MA200"

        else:
            return "MA10 < 200", ma200, "MA200"

    # ----------------------------
    # APPLY CLASSIFICATION (LATEST)
    # ----------------------------
    latest_df[["group", "base_value", "base_label"]] = latest_df.apply(
        lambda r: pd.Series(classify(r)),
        axis=1
    )

    # ----------------------------
    # APPLY CLASSIFICATION (PREV ONLY FOR COMPARISON)
    # ----------------------------
    if not prev_df.empty:
        prev_df[["group", "_", "__"]] = prev_df.apply(
            lambda r: pd.Series(classify(r)),
            axis=1
        )

        prev_map = prev_df[["TICKER", "group"]].rename(
            columns={"group": "prev_group"}
        )

        latest_df = latest_df.merge(prev_map, on="TICKER", how="left")
    else:
        latest_df["prev_group"] = latest_df["group"]

    latest_df["prev_group"] = latest_df["prev_group"].fillna(latest_df["group"])

    # ----------------------------
    # MOVEMENT (ONLY REAL CHANGES)
    # ----------------------------
    rank = {
        "MA10 > ALL": 5,
        "MA10: 21–34": 4,
        "MA10: 34–50": 3,
        "MA10: 50–100": 2,
        "MA10: 100–200": 1,
        "MA10 < 200": 0
    }

    def movement(row):
        if row["group"] == row["prev_group"]:
            return ""
        return "⬆" if rank[row["group"]] > rank[row["prev_group"]] else "⬇"

    latest_df["move"] = latest_df.apply(movement, axis=1)

    # ----------------------------
    # DISTANCE FROM BASE
    # ----------------------------
    latest_df["pct_distance"] = (
        (latest_df["MA_10"] - latest_df["base_value"]) / latest_df["base_value"]
    ) * 100

    # ----------------------------
    # GROUP ORDER SORT (IMPORTANT FIX)
    # ----------------------------
    group_order = {
        "MA10 > ALL": 0,
        "MA10: 21–34": 1,
        "MA10: 34–50": 2,
        "MA10: 50–100": 3,
        "MA10: 100–200": 4,
        "MA10 < 200": 5
    }

    latest_df["group_rank"] = latest_df["group"].map(group_order)

    latest_df = latest_df.sort_values(
        ["group_rank", "pct_distance"],
        ascending=[True, False]
    )

    # ----------------------------
    # VIEW MODE
    # ----------------------------
    view_mode = request.GET.get("view", "group")
    industry_filter = request.GET.get("industry")

    # ----------------------------
    # APPLY INDUSTRY FILTER FIRST (CRITICAL)
    # ----------------------------
    if industry_filter:
        latest_df = latest_df[latest_df["Industry"] == industry_filter]

    # ----------------------------
    # SORT BY GROUP ORDER
    # ----------------------------
    latest_df["group_rank"] = latest_df["group"].map(group_order)

    latest_df = latest_df.sort_values(
        ["group_rank", "pct_distance"],
        ascending=[True, False]
    )

    # ----------------------------
    # VIEW MODE LOGIC
    # ----------------------------
    if view_mode == "industry":
        grouped_data = {
            ind: grp.to_dict("records")
            for ind, grp in latest_df.groupby("Industry")
        }
    else:
        grouped_data = {
            g: latest_df[latest_df["group"] == g].to_dict("records")
            for g in group_order.keys()
        }

    # ----------------------------
    # RETURN
    # ----------------------------
    return render(
        request,
        "scanner_dashboard/ma_structure.html",
        {
            "rows": latest_df.to_dict("records"),
            "groups": grouped_data,
            "date": latest_date,
            "view_mode": view_mode
        }
    )

def documentation(request):
    return render(request, "scanner_dashboard/documentation.html")







