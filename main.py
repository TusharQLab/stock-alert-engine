
import sys
sys.path.insert(0, "/content/stock_alert_engine")

import json
import yaml
import importlib
from datetime import datetime

# ── Imports ──────────────────────────────────────────────────
import engine.data_fetcher  as _df
import engine.alert_checker as _ac
import engine.history       as _hi
import engine.notifier      as _no
import engine.summary       as _su

# Force fresh reload every run
for mod in [_df, _ac, _hi, _no, _su]:
    importlib.reload(mod)

from engine.data_fetcher  import fetch_market_data
from engine.alert_checker import run_alert_check
from engine.history       import append_triggered
from engine.notifier      import notify_triggered, notify_warnings, notify_daily_summary
from engine.summary       import build_daily_summary, print_summary

def load_config():
    with open("/content/stock_alert_engine/config/config.yaml") as f:
        return yaml.safe_load(f)

def load_alerts():
    with open("/content/stock_alert_engine/config/alerts.json") as f:
        return json.load(f)

def run_pipeline(mode="normal"):
    """
    Full pipeline:
    1. Load alerts
    2. Fetch market data
    3. Check alerts
    4. Save history
    5. Send Telegram notifications
    6. Build and send daily summary
    """
    cfg  = load_config()
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("=" * 52)
    print("🚀 STOCK ALERT ENGINE — STARTING")
    print(f"   Time : {now}")
    print(f"   Mode : {mode.upper()}")
    print("=" * 52)
    print()

    # ── Step 1 : Load active alerts ──────────────────────────
    alerts  = load_alerts()
    symbols = list(alerts.keys())

    if not symbols:
        print("⚠️  No active alerts found. Exiting.")
        return

    print(f"📋 Active stocks  : {len(symbols)}")
    print(f"📋 Total alerts   : {sum(len(v) for v in alerts.values())}")
    print()

    # ── Step 2 : Fetch market data ───────────────────────────
    market_data = fetch_market_data(symbols)

    # ── Step 3 : Check alerts ────────────────────────────────
    print("🔍 Checking alerts...")
    print()
    triggered, warnings = run_alert_check(market_data)

    # ── Step 4 : Save history ────────────────────────────────
    print("💾 Saving history...")
    append_triggered(triggered)
    print()

    # ── Step 5 : Send Telegram notifications ─────────────────
    print("📨 Sending notifications...")
    if triggered:
        notify_triggered(triggered)
    if warnings:
        notify_warnings(warnings)
    print()

    # ── Step 6 : Build and send daily summary ────────────────
    print("📊 Building summary...")
    summary = build_daily_summary(market_data)
    print_summary(summary)

    # Send summary to Telegram
    notify_daily_summary(summary["triggered"], summary["closest"])
    print()

    print("=" * 52)
    print("✅ PIPELINE COMPLETE")
    print(f"   Triggered : {len(triggered)}")
    print(f"   Warnings  : {len(warnings)}")
    print("=" * 52)

    return {
        "triggered" : triggered,
        "warnings"  : warnings,
        "summary"   : summary
    }


# ── DEMO MODE — force trigger one alert for testing ──────────
def run_demo():
    """
    Demo mode:
    - Temporarily lowers one alert level to current price
    - Runs full pipeline to verify end-to-end flow
    - Restores original alert after test
    """
    import json

    print("🧪 DEMO MODE — Injecting test trigger")
    print()

    alerts_path = "/content/stock_alert_engine/config/alerts.json"

    with open(alerts_path) as f:
        alerts = json.load(f)

    # ── Fetch current price of RELIANCE ──────────────────────
    from engine.data_fetcher import fetch_market_data
    data    = fetch_market_data(["RELIANCE"])
    current = data["RELIANCE"]["current_price"]

    # ── Inject alert at exactly current price ─────────────────
    original_alerts = json.loads(json.dumps(alerts))  # deep copy
    alerts["RELIANCE"].insert(0, {
        "type"  : "Price",
        "level" : round(current, 2)
    })

    with open(alerts_path, "w") as f:
        json.dump(alerts, f, indent=2)

    print(f"   Injected alert : RELIANCE @ {round(current, 2)}")
    print()

    # ── Run full pipeline ─────────────────────────────────────
    result = run_pipeline(mode="demo")

    # ── Restore original alerts ───────────────────────────────
    # Check if demo alert was already deleted by pipeline
    with open(alerts_path) as f:
        current_alerts = json.load(f)

    # Restore from original backup
    with open(alerts_path, "w") as f:
        json.dump(original_alerts, f, indent=2)

    print()
    print("🔁 Original alerts restored")

    return result


# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    run_pipeline()
