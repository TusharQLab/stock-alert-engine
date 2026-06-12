
import json
import sys
import os
sys.path.insert(0, "/content/stock_alert_engine")
from engine.paths import get_alerts_path, get_config_path

def load_alerts():
    with open(get_alerts_path()) as f:
        return json.load(f)

def save_alerts(alerts):
    with open(get_alerts_path(), "w") as f:
        json.dump(alerts, f, indent=2)

# ── View all alerts ──────────────────────────────────────────
def view_alerts():
    alerts = load_alerts()
    if not alerts:
        print("No active alerts.")
        return

    print()
    print("=" * 55)
    print("📋 ACTIVE ALERTS")
    print("=" * 55)
    total = 0
    for stock, alert_list in sorted(alerts.items()):
        print(f"  {stock}")
        for i, a in enumerate(alert_list):
            atype = a["type"]
            level = a.get("level", "—")
            extra = ""
            if atype in {"TrendlineBreak","TrendlineBreakout","TrendlineBreakdown"}:
                p1 = a.get("point1", {})
                p2 = a.get("point2", {})
                extra = f"  [{p1.get('date')} @ {p1.get('price')} → {p2.get('date')} @ {p2.get('price')}]"
            print(f"    [{i}] {atype:<18} {level}{extra}")
            total += 1
        print()
    print(f"  Stocks : {len(alerts)} | Total alerts : {total}")
    print("=" * 55)

# ── Add price-based alert ────────────────────────────────────
def add_alert(stock, alert_type, level):
    """
    Add a simple price/support/resistance alert.
    Example: add_alert("RELIANCE", "Support", 1200)
    """
    alerts = load_alerts()
    stock  = stock.upper().strip()

    if stock not in alerts:
        alerts[stock] = []

    # Check for duplicate
    for a in alerts[stock]:
        if a.get("type") == alert_type and a.get("level") == level:
            print(f"⚠️  Alert already exists: {stock} {alert_type} @ {level}")
            return

    alerts[stock].append({"type": alert_type, "level": level})
    alerts[stock] = sorted(alerts[stock], key=lambda x: x.get("level", 0))
    save_alerts(alerts)
    print(f"✅ Added  : {stock} | {alert_type} @ {level}")

# ── Add trendline alert ──────────────────────────────────────
def add_trendline_alert(stock, alert_type,
                         date1, price1,
                         date2, price2,
                         volume_factor=1.5):
    """
    Add a trendline breakout/breakdown alert.
    Example:
        add_trendline_alert(
            "RELIANCE", "TrendlineBreak",
            "2026-01-01", 1500,
            "2026-03-01", 1400
        )
    """
    alerts = load_alerts()
    stock  = stock.upper().strip()

    if stock not in alerts:
        alerts[stock] = []

    alert = {
        "type"          : alert_type,
        "point1"        : {"date": date1, "price": float(price1)},
        "point2"        : {"date": date2, "price": float(price2)},
        "volume_factor" : volume_factor
    }

    alerts[stock].append(alert)
    save_alerts(alerts)
    print(f"✅ Added trendline : {stock} | {alert_type}")
    print(f"   Point1 : {date1} @ {price1}")
    print(f"   Point2 : {date2} @ {price2}")

# ── Remove alert by index ────────────────────────────────────
def remove_alert(stock, index):
    """
    Remove alert by index number shown in view_alerts().
    Example: remove_alert("RELIANCE", 0)
    """
    alerts = load_alerts()
    stock  = stock.upper().strip()

    if stock not in alerts:
        print(f"⚠️  {stock} not found in alerts")
        return

    if index >= len(alerts[stock]):
        print(f"⚠️  Index {index} out of range for {stock}")
        return

    removed = alerts[stock].pop(index)

    if len(alerts[stock]) == 0:
        del alerts[stock]
        print(f"🗑️  Removed : {stock} [{removed['type']} @ {removed.get('level','trendline')}]")
        print(f"   {stock} has no more alerts — removed from list")
    else:
        save_alerts(alerts)
        print(f"🗑️  Removed : {stock} [{removed['type']} @ {removed.get('level','trendline')}]")
        print(f"   {stock} has {len(alerts[stock])} alert(s) remaining")

    save_alerts(alerts)

# ── Remove entire stock ──────────────────────────────────────
def remove_stock(stock):
    """Remove all alerts for a stock."""
    alerts = load_alerts()
    stock  = stock.upper().strip()

    if stock not in alerts:
        print(f"⚠️  {stock} not found")
        return

    count = len(alerts[stock])
    del alerts[stock]
    save_alerts(alerts)
    print(f"🗑️  Removed all {count} alerts for {stock}")

# ── Summary stats ────────────────────────────────────────────
def alert_stats():
    alerts = load_alerts()
    from collections import Counter
    type_counts = Counter()
    for alert_list in alerts.values():
        for a in alert_list:
            type_counts[a["type"]] += 1

    print()
    print("=" * 40)
    print("📊 ALERT STATISTICS")
    print("=" * 40)
    print(f"  Total stocks : {len(alerts)}")
    print(f"  Total alerts : {sum(len(v) for v in alerts.values())}")
    print()
    print("  By type:")
    for atype, count in type_counts.most_common():
        print(f"    {atype:<20} : {count}")
    print("=" * 40)
