# Price alerts (email, works with your phone locked)

A free scheduled job checks your prices every 15 minutes and emails you the moment a target is hit.

## 1. Get a Gmail "App Password" (2 minutes)
Your normal Gmail password won't work for this — you need an App Password.
1. Turn on 2-Step Verification on your Google account, if it isn't already: https://myaccount.google.com/security
2. Go to https://myaccount.google.com/apppasswords
3. Create a new app password (name it anything, e.g. "price alerts"). Copy the 16-character code — you won't see it again.

(Using a different email provider? Same idea applies — you just need SMTP host/port and an app-specific password. Tell me the provider and I'll adjust the workflow.)

## 2. Create the repo
1. Go to https://github.com/new, create a new repository (private is fine, e.g. `price-alerts`).
2. Upload these files, keeping the folder structure:
   ```
   check_prices.py
   alerts.json
   requirements.txt
   .github/workflows/check-prices.yml
   ```
   Easiest way: on the repo page, "Add file" → "Upload files", drag all of them in (GitHub preserves the `.github/workflows/` path automatically if you drag the whole folder in supported browsers — otherwise create the `.github/workflows/check-prices.yml` file manually via "Create new file" and paste the path in as the filename).

## 3. Add your secrets
In your repo: **Settings → Secrets and variables → Actions → New repository secret**. Add:

| Name | Value |
|---|---|
| `EMAIL_ADDRESS` | your Gmail address |
| `EMAIL_APP_PASSWORD` | the 16-character app password from step 1 |
| `EMAIL_TO` | where you want alerts sent (can be the same address) |
| `FINNHUB_API_KEY` | *(optional, only needed for stock alerts)* your free key from finnhub.io |

## 4. Edit alerts.json with your real targets
Each alert looks like one of these:

```json
{ "id": "btc-100k", "market": "crypto", "coin_id": "bitcoin", "label": "BTC", "condition": "above", "target": 100000, "triggered": false }
{ "id": "usd-eur",  "market": "forex",  "from": "USD", "to": "EUR", "condition": "below", "target": 0.90, "triggered": false }
{ "id": "aapl-250", "market": "stock",  "symbol": "AAPL", "condition": "above", "target": 250, "triggered": false }
```
- `condition` is `"above"` or `"below"`.
- For crypto, `coin_id` must be the CoinGecko id (bitcoin, ethereum, solana, cardano, dogecoin, ripple, binancecoin, etc — search any coin at coingecko.com, the id is in the URL).
- Once an alert fires it's marked `"triggered": true` and won't email you again. Set it back to `false` (and maybe bump the target) to re-arm it.

Commit the change — that alone doesn't trigger a run, it just updates what's watched.

## 5. Test it
Go to the **Actions** tab in your repo → "Check price alerts" → **Run workflow** (this is the `workflow_dispatch` trigger) to fire it manually and confirm you get an email. Check the run logs if something doesn't arrive — the script prints every price it checks.

After that, it runs automatically every 15 minutes.

## Things worth knowing
- **GitHub disables scheduled workflows after 60 days of repo inactivity** (no commits/pushes). If your alerts stop firing after a couple of months, just push any small commit (or re-run manually) to wake it back up.
- 15-minute granularity means you could miss a price by a few minutes at the exact moment it crosses your target — fine for "let me know when BTC hits $100k," not meant for second-by-second trading.
- CoinGecko's free endpoint is rate-limited; if crypto checks start failing in the logs, get a free CoinGecko "Demo" API key and I can wire it in.
- Keep the repo **private** if you'd rather not have your watched prices/targets public.
