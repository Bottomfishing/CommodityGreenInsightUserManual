import argparse
import csv
import datetime as dt
import json
import sys
import time
import urllib.parse
from typing import Any, Dict, List

import urllib.error
import urllib.request

SYMBOL = "CL=F"
YAHOO_CHART_URLS = [
    "https://query2.finance.yahoo.com/v8/finance/chart/CL=F",
    "https://query1.finance.yahoo.com/v8/finance/chart/CL=F",
]
PROXY_URL: str | None = None


def get_recent_history(days: int = 20) -> List[Dict[str, Any]]:
    data = _fetch_chart_json(range_value="3mo", interval="1d")
    result = (data.get("chart", {}).get("result") or [{}])[0]
    timestamps = result.get("timestamp") or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]

    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []

    rows: List[Dict[str, Any]] = []
    for i, ts in enumerate(timestamps):
        close = closes[i] if i < len(closes) else None
        if close is None:
            continue
        date = dt.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")
        rows.append(
            {
                "date": date,
                "open": opens[i] if i < len(opens) else None,
                "high": highs[i] if i < len(highs) else None,
                "low": lows[i] if i < len(lows) else None,
                "close": close,
                "volume": volumes[i] if i < len(volumes) else None,
            }
        )

    if not rows:
        raise RuntimeError("Yahoo history is empty (possibly blocked or unavailable).")
    return rows[-days:]


def get_realtime_quote() -> Dict[str, Any]:
    data = _fetch_chart_json(range_value="1d", interval="1m")
    result = (data.get("chart", {}).get("result") or [{}])[0]
    meta = result.get("meta") or {}
    timestamps = result.get("timestamp") or []
    quote_ind = (result.get("indicators", {}).get("quote") or [{}])[0]
    closes = quote_ind.get("close") or []
    if not timestamps or not closes:
        raise RuntimeError("Failed to load realtime quote from Yahoo chart endpoint.")

    market_time_raw = timestamps[-1]
    market_time_str = (
        dt.datetime.fromtimestamp(market_time_raw).strftime("%Y-%m-%d %H:%M:%S")
        if market_time_raw
        else None
    )
    last_price = closes[-1]
    prev_close = meta.get("chartPreviousClose")
    change = None
    change_pct = None
    if last_price is not None and prev_close not in (None, 0):
        change = float(last_price - prev_close)
        change_pct = float(change / prev_close * 100)

    return {
        "symbol": SYMBOL,
        "shortName": meta.get("shortName") or "Crude Oil Futures",
        "currency": meta.get("currency") or "USD",
        "exchange": meta.get("fullExchangeName") or meta.get("exchangeName"),
        "regularMarketPrice": last_price,
        "regularMarketChange": change,
        "regularMarketChangePercent": change_pct,
        "regularMarketTime": market_time_str,
    }


def _build_yahoo_opener() -> urllib.request.OpenerDirector:
    handlers: List[urllib.request.BaseHandler] = []
    if PROXY_URL:
        handlers.append(urllib.request.ProxyHandler({"http": PROXY_URL, "https": PROXY_URL}))
    return urllib.request.build_opener(*handlers)


def _fetch_chart_json(range_value: str, interval: str) -> Dict[str, Any]:
    opener = _build_yahoo_opener()
    params = urllib.parse.urlencode({"range": range_value, "interval": interval})
    last_error = None
    for base in YAHOO_CHART_URLS:
        try:
            text = _fetch_text(f"{base}?{params}", opener=opener)
            data = json.loads(text)
            if data.get("chart", {}).get("result"):
                return data
            last_error = RuntimeError(f"Empty chart result from {base}")
        except RuntimeError as e:
            last_error = e
            continue
    raise RuntimeError(f"Failed to load chart data from Yahoo: {last_error}")


def _fetch_text(
    url: str,
    timeout: int = 20,
    opener: urllib.request.OpenerDirector | None = None,
    retries: int = 2,
) -> str:
    if opener is None:
        opener = urllib.request.build_opener()

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    delay = 1.0
    for i in range(retries):
        try:
            with opener.open(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise RuntimeError(f"HTTP error {e.code} when requesting {url}") from e
        except urllib.error.URLError as e:
            if i < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise RuntimeError(f"Network error when requesting {url}: {e.reason}") from e
    raise RuntimeError(f"Request failed after retries: {url}")


def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    fieldnames = ["date", "open", "high", "low", "close", "volume"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    global PROXY_URL
    parser = argparse.ArgumentParser(
        description="Fetch WTI futures (CL=F) realtime and recent 20-day history."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=20,
        help="How many latest trading days to keep (default: 20).",
    )
    parser.add_argument(
        "--csv",
        default="wti_clf_last20days.csv",
        help="CSV output path for historical data.",
    )
    parser.add_argument(
        "--proxy",
        default=None,
        help="Optional HTTP/HTTPS proxy, e.g. http://127.0.0.1:7890",
    )
    args = parser.parse_args()
    PROXY_URL = args.proxy

    try:
        history = get_recent_history(days=args.days)
        quote = get_realtime_quote()
    except RuntimeError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    write_csv(args.csv, history)

    print("=== CL=F Realtime Quote ===")
    print(json.dumps(quote, ensure_ascii=False, indent=2))
    print()
    print(f"Saved {len(history)} rows to: {args.csv}")
    if history:
        print(f"Date range: {history[0]['date']} -> {history[-1]['date']}")
        print(f"Latest close: {history[-1]['close']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
