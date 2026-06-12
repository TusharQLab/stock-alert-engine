
import os
import yaml
import pandas as pd
from datetime import datetime
from engine.paths import get_config_path, get_history_path_from_cfg, get_archive_folder_from_cfg

def load_config():
    with open(get_config_path()) as f:
        return yaml.safe_load(f)

def load_history():
    path = get_history_path_from_cfg()
    if not os.path.exists(path):
        return pd.DataFrame(columns=[
            "date","time","stock","alert_type",
            "alert_level","current_price","distance","volume","vol_spike"
        ])
    return pd.read_parquet(path)

def save_history(df):
    path = get_history_path_from_cfg()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False)

def append_triggered(triggered):
    if not triggered:
        print("   No new alerts to save.")
        return
    existing = load_history()
    new_rows = pd.DataFrame(triggered)
    new_rows["alert_level"]   = pd.to_numeric(new_rows["alert_level"],   errors="coerce")
    new_rows["current_price"] = pd.to_numeric(new_rows["current_price"], errors="coerce")
    new_rows["distance"]      = pd.to_numeric(new_rows["distance"],      errors="coerce")
    new_rows["volume"]        = pd.to_numeric(new_rows["volume"],        errors="coerce")
    new_rows["vol_spike"]     = pd.to_numeric(new_rows["vol_spike"],     errors="coerce")

    # Fix FutureWarning — drop empty cols before concat
    existing = existing.dropna(axis=1, how="all")
    combined = pd.concat([existing, new_rows], ignore_index=True)
    save_history(combined)
    print(f"   ✅ Saved {len(new_rows)} record(s) — total: {len(combined)}")

def get_todays_triggered():
    df    = load_history()
    today = datetime.now().strftime("%Y-%m-%d")
    return df[df["date"] == today].to_dict("records")

def get_monthly_records(year, month):
    df = load_history()
    df["date"] = pd.to_datetime(df["date"])
    mask = (df["date"].dt.year == year) & (df["date"].dt.month == month)
    return df[mask].copy()

def create_monthly_archive(year, month):
    df = get_monthly_records(year, month)
    if df.empty:
        print(f"   No records for {year}-{month:02d}")
        return None
    folder   = get_archive_folder_from_cfg()
    os.makedirs(folder, exist_ok=True)
    path     = os.path.join(folder, f"alert_history_{year}_{month:02d}.parquet")
    df.to_parquet(path, index=False)
    print(f"   ✅ Archive: {path} ({len(df)} records)")
    return path

def get_statistics():
    df = load_history()
    if df.empty:
        return {"error": "No history available"}
    stats = {
        "total_triggered"  : len(df),
        "by_type"          : df["alert_type"].value_counts().to_dict(),
        "by_stock"         : df["stock"].value_counts().to_dict(),
        "most_active_stock": df["stock"].value_counts().idxmax(),
        "most_common_type" : df["alert_type"].value_counts().idxmax(),
    }
    df["month"]    = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
    stats["by_month"] = df["month"].value_counts().to_dict()
    return stats
