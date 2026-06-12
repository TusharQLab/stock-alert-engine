
import numpy as np
import pandas as pd
from datetime import datetime

def parse_point(point):
    """Parse a trendline point dict into (date, price)."""
    date  = pd.to_datetime(point["date"])
    price = float(point["price"])
    return date, price

def calc_slope_intercept(p1, p2):
    """
    Calculate slope (m) and intercept (c) for trendline.
    Line equation : price = m * day_number + c
    day_number    : days since p1 date
    """
    date1, price1 = p1
    date2, price2 = p2

    days_diff = (date2 - date1).days
    if days_diff == 0:
        return None, None

    m = (price2 - price1) / days_diff
    c = price1   # price at day 0 (p1)

    return m, c

def get_trendline_value(alert, hist):
    """
    Calculate current trendline value for today.

    alert must have:
        point1 : {"date": "YYYY-MM-DD", "price": float}
        point2 : {"date": "YYYY-MM-DD", "price": float}
    """
    try:
        p1 = parse_point(alert["point1"])
        p2 = parse_point(alert["point2"])

        m, c = calc_slope_intercept(p1, p2)
        if m is None:
            return None

        # Today = last date in history
        today     = hist.index[-1]
        today     = pd.Timestamp(today).tz_localize(None) if today.tzinfo else pd.Timestamp(today)
        base_date = p1[0].tz_localize(None) if p1[0].tzinfo else p1[0]

        days_from_p1 = (today - base_date).days
        tl_value     = c + m * days_from_p1

        return round(tl_value, 2)

    except Exception as e:
        print(f"⚠️  Trendline calc error: {e}")
        return None

def get_trendline_series(alert, hist):
    """
    Return full trendline value series aligned to history index.
    Useful for charting and future backtesting.
    """
    try:
        p1 = parse_point(alert["point1"])
        p2 = parse_point(alert["point2"])

        m, c = calc_slope_intercept(p1, p2)
        if m is None:
            return None

        base_date = p1[0].tz_localize(None) if p1[0].tzinfo else p1[0]
        series    = {}

        for ts in hist.index:
            ts_clean     = pd.Timestamp(ts).tz_localize(None) if ts.tzinfo else pd.Timestamp(ts)
            days         = (ts_clean - base_date).days
            series[ts]   = round(c + m * days, 2)

        return pd.Series(series, name="trendline")

    except Exception as e:
        print(f"⚠️  Trendline series error: {e}")
        return None

def describe_trendline(alert):
    """Print human-readable trendline description."""
    try:
        p1 = parse_point(alert["point1"])
        p2 = parse_point(alert["point2"])
        m, c = calc_slope_intercept(p1, p2)

        direction = "Ascending ↗" if m > 0 else "Descending ↘"
        print(f"   Direction : {direction}")
        print(f"   Slope     : {m:.4f} per day")
        print(f"   Point 1   : {p1[0].date()} @ {p1[1]}")
        print(f"   Point 2   : {p2[0].date()} @ {p2[1]}")
    except Exception as e:
        print(f"⚠️  Trendline describe error: {e}")
