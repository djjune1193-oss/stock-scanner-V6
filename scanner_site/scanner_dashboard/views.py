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

    df = df[df["TICKER"].notna()]
    df = df[df["TICKER"] != ""]

    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
    today = df["Date"].max()

    today_df = df[df["Date"] == today].copy()

    mhi = build_market_health_indicator()
    scanner_status = get_scan_status()

    up_count = (today_df["perc_change"] > 0).sum()
    down_count = (today_df["perc_change"] < 0).sum()
    flat_count = (today_df["perc_change"] == 0).sum()

    # Index
    index_tickers = ["^IXIC", "^GSPC", "^RUT", "^VIX"]
    index_df = today_df[today_df["TICKER"].isin(index_tickers)]

    index_values = {}

    for _, row in index_df.iterrows():
        key_map = {
            "^IXIC": "IXIC",
            "^GSPC": "GSPC",
            "^RUT": "RUT",
            "^VIX": "VIX"
        }

        key = key_map[row["TICKER"]]

        index_values[key] = {
            "close": round(row["Close"], 2),
            "pct": round(row["perc_change"], 2)
        }

    selected_columns = [
        "Date","TICKER","perc_change","Sector","Industry",
        "Close","Open","High","Low","Volume"
    ]

    table_df = today_df[selected_columns].sort_values("Volume", ascending=False)

    remove = ["^GSPC","^DJI","^NYA","^RUT","^VIX","^TNX","^TYX","^IXIC"]
    table_df = table_df[~table_df["TICKER"].isin(remove)]

    table_df["Date"] = table_df["Date"].dt.date

    # 🔥 ADD COLOR LOGIC
    def get_row_class(pct):
        if pct >= 4:
            return "dark-green"
        elif pct > 0:
            return "light-green"
        elif pct <= -4:
            return "dark-red"
        elif pct < 0:
            return "light-red"
        return ""

    rows = []
    for _, r in table_df.iterrows():
        rows.append({
            "Date": r["Date"],
            "TICKER": r["TICKER"],
            "perc_change": r["perc_change"],
            "Sector": r["Sector"],
            "Industry": r["Industry"],
            "Close": r["Close"],
            "Open": r["Open"],
            "High": r["High"],
            "Low": r["Low"],
            "Volume": r["Volume"],
            "row_class": get_row_class(r["perc_change"])
        })

    return render(request, "scanner_dashboard/home.html", {
        "scanner_status": scanner_status,
        "columns": selected_columns,
        "rows": rows,
        "mhi": mhi,
        "index_values": index_values,
        "up_count": int(up_count),
        "down_count": int(down_count),
        "flat_count": int(flat_count),
    })


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
#        (df["slope_d"] > 0) &
        (df["lower_count"] > 0)
    )

    scanner_df = df[row_condition].copy()
    selected_columns = ["Date","TICKER","perc_change","Sector","Industry", "Close", "Open", "High", "Low", "Volume",  "Candle_Type","slope_50","lower_count"]
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
    selected_columns = ["Date","TICKER","perc_change","Sector","Industry", "Close", "Open", "High", "Low", "Volume",  "Candle_Type","slope_Lower", "delta_upper", "lower_count"]
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
    selected_columns = ["Date","TICKER","perc_change","Sector","Industry", "Close", "Open", "High", "Low", "Volume",  "Candle_Type","slope_Lower", "delta_upper", "lower_count" ]
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

    BASE_DIR = Path(__file__).resolve().parents[2]

    latest_path = BASE_DIR / "scanner_site" / "data" / "all_data.parquet"
    history_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    latest_df = pd.read_parquet(latest_path).reset_index()
    history_df = pd.read_parquet(history_path)

    # =========================================
    # DATE CLEANING
    # =========================================

    latest_df["Date"] = pd.to_datetime(latest_df["Date"])
    history_df["Date"] = pd.to_datetime(history_df["Date"])

    history_df = history_df.sort_values(["TICKER", "Date"])

    # =========================================
    # ETF FILTER
    # =========================================

    row_condition = (
        latest_df["Industry"].str.contains("ETF", na=False)
    )

    sector_df = latest_df[row_condition].copy()

    # =========================================
    # TABLE DATA
    # =========================================

    selected_columns = [
        "Date",
        "TICKER",
        "perc_change",
        "Sector",
        "Industry",
        "Close",
        "Open",
        "High",
        "Low",
        "Volume"
    ]

    sector_df = sector_df[selected_columns]

    sector_df = sector_df.sort_values(
        "Volume",
        ascending=False
    ).reset_index(drop=True)

    sector_df["Date"] = sector_df["Date"].dt.date

    # =========================================
    # HISTOGRAM DATA FROM FULL_HISTORY
    # =========================================

    etf_tickers = sector_df["TICKER"].unique()

    hist_df = history_df[
        history_df["TICKER"].isin(etf_tickers)
    ].copy()

    hist_df["ret_5d"] = (
        hist_df.groupby("TICKER")["Close"]
        .pct_change(5) * 100
    )

    hist_df["ret_21d"] = (
        hist_df.groupby("TICKER")["Close"]
        .pct_change(21) * 100
    )

    latest_hist = (
        hist_df.sort_values("Date")
        .groupby("TICKER")
        .tail(1)
        .copy()
    )

    latest_hist = latest_hist.sort_values(
        "ret_5d",
        ascending=False
    )

    # =========================================
    # 5 DAY HISTOGRAM
    # =========================================

    import plotly.graph_objects as go

    fig_5d = go.Figure()

    fig_5d.add_trace(
        go.Bar(
            x=latest_hist["TICKER"],
            y=latest_hist["ret_5d"],
            text=latest_hist["ret_5d"].round(1),
            textposition="outside"
        )
    )

    fig_5d.update_layout(
        template="plotly_dark",
        height=500,
        title="Sector ETF 5-Day Return (%)",
        margin=dict(l=20, r=20, t=60, b=40),
        xaxis_title="ETF",
        yaxis_title="% Return"
    )

    chart_5d = fig_5d.to_html(full_html=False)

    # =========================================
    # 21 DAY HISTOGRAM
    # =========================================

    latest_hist = latest_hist.sort_values(
        "ret_21d",
        ascending=False
    )

    fig_21d = go.Figure()

    fig_21d.add_trace(
        go.Bar(
            x=latest_hist["TICKER"],
            y=latest_hist["ret_21d"],
            text=latest_hist["ret_21d"].round(1),
            textposition="outside"
        )
    )

    fig_21d.update_layout(
        template="plotly_dark",
        height=500,
        title="Sector ETF 21-Day Return (%)",
        margin=dict(l=20, r=20, t=60, b=40),
        xaxis_title="ETF",
        yaxis_title="% Return"
    )

    chart_21d = fig_21d.to_html(full_html=False)

    return render(
        request,
        "scanner_dashboard/sector.html",
        {
            "columns": sector_df.columns.tolist(),
            "rows": sector_df.values.tolist(),
            "chart_5d": chart_5d,
            "chart_21d": chart_21d,
        }
    )


