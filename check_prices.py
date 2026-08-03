"""
Checks watched prices against alerts.json and emails you when a target is hit.
Run on a schedule by the GitHub Actions workflow in .github/workflows/check-prices.yml
"""
import json
import os
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

import requests

ALERTS_FILE = Path(__file__).parent / "alerts.json"


def load_alerts():
    with open(ALERTS_FILE) as f:
        return json.load(f)


def save_alerts(alerts):
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f, indent=2)
        f.write("\n")


def get_crypto_prices(coin_ids):
    if not coin_ids:
        return {}
    ids = ",".join(sorted(set(coin_ids)))
    r = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": ids, "vs_currencies": "usd"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def get_forex_rate(base, quote):
    r = requests.get(
        "https://api.frankfurter.app/latest",
        params={"from": base, "to": quote},
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("rates", {}).get(quote)


def get_stock_price(symbol, api_key):
    if not api_key:
        return None
    r = requests.get(
        "https://finnhub.io/api/v1/quote",
        params={"symbol": symbol, "token": api_key},
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("c")


def send_email(subject, body):
    host = os.environ.get("EMAIL_SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
    user = os.environ["EMAIL_ADDRESS"]
    password = os.environ["EMAIL_APP_PASSWORD"]
    to_addr = os.environ.get("EMAIL_TO", user)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(user, [to_addr], msg.as_string())


def fmt(n):
    if n is None:
        return "—"
    return f"{n:,.6f}".rstrip("0").rstrip(".") if n < 1 else f"{n:,.2f}"


def label_for(a):
    if a["market"] == "crypto":
        return a.get("label") or a["coin_id"]
    if a["market"] == "forex":
        return f'{a["from"]}/{a["to"]}'
    return a["symbol"]


def main():
    alerts = load_alerts()
    finnhub_key = os.environ.get("FINNHUB_API_KEY", "")

    active = [a for a in alerts if not a.get("triggered")]
    crypto_ids = [a["coin_id"] for a in active if a["market"] == "crypto"]

    crypto_prices = {}
    try:
        crypto_prices = get_crypto_prices(crypto_ids)
    except Exception as e:
        print(f"Crypto price fetch failed: {e}")

    changed = False
    for a in active:
        try:
            if a["market"] == "crypto":
                price = crypto_prices.get(a["coin_id"], {}).get("usd")
            elif a["market"] == "forex":
                price = get_forex_rate(a["from"], a["to"])
            elif a["market"] == "stock":
                price = get_stock_price(a["symbol"], finnhub_key)
            else:
                print(f"Unknown market type for alert {a.get('id')}")
                continue

            if price is None:
                print(f"No price returned for {label_for(a)}")
                continue

            a["last_price"] = price
            met = (price >= a["target"]) if a["condition"] == "above" else (price <= a["target"])
            print(f"{label_for(a)}: {fmt(price)} (target {a['condition']} {fmt(a['target'])}) -> {'HIT' if met else 'watching'}")

            if met:
                label = label_for(a)
                verb = "rose above" if a["condition"] == "above" else "fell below"
                subject = f"Price alert: {label} {verb} {fmt(a['target'])}"
                body = f"{label} is now {fmt(price)}.\nTarget: {a['condition']} {fmt(a['target'])}.\n\n(This alert won't fire again — edit alerts.json and set \"triggered\": false to re-arm it.)"
                send_email(subject, body)
                a["triggered"] = True
                changed = True
        except Exception as e:
            print(f"Error checking alert {a.get('id')}: {e}")

    if changed:
        save_alerts(alerts)


if __name__ == "__main__":
    main()
