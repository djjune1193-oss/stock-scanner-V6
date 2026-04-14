# scanner/strategies/double_bottom.py

import pandas as pd

def find_swings(df, lookback=5):
    swings = []
    for i in range(lookback, len(df) - lookback):
        low = df['Low'].iloc[i]
        high = df['High'].iloc[i]

        if low == df['Low'].iloc[i-lookback:i+lookback+1].min():
            swings.append((i, 'low'))
        elif high == df['High'].iloc[i-lookback:i+lookback+1].max():
            swings.append((i, 'high'))

    return swings


def detect_double_bottom(df, tolerance=0.02):
    swings = find_swings(df)
    patterns = []

    for i in range(len(swings) - 2):
        idx1, t1 = swings[i]
        idx2, t2 = swings[i + 1]
        idx3, t3 = swings[i + 2]

        if t1 == 'low' and t2 == 'high' and t3 == 'low':
            L1 = df['Low'].iloc[idx1]
            L2 = df['Low'].iloc[idx3]

            if abs(L1 - L2) / L1 <= tolerance:
                patterns.append({
                    'L1_idx': idx1,
                    'L2_idx': idx3,
                    'neckline': df['High'].iloc[idx2],
                    'neckline_idx': idx2,
                    'neckline_date': df.index[idx2]
                })

    return patterns


def detect_breakout_retest(df, patterns, retest_tol=0.01, max_retest_bars=10):
    signals = []

    for p in patterns:
        start = p['L2_idx']
        neckline = p['neckline']

        data = df.iloc[start:].copy()

        breakout = data[data['Close'] > neckline]
        if breakout.empty:
            continue

        breakout_idx = breakout.index[0]
        after_breakout = df.loc[breakout_idx:].iloc[1:max_retest_bars+1]

        retest = after_breakout[
            (after_breakout['Low'] <= neckline * (1 + retest_tol)) &
            (after_breakout['Close'] > neckline)
        ]

        if not retest.empty:
            retest_row = retest.iloc[0]

            signals.append({
                'signal_date': retest_row['Date'],   # ✅ FIX
                'close_price': retest_row['Close'],
                'neckline_price': neckline,
                'neckline_date': df['Date'].iloc[p['neckline_idx']],
                'L1_low': df['Low'].iloc[p['L1_idx']],
                'L2_low': df['Low'].iloc[p['L2_idx']],
                'L1_date': df['Date'].iloc[p['L1_idx']],
                'L2_date': df['Date'].iloc[p['L2_idx']],
            })

    return pd.DataFrame(signals)
