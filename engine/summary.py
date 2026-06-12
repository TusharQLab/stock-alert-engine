
import json
import yaml
import numpy as np
import pandas as pd
from engine.history import load_history, get_todays_triggered
from engine.paths   import get_config_path, get_alerts_path

def load_config():
    with open(get_config_path()) as f:
        return yaml.safe_load(f)

def load_alerts():
    with open(get_alerts_path()) as f:
        return json.load(f)

def get_closest_alerts(market_data):
    cfg    = load_config()
    alerts = load_alerts()
    max_n  = cfg["distance"]["max_alerts_in_summary"]
    rows   = []

    for stock, alert_list in alerts.items():
        data = market_data.get(stock)
        if data is None:
            continue
        current = data["current_price"]
        for alert in alert_list:
            level = alert.get("level")
            if level is None:
                continue
            distance = round((current - level) / level * 100, 2)
            rows.append({
                "stock"        : stock,
                "alert_type"   : alert["type"],
                "alert_level"  : level,
                "current_price": current,
                "distance"     : distance,
                "abs_distance" : abs(distance)
            })

    if not rows:
        return []
    df = pd.DataFrame(rows).sort_values("abs_distance").head(max_n)
    return df.to_dict("records")

def build_daily_summary(market_data):
    return {
        "triggered": get_todays_triggered(),
        "closest"  : get_closest_alerts(market_data)
    }

def print_summary(summary):
    triggered = summary["triggered"]
    closest   = summary["closest"]

    print("=" * 52)
    print("📊 ALERTS HIT TODAY")
    print("=" * 52)
    if triggered:
        print(f"Total Hits: {len(triggered)}\n")
        for r in triggered:
            print(f"  {r['stock']:<12} {r['alert_level']}")
    else:
        print("  No alerts triggered today.")

    print()
    print("=" * 52)
    print("📈 CLOSEST ALERTS")
    print("=" * 52)
    if closest:
        for i, c in enumerate(closest, 1):
            print(f"  {i}. {c['stock']}")
            print(f"     Current  : {c['current_price']:.2f}")
            print(f"     Alert    : {c['alert_level']}")
            print(f"     Distance : {abs(c['distance'])}%")
            print()
    else:
        print("  No active alerts remaining.")
    print("=" * 52)
