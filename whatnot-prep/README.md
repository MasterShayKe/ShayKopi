# whatnot-prep

A small Flask app that lives on your Windows PC. You snap a card in your iPhone
browser; Claude identifies it, eBay sold listings give you comps, and Claude
turns the result into a tier (HEAT / SOLID / FILLER), a one-line hype call, a
Whatnot listing description, and a show-order score. The frontend keeps a
running, sorted pile and exports the whole thing as a script you can paste.

## Pipeline

1. **Vision** — image goes to `claude-sonnet-4-20250514` which returns
   `{name, set, number, rarity, variant, condition, ebay_query}`.
2. **Comps** — `requests` + `BeautifulSoup4` scrape eBay sold listings using
   the query (`LH_Sold=1&LH_Complete=1`), extract up to 10 prices, summarise
   low / mid (median) / high.
3. **Tier** — card metadata + comps go back to Claude, which returns
   `{tier, hype_line, whatnot_description, show_order_score}`.
4. The frontend renders a sorted list and offers a one-tap export.

---

## Windows setup

### 1. Install Python 3.10+

If you don't have it: https://www.python.org/downloads/windows/ — during the
installer, tick **"Add python.exe to PATH"**.

Verify in PowerShell:

```powershell
python --version
```

### 2. Get the code and create a venv

From the `whatnot-prep` folder in PowerShell:

```powershell
cd whatnot-prep
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks the activate script, run once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

(Use `venv\Scripts\activate.bat` from `cmd.exe` if you prefer the classic
shell.)

### 3. Add your Anthropic API key

Copy `.env.example` to `.env` and paste your key:

```powershell
copy .env.example .env
notepad .env
```

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Run it

```powershell
python app.py
```

You should see `Running on http://0.0.0.0:5000`.

---

## Open it on your iPhone

Both devices need to be on the **same Wi-Fi network**.

### Find your PC's local IP

In PowerShell:

```powershell
ipconfig
```

Look for the active adapter (usually `Wireless LAN adapter Wi-Fi`) and grab
the **IPv4 Address**, e.g. `192.168.1.42`.

### Allow Flask through the Windows firewall (first run)

When Flask starts the first time, Windows Defender Firewall pops up — tick
**Private networks** and click **Allow access**. If you missed the prompt:

> Settings → Privacy & Security → Windows Security → Firewall & network
> protection → Allow an app through firewall → Python — make sure **Private**
> is checked.

### Open on iPhone

In Safari, go to:

```
http://192.168.1.42:5000
```

(Substitute your actual IP.) Tap **Snap card** to use the camera, or **Upload**
to pick from the photo library. The app stores the running list in the
browser's localStorage, so you can refresh without losing the pile.

Add it to the home screen via Share → **Add to Home Screen** for a fullscreen
PWA-style experience.

---

## Notes

- **Model**: defaults to `claude-sonnet-4-20250514`. Override via
  `CLAUDE_MODEL` in `.env`.
- **Port**: defaults to `5000`. Override via `PORT` in `.env`.
- **eBay scraping** can fail or return zero results if eBay rate-limits you or
  changes their HTML. The app degrades gracefully — Claude still tiers the card
  using rarity/variant signals when there are no comps.
- **HEIC photos** from iPhone are usually auto-converted to JPEG by Safari on
  upload. If you hit a vision error mentioning media type, retake the photo or
  toggle iPhone → Settings → Camera → Formats → **Most Compatible**.
- **Privacy**: images are sent to Anthropic's API; eBay scrape requests come
  from your PC. Nothing else leaves the machine.
