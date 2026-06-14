# 🔔 Stock Alert Intelligence Engine

Unlimited automated NSE stock alert system using Python, GitHub Actions, and Telegram.
No broker dependency. No subscription fees.

---

## ✅ Features
- Unlimited NSE stock alerts
- Price, Support, Resistance, Breakout, Trendline, Volume spike alerts
- Crossed level detection (detects skipped prices)
- Proximity warning before alert hits (±1% zone + volume spike)
- Instant Telegram notifications
- Daily summary at 6:00 PM IST
- Full alert history in Parquet
- Monthly archive sent to Telegram
- Configuration driven — change everything from config.yaml

---

## ⚙️ One Time Setup

### 1. Fork this repo

### 2. Create Telegram Bot
- Open Telegram → search @BotFather → /newbot → copy bot token
- Search @userinfobot → /start → copy your chat id

### 3. Add GitHub Secrets
Repo → Settings → Secrets → Actions → New secret

| Name | Value |
|------|-------|
| BOT_TOKEN | your telegram bot token |
| CHAT_ID | your telegram chat id |

### 4. Create GitHub PAT Token
GitHub → Settings → Developer Settings → Personal Access Tokens → Classic
Scopes: ✅ repo ✅ workflow → 90 days → Generate → copy token

### 5. Download Alert_Manager.ipynb
Download from this repo → upload to Google Drive → open in Colab
Fill in Cell 1:
```python
GITHUB_USERNAME = "your_github_username"
GITHUB_TOKEN    = "your_pat_token"
REPO_NAME       = "stock-alert-engine"
```

### 6. Add your first alert
Run Cell 1 then Cell 3 in Alert Manager:
```python
add_alert("RELIANCE", "Support",    1200.00)
add_alert("TCS",      "Resistance", 4200.00)
add_alert("INFY",     "Price",      1500.00)
```
Run Cell 8 to push to GitHub.

### 7. Test
Repo → Actions → Stock Alert Scan → Run workflow
Check Telegram for confirmation message.

---

## 📅 Automated Schedule

| Time | Action |
|------|--------|
| 5:30 PM IST Mon–Sat | Scan all alerts, send Telegram on hit |
| 6:00 PM IST Mon–Sat | Daily summary — closest alerts |
| 1st of every month | Archive history to Telegram |

---

## 🔔 Alert Types

```python
add_alert("STOCK", "Price",       1300.00)  # crosses level
add_alert("STOCK", "Support",     1200.00)  # falls to level
add_alert("STOCK", "Resistance",  1400.00)  # rises to level
add_alert("STOCK", "Breakout",    1350.00)  # breaks above
add_alert("STOCK", "Breakdown",   1250.00)  # breaks below
add_alert("STOCK", "VolumeSpike",    3.0)   # volume > 3x average

# Trendline alert
add_trendline_alert(
    "RELIANCE", "TrendlineBreakout",
    "2026-03-01", 1350,   # point 1 from your chart
    "2026-05-01", 1280,   # point 2 from your chart
    volume_factor=1.5
)
```

---

## 🔄 Every 90 Days — Renew Token
GitHub → Settings → Developer Settings → PAT → Regenerate
Update in Alert_Manager.ipynb Cell 1 → save to Drive

---

## ⚠️ Disclaimer
Educational purposes only. Not financial advice.

---
Built by [Tushar Deshmane](https://github.com/TusharQLab)
