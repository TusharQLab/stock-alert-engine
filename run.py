
import sys
import os
import argparse
import yaml

def get_project_root():
    return os.path.dirname(os.path.abspath(__file__))

def inject_secrets():
    root        = get_project_root()
    config_path = os.path.join(root, "config", "config.yaml")
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    bot_token = os.environ.get("BOT_TOKEN", "")
    chat_id   = os.environ.get("CHAT_ID",   "")
    if bot_token:
        cfg["telegram"]["bot_token"] = bot_token
        cfg["telegram_enabled"]      = True
    if chat_id:
        cfg["telegram"]["chat_id"] = chat_id
    with open(config_path, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)

def mode_scan():
    from engine.data_fetcher  import fetch_market_data
    from engine.alert_checker import run_alert_check
    from engine.history       import append_triggered
    from engine.notifier      import notify_triggered, notify_warnings
    import json, os
    alerts_path = os.path.join(get_project_root(), "config", "alerts.json")
    with open(alerts_path) as f:
        alerts = json.load(f)
    symbols     = list(alerts.keys())
    market_data = fetch_market_data(symbols)
    triggered, warnings = run_alert_check(market_data)
    append_triggered(triggered)
    if triggered: notify_triggered(triggered)
    if warnings:  notify_warnings(warnings)
    print(f"✅ Scan complete — triggered: {len(triggered)}, warnings: {len(warnings)}")

def mode_summary():
    from engine.data_fetcher import fetch_market_data
    from engine.summary      import build_daily_summary, print_summary
    from engine.notifier     import notify_daily_summary
    import json, os
    alerts_path = os.path.join(get_project_root(), "config", "alerts.json")
    with open(alerts_path) as f:
        alerts = json.load(f)
    symbols     = list(alerts.keys())
    market_data = fetch_market_data(symbols)
    summary     = build_daily_summary(market_data)
    print_summary(summary)
    notify_daily_summary(summary["triggered"], summary["closest"])
    print("✅ Summary sent")

def mode_archive():
    from engine.history  import create_monthly_archive
    from engine.notifier import send_file, send_message
    from datetime import datetime
    import os
    now   = datetime.now()
    month = now.month - 1 if now.month > 1 else 12
    year  = now.year      if now.month > 1 else now.year - 1
    print(f"📦 Archiving {year}-{month:02d}...")
    path = create_monthly_archive(year, month)
    root = get_project_root()
    config_path = os.path.join(root, "config", "config.yaml")
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    if path and os.path.exists(path):
        if cfg["archive"]["send_to_telegram"]:
            ok = send_file(path, caption=f"📦 Monthly Archive {year}-{month:02d}")
            if ok and cfg["archive"]["delete_after_send"]:
                os.remove(path)
                print("🗑️  Archive deleted after send")
    else:
        send_message(f"⚠️ No records for {year}-{month:02d}")
    print("✅ Archive complete")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["scan","summary","archive"], default="scan")
    args = parser.parse_args()

    root = get_project_root()
    os.chdir(root)
    sys.path.insert(0, root)

    inject_secrets()

    if   args.mode == "scan":    mode_scan()
    elif args.mode == "summary": mode_summary()
    elif args.mode == "archive": mode_archive()
