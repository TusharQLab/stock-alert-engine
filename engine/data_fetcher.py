
import yfinance as yf
import pandas as pd
import numpy as np
import time
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from engine.paths import get_config_path

def load_config():
    with open(get_config_path()) as f:
        return yaml.safe_load(f)

def fetch_single(sym):
    try:
        cfg     = load_config()
        period  = cfg["fetch"]["history_period"]
        min_c   = cfg["fetch"]["min_candles_required"]
        v_short = cfg["volume"]["avg_period_short"]
        v_long  = cfg["volume"]["avg_period_long"]

        hist = yf.Ticker(sym + ".NS").history(period=period, auto_adjust=True)

        if hist.empty or len(hist) < min_c:
            return sym, None

        hist = hist.dropna(subset=["Close","Volume"])

        current_price = float(hist["Close"].iloc[-1])
        prev_close    = float(hist["Close"].iloc[-2])
        current_vol   = float(hist["Volume"].iloc[-1])

        vol = hist["Volume"].dropna()
        avg_vol_short = float(vol.iloc[-(v_short+1):-1].mean()) if len(vol) >= v_short+1 else np.nan
        avg_vol_long  = float(vol.iloc[-(v_long+1):-1].mean())  if len(vol) >= v_long+1  else np.nan

        return sym, {
            "symbol"         : sym,
            "current_price"  : current_price,
            "prev_close"     : prev_close,
            "current_vol"    : current_vol,
            "avg_vol_short"  : avg_vol_short,
            "avg_vol_long"   : avg_vol_long,
            "vol_spike_short": round(current_vol / avg_vol_short, 2) if avg_vol_short else np.nan,
            "vol_spike_long" : round(current_vol / avg_vol_long,  2) if avg_vol_long  else np.nan,
            "history"        : hist
        }
    except:
        return sym, None

def fetch_market_data(symbols):
    cfg         = load_config()
    batch_size  = cfg["fetch"]["batch_size"]
    max_workers = cfg["fetch"]["max_workers"]
    sleep_time  = cfg["fetch"]["sleep_between_batches"]

    total     = len(symbols)
    batches   = [symbols[i:i+batch_size] for i in range(0, total, batch_size)]
    results   = {}
    completed = 0

    print(f"📡 Fetching market data for {total} symbols [workers={max_workers}]")

    for batch in batches:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_single, sym): sym for sym in batch}
            for future in as_completed(futures):
                try:
                    sym, data = future.result()
                except:
                    sym  = futures[future]
                    data = None
                results[sym] = data
                completed += 1
                pct = completed / total * 100
                bar = "█" * int(pct // 5) + "░" * (20 - int(pct // 5))
                print(f"\r   [{bar}] {completed}/{total} ({pct:.0f}%)", end="", flush=True)
        time.sleep(sleep_time)

    print()
    success = sum(1 for v in results.values() if v is not None)
    failed  = [s for s, v in results.items() if v is None]
    print(f"✅ Fetch complete — {success}/{total} succeeded")
    if failed:
        print(f"⚠️  Failed: {failed}")
    return results
