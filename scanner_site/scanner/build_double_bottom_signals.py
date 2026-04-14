import pandas as pd
from pathlib import Path
from .double_bottom import detect_double_bottom, detect_breakout_retest


def build_double_bottom_signals():
    """
    Reads historical stock data, detects double bottom patterns,
    and saves today's signals to a parquet file. All paths are internal.
    """
    # Base directory
    BASE_DIR = Path(__file__).resolve().parents[1]

    # Input data
    data_path = BASE_DIR / "data" / "full_history.parquet"
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    # Read full history
    df = pd.read_parquet(data_path)
    df["Date"] = pd.to_datetime(df["Date"])
    latest_date = df["Date"].max()

    signals = []

    for ticker, g in df.groupby("TICKER"):
        g = g.sort_values("Date").reset_index(drop=True)

        # Detect patterns
        patterns = detect_double_bottom(g)
        signal_df = detect_breakout_retest(g, patterns)

        if signal_df.empty:
            continue

        # Convert date columns
        for col in ["signal_date", "L1_date", "L2_date", "neckline_date"]:
            signal_df[col] = pd.to_datetime(signal_df[col])

        # Filter stale bases
        signal_df = signal_df[signal_df["signal_date"] - signal_df["L2_date"] < pd.Timedelta(days=10)]

        # Add symmetry columns
        signal_df["LHS"] = signal_df["neckline_date"] - signal_df["L1_date"]
        signal_df["RHS"] = signal_df["L2_date"] - signal_df["neckline_date"]
        signal_df["Symmetry"] = signal_df["RHS"] - signal_df["LHS"]

        # Keep only today's signals
        today_signal = signal_df[signal_df["signal_date"] == latest_date]
        if today_signal.empty:
            continue

        row = today_signal.iloc[-1].to_dict()
        row["TICKER"] = ticker
        signals.append(row)

    # Save results
    signals_df = pd.DataFrame(signals)
    out_path = BASE_DIR / "data" / "double_bottom_signals.parquet"
    signals_df.to_parquet(out_path, index=False)

    print(f"Saved {len(signals_df)} signals for {latest_date.date()} -> {out_path}")
