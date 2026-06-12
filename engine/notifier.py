
import requests
import yaml
from engine.paths import get_config_path

def load_config():
    with open(get_config_path()) as f:
        return yaml.safe_load(f)

def send_message(text):
    cfg = load_config()
    if not cfg.get("telegram_enabled", False):
        print(f"[TELEGRAM DISABLED] {text}")
        return
    token   = cfg["telegram"]["bot_token"]
    chat_id = cfg["telegram"]["chat_id"]
    url     = f"https://api.telegram.org/bot{token}/sendMessage"
    res     = requests.post(url, json={
        "chat_id"   : chat_id,
        "text"      : text,
        "parse_mode": "HTML"
    })
    if res.status_code != 200:
        print(f"⚠️  Telegram failed: {res.text}")

def send_file(filepath, caption=""):
    cfg = load_config()
    if not cfg.get("telegram_enabled", False):
        print(f"[TELEGRAM DISABLED] File: {filepath}")
        return False
    token   = cfg["telegram"]["bot_token"]
    chat_id = cfg["telegram"]["chat_id"]
    url     = f"https://api.telegram.org/bot{token}/sendDocument"
    with open(filepath, "rb") as f:
        res = requests.post(url,
            data={"chat_id": chat_id, "caption": caption},
            files={"document": f}
        )
    ok = res.status_code == 200
    if not ok:
        print(f"⚠️  File send failed: {res.text}")
    return ok

def fmt_alert_hit(record):
    return (
        f"🔔 <b>ALERT HIT</b>\n\n"
        f"Stock      : <b>{record['stock']}</b>\n"
        f"Type       : {record['alert_type']}\n"
        f"Level      : {record['alert_level']}\n"
        f"Current    : {record['current_price']:.2f}\n"
        f"Distance   : {record['distance']}%\n"
        f"Time       : {record['time']}"
    )

def fmt_proximity_warning(w):
    return (
        f"⚠️ <b>APPROACHING ALERT</b>\n\n"
        f"Stock      : <b>{w['stock']}</b>\n"
        f"Type       : {w['alert_type']}\n\n"
        f"Current    : {w['current_price']:.2f}\n"
        f"Alert      : {w['alert_level']}\n"
        f"Distance   : {w['distance']}%\n"
        f"Vol Spike  : {w['vol_spike']}x"
    )

def fmt_daily_summary(triggered, closest):
    lines = ["📊 <b>ALERTS HIT TODAY</b>\n"]
    if triggered:
        lines.append(f"Total Hits: {len(triggered)}\n")
        for r in triggered:
            lines.append(f"{r['stock']:<12} {r['alert_level']}")
    else:
        lines.append("No alerts triggered today.")
    lines.append("\n📈 <b>CLOSEST ALERTS</b>\n")
    if closest:
        for i, c in enumerate(closest, 1):
            lines.append(
                f"{i}. {c['stock']}\n"
                f"   Current : {c['current_price']:.2f}\n"
                f"   Alert   : {c['alert_level']}\n"
                f"   Distance: {abs(c['distance'])}%\n"
            )
    else:
        lines.append("No active alerts remaining.")
    return "\n".join(lines)

def notify_triggered(triggered):
    for record in triggered:
        send_message(fmt_alert_hit(record))
        print(f"📨 Alert sent : {record['stock']} @ {record['alert_level']}")

def notify_warnings(warnings):
    for w in warnings:
        send_message(fmt_proximity_warning(w))
        print(f"📨 Warning sent : {w['stock']} → {w['alert_level']}")

def notify_daily_summary(triggered, closest):
    send_message(fmt_daily_summary(triggered, closest))
    print("📨 Daily summary sent")