from plotly.subplots import make_subplots

def futures_view(request):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["TICKER", "Date"])

    # =============================
    # DAILY % CHANGE
    # =============================

    df["Prev_Close"] = df.groupby("TICKER")["Close"].shift(1)

    df["Pct_Change"] = (
        (df["Close"] - df["Prev_Close"])
        / df["Prev_Close"]
    ) * 100

    latest_change = (
        df.sort_values("Date")
          .groupby("TICKER")
          .tail(1)[["TICKER", "Pct_Change"]]
    )

    change_map = dict(
        zip(
            latest_change["TICKER"],
            latest_change["Pct_Change"]
        )
    )

    display_change = {}

    for k, v in change_map.items():

        clean_key = (
            k.replace("=", "")
             .replace("^", "")
             .replace("-", "")
        )

        try:
            display_change[clean_key] = round(float(v), 2)
        except:
            display_change[clean_key] = 0

    # =============================
    # FUTURES GROUPS
    # =============================

    groups = {
        "Equities": ["ES=F","NQ=F","YM=F","RTY=F"],
        "Bonds": ["ZB=F","ZN=F","ZF=F","ZT=F"],
        "Metals": ["GC=F","SI=F","HG=F","PL=F","PA=F"],
        "Energy": ["CL=F","NG=F","RB=F","HO=F","BZ=F"],
        "Agriculture": ["ZC=F","ZS=F","ZM=F","ZL=F","KE=F"],
        "Softs": ["CC=F","KC=F","CT=F","SB=F","OJ=F"],
        "Livestock": ["LE=F","HE=F","GF=F"]
    }

    ordered_tickers = [
        t for g in groups.values() for t in g
    ]

    df = df[df["TICKER"].isin(ordered_tickers)]

    # =============================
    # SUBPLOT TITLES
    # =============================

    ticker_sector_map = (
        df.groupby("TICKER")["Sector"]
        .first()
        .to_dict()
    )

    subplot_titles = [
        ticker_sector_map.get(t, "Unknown")
        for t in ordered_tickers
    ]

    # =============================
    # GRID
    # =============================

    cols = 4
    rows = (len(ordered_tickers) + cols - 1) // cols

    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=subplot_titles,
        shared_xaxes=True,
        vertical_spacing=0.03,
        horizontal_spacing=0.03
    )

    # =============================
    # CHARTS
    # =============================

    for i, ticker in enumerate(ordered_tickers):

        g = df[df["TICKER"] == ticker]

        if g.empty:
            continue

        r = i // cols + 1
        c = i % cols + 1

        fig.add_trace(
            go.Scatter(
                x=g["Date"],
                y=g["Close"],
                mode="lines",
                line=dict(width=1),
                name=g["Sector"].iloc[0],
                showlegend=False
            ),
            row=r,
            col=c
        )

    fig.update_layout(
        height=300 * rows,
        title="Futures Price Dashboard",
        template="plotly_dark"
    )

    chart = fig.to_html(full_html=False)

    return render(
        request,
        "scanner_dashboard/futures.html",
        {
            "chart": chart,
            "display_change": display_change
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
                available_cols = [c for c in new_order if c in df.columns]
                df = df[available_cols]

                # -----------------------------
                # FORMAT DATES (IMPORTANT FIX)
                # -----------------------------
                date_cols = ["signal_date", "neckline_date", "L1_date", "L2_date"]

                for col in date_cols:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d")

    except Exception as e:
        print("Double bottom load error:", e)
        df = pd.DataFrame(columns=new_order)

    return render(
        request,
        "scanner_dashboard/double_bottom.html",
        {
            "columns": df.columns.tolist(),
            "rows": df.to_dict(orient="records"),
        }
    )



def turtle_soup_view(request):

    BASE_DIR = Path(__file__).resolve().parents[2]

    data_path = (
        BASE_DIR
        / "scanner_site"
        / "data"
        / "full_history.parquet"
    )

    df = pd.read_parquet(data_path)

    df["Date"] = pd.to_datetime(df["Date"])

    df = df.sort_values(
        ["TICKER", "Date"]
    )

    # =========================================
    # STOCH(7,10,4)
    # =========================================

    df["pmin"] = (
        df.groupby("TICKER")["Low"]
        .transform(lambda x: x.rolling(7).min())
    )

    df["pmax"] = (
        df.groupby("TICKER")["High"]
        .transform(lambda x: x.rolling(7).max())
    )

    df["fast_stoch"] = 100 * (
        (df["Close"] - df["pmin"]) /
        (df["pmax"] - df["pmin"])
    )

    df["k"] = (
        df.groupby("TICKER")["fast_stoch"]
        .transform(lambda x: x.rolling(4).mean())
    )

    df["d"] = (
        df.groupby("TICKER")["k"]
        .transform(lambda x: x.rolling(10).mean())
    )

    df["K_slope"] = (
        df.groupby("TICKER")["k"]
        .diff()
    )

    df["D_slope"] = (
        df.groupby("TICKER")["d"]
        .diff()
    )

    # =========================================
    # ORIGINAL TURTLE SOUP LOGIC
    # =========================================

    df["opposite_slope"] = (
        ((df["K_slope"] > 0) & (df["D_slope"] < 0)) |
        ((df["K_slope"] < 0) & (df["D_slope"] > 0))
    )

    df["opposite_3days"] = (
        df.groupby("TICKER")["opposite_slope"]
        .transform(
            lambda x:
            x.shift(1).rolling(3).sum() == 3
        )
    )

    df["K_up_today"] = (
        df["K_slope"] > 0
    )

    df["K_down_yesterday"] = (
        df.groupby("TICKER")["K_slope"]
        .shift(1) < 0
    )

    # =========================================
    # TODAY ONLY
    # =========================================

    latest_date = df["Date"].max()

    today_df = df[
        df["Date"] == latest_date
    ].copy()

    # =========================================
    # FINAL SCANNER FILTER
    # =========================================

    row_condition = (
        (today_df["opposite_3days"] == True) &
        (today_df["K_up_today"] == True) &
        (today_df["K_down_yesterday"] == True) &
        (today_df["D_slope"] > 0)
    )

    scanner_df = today_df[
        row_condition
    ].copy()

    # =========================================
    # TABLE COLUMNS
    # =========================================

    selected_columns = [
        "Date",
        "TICKER",
        "perc_change",
        "Sector",
        "Industry",
        "Close",
        "k",
        "d",
        "K_slope",
        "D_slope",
        "Volume"
    ]

    scanner_df = scanner_df[
        selected_columns
    ]

    # =========================================
    # SORTING
    # =========================================

    sort_col = request.GET.get(
        "sort",
        "perc_change"
    )

    if sort_col in scanner_df.columns:

        scanner_df = scanner_df.sort_values(
            by=sort_col,
            ascending=False
        )

    # =========================================
    # TABLE DATA
    # =========================================

    results = (
        scanner_df
        .round(2)
        .to_dict("records")
    )

    # =========================================
    # CHART
    # =========================================

    selected_ticker = request.GET.get(
        "ticker",
        "^GSPC"
    )

    chart_df = (
        df[df["TICKER"] == selected_ticker]
        .sort_values("Date")
        .tail(120)
        .copy()
    )

    chart = None

    if not chart_df.empty:

        from plotly.subplots import make_subplots
        import plotly.graph_objects as go

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3]
        )

        # =====================================
        # PRICE
        # =====================================

        fig.add_trace(
            go.Scatter(
                x=chart_df["Date"],
                y=chart_df["Close"],
                mode="lines",
                name="Close",
                line=dict(
                    color="white",
                    width=2
                )
            ),
            row=1,
            col=1
        )

        # =====================================
        # K LINE
        # =====================================

        fig.add_trace(
            go.Scatter(
                x=chart_df["Date"],
                y=chart_df["k"],
                mode="lines",
                name="%K",
                line=dict(
                    color="#22c55e",
                    width=2
                )
            ),
            row=2,
            col=1
        )

        # =====================================
        # D LINE
        # =====================================

        fig.add_trace(
            go.Scatter(
                x=chart_df["Date"],
                y=chart_df["d"],
                mode="lines",
                name="%D",
                line=dict(
                    color="#ef4444",
                    width=2
                )
            ),
            row=2,
            col=1
        )

        # =====================================
        # 20 / 80 LEVELS
        # =====================================

        fig.add_hline(
            y=80,
            line_dash="dash",
            line_color="#9ca3af",
            opacity=0.6,
            row=2,
            col=1
        )

        fig.add_hline(
            y=20,
            line_dash="dash",
            line_color="#9ca3af",
            opacity=0.6,
            row=2,
            col=1
        )

        # =====================================
        # LAYOUT
        # =====================================

        fig.update_layout(

            template="plotly_dark",

            height=700,

            paper_bgcolor="#111827",
            plot_bgcolor="#111827",

            margin=dict(
                l=30,
                r=30,
                t=40,
                b=30
            ),

            title=f"{selected_ticker}",

            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        fig.update_xaxes(
            showgrid=False
        )

        fig.update_yaxes(
            title_text="Price",
            row=1,
            col=1,
            gridcolor="rgba(255,255,255,0.05)"
        )

        fig.update_yaxes(
            title_text="Stoch",
            range=[0, 100],
            row=2,
            col=1,
            gridcolor="rgba(255,255,255,0.05)"
        )

        chart = fig.to_html(
            full_html=False
        )

    return render(
        request,
        "scanner_dashboard/turtle_soup.html",
        {
            "data": results,
            "chart": chart,
            "selected_ticker": selected_ticker,
            "sort_col": sort_col
        }
    )


def stochastic_short_view(request):

    BASE_DIR = Path(__file__).resolve().parents[2]

    data_path = (
        BASE_DIR
        / "scanner_site"
        / "data"
        / "full_history.parquet"
    )

    df = pd.read_parquet(data_path)

    df["Date"] = pd.to_datetime(df["Date"])

    df = df.sort_values(
        ["TICKER", "Date"]
    )

    # =========================================
    # STOCH(7,10,4)
    # =========================================

    df["pmin"] = (
        df.groupby("TICKER")["Low"]
        .transform(lambda x: x.rolling(7).min())
    )

    df["pmax"] = (
        df.groupby("TICKER")["High"]
        .transform(lambda x: x.rolling(7).max())
    )

    df["fast_stoch"] = 100 * (
        (df["Close"] - df["pmin"]) /
        (df["pmax"] - df["pmin"])
    )

    df["k"] = (
        df.groupby("TICKER")["fast_stoch"]
        .transform(lambda x: x.rolling(4).mean())
    )

    df["d"] = (
        df.groupby("TICKER")["k"]
        .transform(lambda x: x.rolling(10).mean())
    )

    df["K_slope"] = (
        df.groupby("TICKER")["k"]
        .diff()
    )

    df["D_slope"] = (
        df.groupby("TICKER")["d"]
        .diff()
    )

    # =========================================
    # ORIGINAL TURTLE SOUP LOGIC
    # =========================================

    df["opposite_slope"] = (
        ((df["K_slope"] > 0) & (df["D_slope"] < 0)) |
        ((df["K_slope"] < 0) & (df["D_slope"] > 0))
    )

    df["opposite_3days"] = (
        df.groupby("TICKER")["opposite_slope"]
        .transform(
            lambda x:
            x.shift(1).rolling(3).sum() == 3
        )
    )

    df["K_up_today"] = (
        df["K_slope"] > 0
    )

    df["K_down_yesterday"] = (
        df.groupby("TICKER")["K_slope"]
        .shift(1) < 0
    )

    # =========================================
    # TODAY ONLY
    # =========================================

    latest_date = df["Date"].max()

    today_df = df[
        df["Date"] == latest_date
    ].copy()

    # =========================================
    # FINAL SCANNER FILTER
    # =========================================

    row_condition = (
        (today_df["opposite_3days"] == True) &
        (today_df["K_up_today"] == False) &
        (today_df["K_down_yesterday"] == False) &
        (today_df["D_slope"] < 0)
    )

    scanner_df = today_df[
        row_condition
    ].copy()

    # =========================================
    # TABLE COLUMNS
    # =========================================

    selected_columns = [
        "Date",
        "TICKER",
        "perc_change",
        "Sector",
        "Industry",
        "Close",
        "k",
        "d",
        "K_slope",
        "D_slope",
        "Volume"
    ]

    scanner_df = scanner_df[
        selected_columns
    ]

    # =========================================
    # SORTING
    # =========================================

    sort_col = request.GET.get(
        "sort",
        "perc_change"
    )

    if sort_col in scanner_df.columns:

        scanner_df = scanner_df.sort_values(
            by=sort_col,
            ascending=False
        )

    # =========================================
    # TABLE DATA
    # =========================================

    results = (
        scanner_df
        .round(2)
        .to_dict("records")
    )

    # =========================================
    # CHART
    # =========================================

    selected_ticker = request.GET.get(
        "ticker",
        "^GSPC"
    )

    chart_df = (
        df[df["TICKER"] == selected_ticker]
        .sort_values("Date")
        .tail(120)
        .copy()
    )

    chart = None

    if not chart_df.empty:

        from plotly.subplots import make_subplots
        import plotly.graph_objects as go

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3]
        )

        # =====================================
        # PRICE
        # =====================================

        fig.add_trace(
            go.Scatter(
                x=chart_df["Date"],
                y=chart_df["Close"],
                mode="lines",
                name="Close",
                line=dict(
                    color="white",
                    width=2
                )
            ),
            row=1,
            col=1
        )

        # =====================================
        # K LINE
        # =====================================

        fig.add_trace(
            go.Scatter(
                x=chart_df["Date"],
                y=chart_df["k"],
                mode="lines",
                name="%K",
                line=dict(
                    color="#22c55e",
                    width=2
                )
            ),
            row=2,
            col=1
        )

        # =====================================
        # D LINE
        # =====================================

        fig.add_trace(
            go.Scatter(
                x=chart_df["Date"],
                y=chart_df["d"],
                mode="lines",
                name="%D",
                line=dict(
                    color="#ef4444",
                    width=2
                )
            ),
            row=2,
            col=1
        )

        # =====================================
        # 20 / 80 LEVELS
        # =====================================

        fig.add_hline(
            y=80,
            line_dash="dash",
            line_color="#9ca3af",
            opacity=0.6,
            row=2,
            col=1
        )

        fig.add_hline(
            y=20,
            line_dash="dash",
            line_color="#9ca3af",
            opacity=0.6,
            row=2,
            col=1
        )

        # =====================================
        # LAYOUT
        # =====================================

        fig.update_layout(

            template="plotly_dark",

            height=700,

            paper_bgcolor="#111827",
            plot_bgcolor="#111827",

            margin=dict(
                l=30,
                r=30,
                t=40,
                b=30
            ),

            title=f"{selected_ticker} ",

            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        fig.update_xaxes(
            showgrid=False
        )

        fig.update_yaxes(
            title_text="Price",
            row=1,
            col=1,
            gridcolor="rgba(255,255,255,0.05)"
        )

        fig.update_yaxes(
            title_text="Stoch",
            range=[0, 100],
            row=2,
            col=1,
            gridcolor="rgba(255,255,255,0.05)"
        )

        chart = fig.to_html(
            full_html=False
        )

    return render(
        request,
        "scanner_dashboard/stochastic_short.html",
        {
            "data": results,
            "chart": chart,
            "selected_ticker": selected_ticker,
            "sort_col": sort_col
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

    sector_names = {
        "XLF": "Financials",
        "XLK": "Technology",
        "XLV": "Healthcare",
        "XLE": "Energy",
        "XLI": "Industrials",
        "XLY": "Consumer Discretionary",
        "XLP": "Consumer Staples",
        "XLB": "Materials",
        "XLRE": "Real Estate",
        "XLU": "Utilities",
        "XLC": "Communication"
    }

    df = df[df["TICKER"].isin(sector_tickers)].copy()

    # =====================================================
    # ORIGINAL RELATIVE STRENGTH CHART
    # =====================================================

    df["MA21"] = (
        df.groupby("TICKER")["Close"]
        .transform(lambda x: x.rolling(21).mean())
    )

    df = df.dropna(subset=["MA21"])

    df["normalized"] = (
        df.groupby("TICKER")["MA21"]
        .transform(lambda x: x / x.iloc[0] * 100)
    )

    import plotly.graph_objects as go

    fig_main = go.Figure()

    for ticker, g in df.groupby("TICKER"):

        fig_main.add_trace(
            go.Scatter(
                x=g["Date"],
                y=g["normalized"],
                mode="lines",
                name=ticker
            )
        )

    fig_main.update_layout(
        title="Sector Relative Strength (21D MA Normalized)",
        template="plotly_dark",
        height=700,
        xaxis_title="Date",
        yaxis_title="Relative Strength",
        margin=dict(l=20, r=20, t=50, b=20)
    )

    chart = fig_main.to_html(full_html=False)

    # =====================================================
    # 5D + 21D RETURNS
    # =====================================================

    latest_rows = []

    for ticker in sector_tickers:

        g = (
            df[df["TICKER"] == ticker]
            .sort_values("Date")
            .tail(30)
            .copy()
        )

        if len(g) < 22:
            continue

        latest_close = g["Close"].iloc[-1]

        close_5d = g["Close"].iloc[-6]
        close_21d = g["Close"].iloc[-22]

        ret_5d = ((latest_close / close_5d) - 1) * 100
        ret_21d = ((latest_close / close_21d) - 1) * 100

        latest_rows.append({
            "Ticker": ticker,
            "Return_5D": round(ret_5d, 2),
            "Return_21D": round(ret_21d, 2)
        })

    perf_df = pd.DataFrame(latest_rows)

    # =====================================================
    # 5D HISTOGRAM
    # =====================================================

    fig_5d = go.Figure()

    fig_5d.add_trace(go.Bar(
        x=perf_df["Ticker"],
        y=perf_df["Return_5D"],
        text=perf_df["Return_5D"],
        textposition="outside"
    ))

    fig_5d.update_layout(
        template="plotly_dark",
        height=450,
        title="Sector ETF Returns — Last 5 Trading Days",
        yaxis_title="% Return",
        xaxis_title="Sector ETF",
        margin=dict(l=20, r=20, t=50, b=20)
    )

    chart_5d = fig_5d.to_html(full_html=False)

    # =====================================================
    # 21D HISTOGRAM
    # =====================================================

    fig_21d = go.Figure()

    fig_21d.add_trace(go.Bar(
        x=perf_df["Ticker"],
        y=perf_df["Return_21D"],
        text=perf_df["Return_21D"],
        textposition="outside"
    ))

    fig_21d.update_layout(
        template="plotly_dark",
        height=450,
        title="Sector ETF Returns — Last 21 Trading Days",
        yaxis_title="% Return",
        xaxis_title="Sector ETF",
        margin=dict(l=20, r=20, t=50, b=20)
    )

    chart_21d = fig_21d.to_html(full_html=False)

    return render(
        request,
        "scanner_dashboard/sector_chart.html",
        {
            "chart": chart,
            "chart_5d": chart_5d,
            "chart_21d": chart_21d
        }
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

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["TICKER", "Date"])

    # -----------------------------
    # RETURNS
    # -----------------------------
    df["Return"] = df.groupby("TICKER")["Close"].pct_change()

    spy = (
        df[df["TICKER"] == "^GSPC"][["Date", "Return"]]
        .rename(columns={"Return": "SPY_Return"})
    )

    df = df.merge(spy, on="Date", how="left")

    df["RS_Daily"] = df["Return"] - df["SPY_Return"]

    rmse = np.sqrt(np.mean(df["RS_Daily"] ** 2))
    df["RS_Normalized"] = df["RS_Daily"] / rmse

    # -----------------------------
    # RS MULTI TIMEFRAME
    # -----------------------------
    for period in [7, 21, 50, 100, 200]:
        df[f"RS_{period}"] = df.groupby("TICKER")["RS_Normalized"].transform(
            lambda x: x.rolling(period).mean()
        )

    # -----------------------------
    # CUMULATIVE (RAW SCORE, NOT %)
    # -----------------------------
    df["Cumulative_Return"] = df.groupby("TICKER")["RS_Normalized"].cumsum()

    latest_date = df["Date"].max()
    latest_df = df[df["Date"] == latest_date].copy()

    # -----------------------------
    # RS SCORE
    # -----------------------------
    latest_df["RS_SCORE"] = (
        0.30 * latest_df["RS_7"] +
        0.25 * latest_df["RS_21"] +
        0.20 * latest_df["RS_50"] +
        0.15 * latest_df["RS_100"] +
        0.10 * latest_df["RS_200"]
    )

    latest_df = latest_df.dropna(subset=[
        "RS_SCORE", "RS_7", "RS_21", "RS_50", "RS_100", "RS_200"
    ])

    # -----------------------------
    # SORT CONTROL (NEW)
    # -----------------------------
    sort_by = request.GET.get("sort", "cumulative")
    sort_dir = request.GET.get("dir", "desc")

    ascending = False if sort_dir == "desc" else True

    if sort_by == "rs":
        latest_df = latest_df.sort_values("RS_SCORE", ascending=ascending)
    elif sort_by == "ticker":
        latest_df = latest_df.sort_values("Ticker", ascending=ascending)
    else:
        latest_df = latest_df.sort_values("Cumulative_Return", ascending=ascending)

    # -----------------------------
    # FINAL OUTPUT
    # -----------------------------
    ranking_list = latest_df[[
        "TICKER",
        "RS_SCORE",
        "Cumulative_Return",
        "RS_7",
        "RS_21",
        "RS_50",
        "RS_100",
        "RS_200"
    ]].rename(columns={"TICKER": "Ticker"}).to_dict("records")

    return render(
        request,
        "scanner_dashboard/equity_ranking.html",
        {
            "ranking_list": ranking_list,
            "date": latest_date,
            "sort_by": sort_by,
            "sort_dir": sort_dir
        }
    )

def metrics_view(request):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "all_data.parquet"

    df = pd.read_parquet(data_path)

    # -----------------------------
    # CLEAN COLUMNS
    # -----------------------------

    df.columns = df.columns.str.strip()

    if "Ticker" in df.columns:
        df.rename(columns={"Ticker": "TICKER"}, inplace=True)

    elif "ticker" in df.columns:
        df.rename(columns={"ticker": "TICKER"}, inplace=True)

    # -----------------------------
    # FEATURE ENGINEERING
    # -----------------------------

    if "Upper" in df.columns and "Close" in df.columns:

        df["Delta_Upper_BBand"] = (
            ((df["Upper"] - df["Close"]) / df["Close"]) * 100
        ).round(2)

    if "Lower" in df.columns and "Close" in df.columns:

        df["Delta_Lower_BBand"] = (
            ((df["Close"] - df["Lower"]) / df["Lower"]) * 100
        ).round(2)

    # -----------------------------
    # COLUMN ORDER
    # -----------------------------

    selected_columns = [

        "Date",
        "TICKER",
        "perc_change",
        "Sector",
        "Industry",
        "ATR_Pct",
        "slope_k",
        "slope_d",
        "k",
        "d",
        "ADX",
        "PLUS_DI",
        "MINUS_DI",

        "Candle_Type"

    ]

    selected_columns = [
        c for c in selected_columns if c in df.columns
    ]

    df = df[selected_columns]

    # -----------------------------
    # SORTING
    # -----------------------------

    sort_col = request.GET.get("sort")

    if sort_col and sort_col in df.columns:

        df = df.sort_values(
            by=sort_col,
            ascending=False
        )

    else:

        if "PLUS_DI" in df.columns:

            df = df.sort_values(
                by="PLUS_DI",
                ascending=False
            )

    # -----------------------------
    # SEARCH
    # -----------------------------

    search_query = request.GET.get("search")

    highlight_index = None

    if search_query:

        search_query = search_query.upper().strip()

        matches = df[df["TICKER"] == search_query]

        if not matches.empty:

            highlight_index = matches.index[0]

    # -----------------------------
    # FINAL
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

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["TICKER", "Date"])

    # ----------------------------
    # 3-DAY MOMENTUM
    # ----------------------------
    df["close_3d"] = df.groupby("TICKER")["Close"].shift(3)

    df["Momentum_3D"] = (
        100 * (df["Close"] / df["close_3d"])
    ).round(2)

    # ----------------------------
    # INTRADAY STRENGTH
    # ----------------------------
    df["Intraday_Strength"] = (
        ((df["High"] - df["Open"]) + (df["Close"] - df["Low"])) /
        (2 * (df["High"] - df["Low"]))
    ).round(2)

    # ----------------------------
    # AVG VOLUME (EXCLUDING TODAY)
    # ----------------------------
    df["Avg_Volume"] = (
        df.groupby("TICKER")["Volume"]
        .transform(lambda x: x.shift(1).rolling(3).mean()).round(0)
    )

    # ----------------------------
    # LATEST SNAPSHOT
    # ----------------------------
    latest_date = df["Date"].max()
    df_latest = df[df["Date"] == latest_date].copy()

    # ----------------------------
    # CLEAN FILTERS
    # ----------------------------
    df_latest = df_latest.dropna(
        subset=["Momentum_3D", "Intraday_Strength", "Avg_Volume"]
    )

    # liquidity filter (historical only)
    df_latest = df_latest[df_latest["Avg_Volume"] > 50_000_000]

    # ----------------------------
    # SORT
    # ----------------------------
    df_latest = df_latest.sort_values(
        [ "Intraday_Strength","Momentum_3D"],
        ascending=[False, False]
    )

    # ----------------------------
    # FINAL TABLE
    # ----------------------------
    df_latest = df_latest[
        ["Date", "TICKER", "Sector", "Industry",
         "Momentum_3D", "Intraday_Strength",
         "Close", "Volume", "Avg_Volume"]
    ]

    return render(
        request,
        "scanner_dashboard/momentum_strength.html",
        {
            "columns": df_latest.columns.tolist(),
            "rows": df_latest.to_dict(orient="records"),
            "date": latest_date
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
        .transform(lambda x: x.rolling(15, min_periods=15).mean().round(2))
    )

    # -----------------------------
    # 14 BAR HIGH / LOW
    # -----------------------------
    df["low_14"] = (
        df.groupby("TICKER")["Close"]
        .transform(lambda x: x.rolling(14, min_periods=14).min())
    )

    df["high_14"] = (
        df.groupby("TICKER")["Close"]
        .transform(lambda x: x.rolling(14, min_periods=14).max())
    )

    # -----------------------------
    # WAVE LEVELS
    # -----------------------------
    df["up_wave"] = (df["low_14"] + 2.5 * df["ATR_15"]).round(2)
    df["down_wave"] = (df["high_14"] - 2.5 * df["ATR_15"]).round(2)

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
        ["Date", "TICKER","Close","low_14","high_14","ATR_15", "up_wave", "down_wave", "wave_type"]
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

    data_path = (
        BASE_DIR
        / "scanner_site"
        / "data"
        / "full_history.parquet"
    )

    df = pd.read_parquet(data_path)

    # -----------------------------------
    # CLEAN
    # -----------------------------------

    df["Date"] = pd.to_datetime(df["Date"])

    df = df.sort_values(["TICKER", "Date"])

    results = []

    # -----------------------------------
    # LOOP TICKERS
    # -----------------------------------

    for ticker, g in df.groupby("TICKER"):

        g = g.tail(60).copy()

        if len(g) < 25:
            continue

        # -----------------------------------
        # 21 DAY BASE
        # -----------------------------------

        base = g.iloc[-22:-1]

        today = g.iloc[-1]

        base_high = base["High"].max()

        # -----------------------------------
        # BASE VALIDATION
        # -----------------------------------

        highs_near_top = base[
            base["High"] >= base_high * 0.98
        ]

        if len(highs_near_top) < 2:
            continue

        # -----------------------------------
        # VOLUME
        # -----------------------------------

        avg_vol = round(base["Volume"].mean())

        # -----------------------------------
        # TODAY DIRECTION FILTER
        # ONLY STRONG UP DAYS
        # -----------------------------------

        bullish_today = (
            today["Close"] > today["Open"]
        )

        # -----------------------------------
        # BREAKOUT LOGIC
        # -----------------------------------

        breakout = (

            (today["High"] > base_high) and

            (today["Volume"] >= 1.5 * avg_vol) and

            bullish_today

        )

        # -----------------------------------
        # SAVE RESULT
        # -----------------------------------

        if breakout:

            breakout_pct = round(
                (
                    (today["Close"] - base_high)
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

    # -----------------------------------
    # FINAL DF
    # -----------------------------------

    results_df = pd.DataFrame(results)

    # -----------------------------------
    # SORT
    # -----------------------------------

    if not results_df.empty:

        results_df = results_df.sort_values(
            "Breakout_%",
            ascending=False
        )

    return render(

        request,

        "scanner_dashboard/breakout_21.html",

        {

            "columns":
                results_df.columns.tolist(),

            "rows":
                results_df.values.tolist(),

        },
    )

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
    median_gain = df.groupby("Industry")["perc_change"].median()
    grouped["MEDIAN_GAIN"] = median_gain


    # Sort strongest → weakest industries
    grouped = grouped.sort_values("MEDIAN_GAIN", ascending=False).reset_index()

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

    # =========================================
    # TIMEFRAME (FIXED OPTIONS ONLY)
    # =========================================

    valid_periods = [7, 21, 50, 200]
    period = int(request.GET.get("period", 21))

    if period not in valid_periods:
        period = 21

    rs_col = f"RS_{period}"
    align_col = f"ALIGN_{period}"

    # =========================================
    # CLEAN DATA
    # =========================================

    df = df.dropna(subset=[rs_col, align_col])
    df = df[df[rs_col] > 0]

    # =========================================
    # QUADRANTS
    # =========================================

    strong_df = df[(df[rs_col] >= 1) & (df[align_col] >= period / 2)]
    weak_df = df[(df[rs_col] < 1) & (df[align_col] < period / 2)]
    improving_df = df[(df[rs_col] >= 1) & (df[align_col] < period / 2)]
    weakening_df = df[(df[rs_col] < 1) & (df[align_col] >= period / 2)]

    # =========================================
    # PLOT
    # =========================================

    import plotly.graph_objects as go

    fig = go.Figure()

    def add_trace(data, name, color, size=8, opacity=0.7):
        fig.add_trace(go.Scatter(
            x=data[rs_col],
            y=data[align_col],
            mode="markers",
            name=name,
            text=data["TICKER"],
            customdata=data[["Sector", "Industry"]],
            marker=dict(size=size, color=color, opacity=opacity),
            hovertemplate=
            "<b>%{text}</b><br>" +
            "Sector: %{customdata[0]}<br>" +
            "Industry: %{customdata[1]}<br>" +
            "RS: %{x:.2f}<br>" +
            "Alignment: %{y}<extra></extra>"
        ))

    add_trace(strong_df, "Strong and Positive Corr ", "#22c55e", 10, 0.9)
    add_trace(weak_df, "Weak and Negative Corr", "#ef4444")
    add_trace(improving_df, "Strong and Negative Corr", "#3b82f6")
    add_trace(weakening_df, "Weak and Positive Corr", "#f59e0b")

    fig.add_vline(x=1, line_dash="dash", line_color="white", opacity=0.5)
    fig.add_hline(y=period / 2, line_dash="dash", line_color="white", opacity=0.5)

    fig.update_layout(
        template="plotly_dark",
        height=800,
        paper_bgcolor="#0b1220",
        plot_bgcolor="#0b1220",
        title=f"RS vs Alignment ({period}D)",
        legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center")
    )

    chart = fig.to_html(full_html=False)

    # =========================================
    # QUADRANT TABLE DATA
    # =========================================

    def format_table(df):
        return df[["TICKER", rs_col, align_col, "Sector", "Industry"]].rename(
            columns={
                rs_col: "RS",
                align_col: "ALIGN"
            }
        ).to_dict("records")

    context = {
        "chart": chart,
        "period": period,
        "valid_periods": valid_periods,

        "strong_table": format_table(strong_df),
        "weak_table": format_table(weak_df),
        "improving_table": format_table(improving_df),
        "weakening_table": format_table(weakening_df),

        "counts": {
            "strong": len(strong_df),
            "weak": len(weak_df),
            "improving": len(improving_df),
            "weakening": len(weakening_df),
        }
    }

    return render(request, "scanner_dashboard/rs_alignment_dashboard.html", context)




#LBR

import pandas as pd
from django.shortcuts import render
from pathlib import Path
import plotly.graph_objects as go

def sector_lbr_view(request):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)

    df.columns = df.columns.str.lower()
    df["date"] = pd.to_datetime(df["date"])
    df["ticker"] = df["ticker"].astype(str)

    df = df[df["ticker"].notna()]
    df = df[df["ticker"].str.strip() != ""]
    df = df[df["ticker"].str.lower() != "nan"]

    df = df.sort_values(["ticker", "date"])
    latest_rows = df.groupby("ticker").tail(1)

    signal_df = latest_rows[
        (latest_rows["buy_day"] == True) |
        (latest_rows["sell_day"] == True)
    ].copy()

    total_buys = signal_df["buy_day"].sum()
    total_sells = signal_df["sell_day"].sum()

    # =========================
    # AUTO LOAD ^GSPC
    # =========================
    selected_ticker = request.GET.get("ticker", "^GSPC")

    chart = None

    g = df[df["ticker"] == selected_ticker].copy()
    g = g.sort_values("date").tail(30)

    if not g.empty:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=g["date"],
            y=g["roc2"],
            mode="lines",
            name="ROC(2)",
            line=dict(color="#60a5fa", width=2),
            fill="tozeroy",
            fillcolor="rgba(96,165,250,0.08)"
        ))

        fig.add_trace(go.Scatter(
            x=g.loc[g["buy_day"], "date"],
            y=g.loc[g["buy_day"], "roc2"],
            mode="markers",
            name="Buy",
            marker=dict(size=10, color="#22c55e", symbol="triangle-up")
        ))

        fig.add_trace(go.Scatter(
            x=g.loc[g["sell_day"], "date"],
            y=g.loc[g["sell_day"], "roc2"],
            mode="markers",
            name="Sell",
            marker=dict(size=10, color="#ef4444", symbol="triangle-down")
        ))

        fig.add_hline(y=0, line_dash="dash", line_color="#6b7280")

        fig.update_layout(
            title=f"{selected_ticker} - ROC(2) + LBR Signals",
            template="plotly_dark",
            height=520,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor="#0b1220",
            plot_bgcolor="#0b1220",
            font=dict(color="#e5e7eb"),
            legend=dict(orientation="h", y=1.02)
        )

        fig.update_xaxes(gridcolor="#1f2937")
        fig.update_yaxes(gridcolor="#1f2937")

        chart = fig.to_html(full_html=False)

    table_data = []

    for _, row in signal_df.iterrows():
        table_data.append({
            "ticker": row["ticker"],
            "industry": row.get("industry", "N/A"),
            "volume": int(row["volume"]) if pd.notna(row.get("volume")) else 0,
            "buy_day": row["buy_day"],
            "sell_day": row["sell_day"],
        })

    table_data = sorted(table_data, key=lambda x: x["volume"], reverse=True)

    return render(request, "scanner_dashboard/sector_lbr.html", {
        "chart": chart,
        "data": table_data,
        "total_buys": int(total_buys),
        "total_sells": int(total_sells),
        "selected_ticker": selected_ticker
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
    median_gain = df.groupby("Industry")["perc_change"].median()
    grouped["MEDIAN_GAIN"] = median_gain

    # Sort strongest → weakest
    grouped = grouped.sort_values("MEDIAN_GAIN", ascending=False).reset_index()

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

    # ----------------------------
    # 1. HARD STRUCTURE (TOP PRIORITY)
    # ----------------------------
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

    # ----------------------------
    # 2. STRONG TREND
    # ----------------------------
    	if ma10 >= ma21:

    # perfect structure
    		if ma10 > ma21 > ma34 > ma50 > ma100 > ma200:
        		return "MA10 > ALL (strong)", ma10, "MA10"

    # still above but messy
    		return "MA10 > ALL (weak)", ma10, "MA10"

    # fallback safety
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

    # ----------------------------
    # DISTANCE FROM BASE
    # ----------------------------
    latest_df["pct_distance"] = (
        (latest_df["Close"] - latest_df["base_value"]) / latest_df["base_value"]
    ) * 100

    # ----------------------------
    # GROUP ORDER SORT (IMPORTANT FIX)
    # ----------------------------
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



def keltner_scan(request):

    BASE_DIR = Path(__file__).resolve().parents[2]

    latest_path = BASE_DIR / "scanner_site" / "data" / "keltner_latest.parquet"
    history_path = BASE_DIR / "scanner_site" / "data" / "keltner_history.parquet"

    latest_df = pd.read_parquet(latest_path)
    history_df = pd.read_parquet(history_path)

    latest_df["Date"] = pd.to_datetime(latest_df["Date"])
    history_df["Date"] = pd.to_datetime(history_df["Date"])

    # =====================================
    # SORTING
    # =====================================

    sort_col = request.GET.get("sort", "pct_above_ema")
    sort_dir = request.GET.get("dir", "desc")

    valid_cols = [
        "pct_above_ema",
        "atr_pct",
        "days_above_ema",
        "Close",
        "ema20",
        "kc_upper",
        "kc_lower"
    ]

    if sort_col not in valid_cols:
        sort_col = "pct_above_ema"

    ascending = True if sort_dir == "asc" else False

    latest_df = latest_df.sort_values(
        sort_col,
        ascending=ascending
    )

    # =====================================
    # TABLE DATA
    # =====================================

    results = latest_df[[
        "TICKER",
        "Close",
        "ema20",
        "kc_upper",
        "kc_lower",
        "pct_above_ema",
        "atr_pct",
        "days_above_ema"
    ]].round(2).to_dict("records")

    # =====================================
    # CHART
    # =====================================

    selected_ticker = request.GET.get("ticker", "^GSPC")

    if selected_ticker not in history_df["TICKER"].unique():
        selected_ticker = "^GSPC"

    chart_df = (
        history_df[history_df["TICKER"] == selected_ticker]
        .tail(80)
        .copy()
    )

    chart_data = None

    if not chart_df.empty:

        import plotly.graph_objects as go

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=chart_df["Date"],
            y=chart_df["Close"],
            name="Close",
            line=dict(color="white", width=2)
        ))

        fig.add_trace(go.Scatter(
            x=chart_df["Date"],
            y=chart_df["ema20"],
            name="EMA20",
            line=dict(color="cyan", width=2)
        ))

        fig.add_trace(go.Scatter(
            x=chart_df["Date"],
            y=chart_df["kc_upper"],
            name="KC Upper",
            line=dict(color="red", width=1)
        ))

        fig.add_trace(go.Scatter(
            x=chart_df["Date"],
            y=chart_df["kc_lower"],
            name="KC Lower",
            line=dict(color="lime", width=1)
        ))

        fig.update_layout(
            template="plotly_dark",
            height=450,
            margin=dict(l=10, r=10, t=30, b=10),
            title=f"{selected_ticker} - Keltner Channel"
        )

        chart_data = fig.to_html(full_html=False)

    return render(request, "scanner_dashboard/keltner_scan.html", {
        "data": results,
        "chart": chart_data,
        "selected_ticker": selected_ticker,
        "sort_col": sort_col,
        "sort_dir": sort_dir
    })




def fib_retracement_scan(request):

    BASE_DIR = Path(__file__).resolve().parents[2]
    data_path = BASE_DIR / "scanner_site" / "data" / "full_history.parquet"

    df = pd.read_parquet(data_path)

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["TICKER", "Date"])

    import numpy as np
    import plotly.graph_objects as go

    selected_ticker = request.GET.get("ticker", "^GSPC")
    sort_col = request.GET.get("sort")

    results = []

    # =========================
    # FIB CALCULATION PER TICKER
    # =========================

    for ticker, g in df.groupby("TICKER"):

        g = g.copy()

        high_max = g["High"].max()
        low_min = g["Low"].min()

        # avoid divide-by-zero issues
        denom = (high_max - low_min) if (high_max - low_min) != 0 else 1

        g["retracement"] = ((high_max - g["Close"]) / denom) * 100

        latest = g.iloc[-1]

        results.append({
            "ticker": ticker,
            "Close": round(latest["Close"], 2),
            "high_max": round(high_max, 2),
            "low_min": round(low_min, 2),
            "retracement": round(latest["retracement"], 2),
            "tv_link": f"https://www.tradingview.com/chart/?symbol={ticker}"
        })

    # =========================
    # SORTING (IMPORTANT FIX)
    # =========================

    valid_sort_fields = [
        "ticker",
        "Close",
        "high_max",
        "low_min",
        "retracement"
    ]

    if sort_col in valid_sort_fields:

        # ticker ascending
        if sort_col == "ticker":

            results = sorted(
                results,
                key=lambda x: x.get(sort_col, "")
            )

        # numeric ascending
        else:

            results = sorted(
                results,
                key=lambda x: x.get(sort_col, 0)
            )

    else:

        # DEFAULT SORT = retracement ASCENDING
        results = sorted(
            results,
            key=lambda x: x["retracement"]
        )

    # =========================
    # CHART (DEFAULT ^GSPC OR SWITCHED)
    # =========================

    chart = None
    chart_df = df[df["TICKER"] == selected_ticker].tail(120).copy()

    if not chart_df.empty:

        high_max = chart_df["High"].max()
        low_min = chart_df["Low"].min()

        denom = (high_max - low_min) if (high_max - low_min) != 0 else 1

        # fib levels
        chart_df["fib_0"] = high_max
        chart_df["fib_236"] = high_max - 0.236 * (high_max - low_min)
        chart_df["fib_382"] = high_max - 0.382 * (high_max - low_min)
        chart_df["fib_50"] = high_max - 0.5 * (high_max - low_min)
        chart_df["fib_618"] = high_max - 0.618 * (high_max - low_min)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=chart_df["Date"],
            y=chart_df["Close"],
            name="Close",
            line=dict(color="white", width=2)
        ))

        fig.add_trace(go.Scatter(
            x=chart_df["Date"],
            y=chart_df["fib_236"],
            name="23.6%",
            line=dict(color="green", width=1)
        ))

        fig.add_trace(go.Scatter(
            x=chart_df["Date"],
            y=chart_df["fib_382"],
            name="38.2%",
            line=dict(color="yellow", width=1)
        ))

        fig.add_trace(go.Scatter(
            x=chart_df["Date"],
            y=chart_df["fib_50"],
            name="50%",
            line=dict(color="orange", width=1)
        ))

        fig.add_trace(go.Scatter(
            x=chart_df["Date"],
            y=chart_df["fib_618"],
            name="61.8%",
            line=dict(color="red", width=1)
        ))

        fig.update_layout(
            template="plotly_dark",
            height=450,
            margin=dict(l=10, r=10, t=30, b=10),
            title=f"{selected_ticker} - Fibonacci Retracement"
        )

        chart = fig.to_html(full_html=False)

    # =========================
    # FINAL RETURN
    # =========================

    return render(request, "scanner_dashboard/fib_scan.html", {
        "data": results,
        "chart": chart,
        "selected_ticker": selected_ticker
    })
