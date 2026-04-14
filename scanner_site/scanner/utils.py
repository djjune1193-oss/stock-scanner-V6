import numpy as np
from scipy.stats import linregress

def slope(series, n):
    y = series.iloc[-n:]
    if len(y) < n or y.isna().any():
        return np.nan
    x = np.arange(len(y))
    return linregress(x, y.values).slope


def streak(series):
    m = series.astype(bool)
    return (
        m.groupby([m, (~m).cumsum().where(m)])
         .cumcount()
         .add(1)
         .mul(m)
    )
