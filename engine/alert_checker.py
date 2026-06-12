
import yaml
import json
import numpy as np
from datetime import datetime
from engine.paths import get_config_path, get_alerts_path

def load_config():
    with open(get_config_path()) as f:
        return yaml.safe_load(f)

def load_alerts():
    with open(get_alerts_path()) as f:
        return json.load(f)

def save_alerts(alerts):
    with open(get_alerts_path(), "w") as f:
        json.dump(alerts, f, indent=2)

def calc_distance(current, level):
    return round((current - level) / level * 100, 2)

def check_crossed(prev, current, level):
    return (prev < level <= current) or (current <= level < prev)

def check_price_alert(data, alert, cfg):
    current = data["current_price"]
    prev    = data["prev_close"]
    level   = alert["level"]
    crossed = cfg.get("crossed_alert_detection", True)
    hit     = check_crossed(prev, current, level) if crossed else (current >= level)
    return hit, calc_distance(current, level)

def check_volume_alert(data, alert, cfg):
    spike     = data["vol_spike_short"]
    threshold = alert.get("volume_factor", cfg["volume"]["spike_strong"])
    if spike is None or np.isnan(spike):
        return False, None
    return spike >= threshold, round(spike, 2)

def check_proximity_warning(data, alert, cfg):
    current   = data["current_price"]
    level     = alert["level"]
    zone_pct  = cfg["alert_zone_percent"]
    vol_spike = data["vol_spike_short"]
    vol_warn  = cfg["volume"]["spike_warning"]
    distance  = abs(calc_distance(current, level))
    in_zone   = distance <= zone_pct
    vol_ok    = (vol_spike is not None and
                 not np.isnan(vol_spike) and
                 vol_spike >= vol_warn)
    return in_zone and vol_ok, round(distance, 2), round(vol_spike, 2) if vol_ok else None

def check_trendline_alert(data, alert, cfg):
    try:
        from engine.trendline import get_trendline_value
        hist     = data["history"]
        current  = data["current_price"]
        prev     = data["prev_close"]
        vol      = data["vol_spike_short"]
        v_factor = alert.get("volume_factor", cfg["volume"]["trendline_volume_factor"])
        tl_value = get_trendline_value(alert, hist)
        if tl_value is None:
            return False, None, None
        breakout = (current > tl_value) and (prev <= tl_value)
        vol_ok   = (vol is not None and not np.isnan(vol) and vol >= v_factor)
        hit      = breakout and vol_ok
        return hit, round(tl_value, 2), round(calc_distance(current, tl_value), 2)
    except:
        return False, None, None

def run_alert_check(market_data):
    cfg      = load_config()
    alerts   = load_alerts()
    now      = datetime.now()
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%Y-%m-%d")

    triggered = []
    warnings  = []
    to_delete = {}

    PRICE_TYPES = {"Price","Support","Resistance","Breakout",
                   "Breakdown","GapFill","52WeekHigh","52WeekLow","Custom"}

    for stock, alert_list in alerts.items():
        data = market_data.get(stock)
        if data is None:
            print(f"⚠️  No data for {stock} — skipping")
            continue

        for idx, alert in enumerate(alert_list):
            atype = alert["type"]
            hit   = False
            meta  = {}

            if atype in PRICE_TYPES:
                hit, distance = check_price_alert(data, alert, cfg)
                meta = {"distance": distance}
            elif atype == "VolumeSpike":
                hit, spike = check_volume_alert(data, alert, cfg)
                meta = {"vol_spike": spike}
            elif atype in {"TrendlineBreak","TrendlineBreakout","TrendlineBreakdown"}:
                hit, tl_val, distance = check_trendline_alert(data, alert, cfg)
                meta = {"trendline_value": tl_val, "distance": distance}
            else:
                print(f"⚠️  Unknown alert type [{atype}] for {stock}")
                continue

            if hit:
                triggered.append({
                    "date"          : date_str,
                    "time"          : time_str,
                    "stock"         : stock,
                    "alert_type"    : atype,
                    "alert_level"   : alert.get("level", meta.get("trendline_value")),
                    "current_price" : data["current_price"],
                    "distance"      : meta.get("distance", 0),
                    "volume"        : data["current_vol"],
                    "vol_spike"     : data["vol_spike_short"]
                })
                if stock not in to_delete:
                    to_delete[stock] = []
                to_delete[stock].append(idx)

            elif atype in PRICE_TYPES:
                warn, dist, spike = check_proximity_warning(data, alert, cfg)
                if warn:
                    warnings.append({
                        "stock"         : stock,
                        "alert_type"    : atype,
                        "alert_level"   : alert["level"],
                        "current_price" : data["current_price"],
                        "distance"      : dist,
                        "vol_spike"     : spike
                    })

    for stock, indices in to_delete.items():
        for idx in sorted(indices, reverse=True):
            del alerts[stock][idx]
        if len(alerts[stock]) == 0:
            del alerts[stock]
            print(f"🗑️  {stock} — all alerts triggered, removed")
        else:
            print(f"🗑️  {stock} — {len(indices)} deleted, {len(alerts[stock])} remaining")

    save_alerts(alerts)
    print(f"\n📊 Check complete — Triggered: {len(triggered)} | Warnings: {len(warnings)}\n")
    return triggered, warnings
