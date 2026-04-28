import argparse
import csv
import datetime as dt
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from wti_yahoo_realtime import get_recent_history

MYSQL_URL = os.environ.get("MYSQL_URL", "").strip()
_SQLALCHEMY_IMPORT_ERROR = ""
try:
    from sqlalchemy import create_engine, text

    _SQLALCHEMY_AVAILABLE = True
except Exception as e:
    create_engine = None  # type: ignore[assignment]
    text = None  # type: ignore[assignment]
    _SQLALCHEMY_AVAILABLE = False
    _SQLALCHEMY_IMPORT_ERROR = str(e)

DB_ENABLED = bool(_SQLALCHEMY_AVAILABLE and MYSQL_URL)
_ENGINE = None


FRED_SERIES_WEEKLY_WTI = "WCOILWTICO"
FRED_WEEKLY_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=WCOILWTICO"
BARCHART_OVERVIEW_URL = "https://www.barchart.com/futures/quotes/CL*0/overview"
INVESTING_CN_URL = "https://cn.investing.com/commodities/crude-oil"
INVESTING_EN_URL = "https://www.investing.com/commodities/crude-oil"


@dataclass
class UnifiedPriceRow:
    country: str
    last_update: dt.date
    current_price: Optional[float]
    measure: str
    page_url: str
    source: str
    fetched_at: str


def _require_db_enabled() -> None:
    if not _SQLALCHEMY_AVAILABLE:
        detail = f" ({_SQLALCHEMY_IMPORT_ERROR})" if _SQLALCHEMY_IMPORT_ERROR else ""
        raise RuntimeError(
            "MySQL not enabled: SQLAlchemy unavailable. "
            "Please run: pip install -U sqlalchemy pymysql typing_extensions" + detail
        )
    if not MYSQL_URL:
        raise RuntimeError("MySQL not enabled: MYSQL_URL is not configured.")


def get_engine():
    global _ENGINE
    _require_db_enabled()
    if _ENGINE is None:
        _ENGINE = create_engine(
            MYSQL_URL,
            pool_pre_ping=True,
            pool_recycle=3600,
            future=True,
        )
    return _ENGINE


def init_mysql_table() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS global_gasoline_prices (
                    country VARCHAR(128) NOT NULL,
                    last_update DATE NOT NULL,
                    current_price DECIMAL(10,4) NULL,
                    measure VARCHAR(64) NULL,
                    page_url VARCHAR(255) NOT NULL,
                    source VARCHAR(32) NOT NULL DEFAULT 'globalpetrolprices',
                    fetched_at DATETIME NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (country, last_update)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
        )


def _fetch_fred_weekly_spot(limit: int, timeout: int) -> List[Dict]:
    resp = requests.get(FRED_WEEKLY_URL, timeout=timeout)
    resp.raise_for_status()
    lines = resp.text.splitlines()
    if not lines:
        return []
    reader = csv.DictReader(lines)
    out: List[Dict] = []
    for row in reader:
        date_s = (row.get("DATE") or row.get("observation_date") or "").strip()
        value_s = (row.get(FRED_SERIES_WEEKLY_WTI) or "").strip()
        if not date_s or not value_s or value_s == ".":
            continue
        try:
            trade_date = dt.datetime.strptime(date_s, "%Y-%m-%d").date()
            price = float(value_s)
        except Exception:
            continue
        out.append({"date": trade_date, "close": price})
    out.sort(key=lambda x: x["date"])
    return out[-limit:]


def _fetch_futures_from_yahoo(limit: int) -> List[Dict]:
    rows = get_recent_history(days=max(20, limit))
    out: List[Dict] = []
    for r in rows[-limit:]:
        try:
            trade_date = dt.datetime.strptime(str(r["date"]), "%Y-%m-%d").date()
            close = float(r["close"])
        except Exception:
            continue
        out.append({"date": trade_date, "close": close})
    return out


def _fetch_futures_from_barchart_overview(timeout: int) -> List[Dict]:
    headers = {"User-Agent": "Mozilla/5.0"}
    html = requests.get(BARCHART_OVERVIEW_URL, timeout=timeout, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")

    # 优先从“Related instruments”表抓 CLMxx 的 Latest
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        head = [c.get_text(" ", strip=True).lower() for c in rows[0].find_all(["th", "td"])]
        if not ("symbol" in head and "latest" in head):
            continue
        for tr in rows[1:20]:
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
            if len(cells) < 2:
                continue
            sym = cells[0].strip().upper()
            if not re.fullmatch(r"CL[A-Z]\d{2}", sym):
                continue
            try:
                latest = float(cells[1].replace(",", ""))
            except Exception:
                continue
            return [{"date": dt.date.today(), "close": latest}]

    # 次级兜底：全文正则抓 CLM26 : 99.89 这种片段
    text = soup.get_text("\n", strip=True)
    m = re.search(r"\bCL[A-Z]\d{2}\b\s*:?\s*([0-9]+\.[0-9]+)", text)
    if m:
        return [{"date": dt.date.today(), "close": float(m.group(1))}]
    return []


def _fetch_futures_from_investing(timeout: int) -> List[Dict]:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    for url in (INVESTING_CN_URL, INVESTING_EN_URL):
        html = requests.get(url, timeout=timeout, headers=headers).text
        # Cloudflare / challenge page: ignore and try next source
        if "Just a moment" in html or "challenges.cloudflare.com" in html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        txt = soup.get_text("\n", strip=True)
        # 兼容中英文页面关键词，抓“最新价”附近数字
        patterns = [
            r"(?:最新价|Last|Prev\. Close|当前价)\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)",
            r"\"last\"\\s*:\\s*\"?([0-9]+(?:\.[0-9]+)?)\"?",
            r"\"last_price\"\\s*:\\s*\"?([0-9]+(?:\.[0-9]+)?)\"?",
        ]
        for pat in patterns:
            m = re.search(pat, txt, flags=re.IGNORECASE)
            if not m:
                continue
            try:
                price = float(m.group(1))
            except Exception:
                continue
            return [{"date": dt.date.today(), "close": price}]
    return []


def build_unified_rows(limit: int, timeout: int) -> List[UnifiedPriceRow]:
    fetched_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    weekly_spot = _fetch_fred_weekly_spot(limit=limit, timeout=timeout)
    futures: List[Dict] = []
    futures_source = "yahoo_clf_daily"
    try:
        futures = _fetch_futures_from_yahoo(limit=limit)
    except Exception as exc:
        print(f"[WARN] Yahoo futures fetch failed, try Investing: {exc}")
        try:
            futures = _fetch_futures_from_investing(timeout=timeout)
            futures_source = "investing_cl_overview"
            if futures:
                print(f"[OK] Investing futures fallback rows: {len(futures)}")
            else:
                print("[WARN] Investing futures fallback returned empty, try Barchart.")
        except Exception as iexc:
            print(f"[WARN] Investing futures fetch failed, try Barchart: {iexc}")
        if not futures:
            futures = _fetch_futures_from_barchart_overview(timeout=timeout)
            futures_source = "barchart_cl_overview"
            if futures:
                print(f"[OK] Barchart futures fallback rows: {len(futures)}")
            else:
                print("[WARN] Barchart futures fallback returned empty.")
        

    rows: List[UnifiedPriceRow] = []
    for item in weekly_spot:
        rows.append(
            UnifiedPriceRow(
                country="WTI_SPOT_FRED",
                last_update=item["date"],
                current_price=item["close"],
                measure="USD/Barrel",
                page_url=f"https://fred.stlouisfed.org/series/{FRED_SERIES_WEEKLY_WTI}",
                source="fred_wti_weekly",
                fetched_at=fetched_at,
            )
        )
    for item in futures:
        futures_country = (
            "WTI_FUTURES_YAHOO"
            if futures_source == "yahoo_clf_daily"
            else ("WTI_FUTURES_INVESTING" if futures_source == "investing_cl_overview" else "WTI_FUTURES_BARCHART")
        )
        rows.append(
            UnifiedPriceRow(
                country=futures_country,
                last_update=item["date"],
                current_price=item["close"],
                measure="USD/Barrel",
                page_url=(
                    "https://finance.yahoo.com/quote/CL=F"
                    if futures_source == "yahoo_clf_daily"
                    else (INVESTING_CN_URL if futures_source == "investing_cl_overview" else BARCHART_OVERVIEW_URL)
                ),
                source=futures_source,
                fetched_at=fetched_at,
            )
        )
    return rows


def write_csv(path: str, rows: List[UnifiedPriceRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "country",
                "last_update",
                "current_price",
                "measure",
                "page_url",
                "source",
                "fetched_at",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "country": r.country,
                    "last_update": r.last_update.isoformat(),
                    "current_price": r.current_price,
                    "measure": r.measure,
                    "page_url": r.page_url,
                    "source": r.source,
                    "fetched_at": r.fetched_at,
                }
            )


def upsert_mysql(rows: List[UnifiedPriceRow]) -> int:
    engine = get_engine()
    sql = text(
        """
    INSERT INTO global_gasoline_prices
    (country, last_update, current_price, measure, page_url, source, fetched_at)
    VALUES (:country, :last_update, :current_price, :measure, :page_url, :source, :fetched_at)
    ON DUPLICATE KEY UPDATE
        current_price = VALUES(current_price),
        measure = VALUES(measure),
        page_url = VALUES(page_url),
        source = VALUES(source),
        fetched_at = VALUES(fetched_at);
    """
    )
    n = 0
    with engine.begin() as conn:
        for r in rows:
            conn.execute(
                sql,
                {
                    "country": r.country,
                    "last_update": r.last_update,
                    "current_price": r.current_price,
                    "measure": r.measure,
                    "page_url": r.page_url,
                    "source": r.source,
                    "fetched_at": r.fetched_at,
                },
            )
            n += 1
    return n


def summarize_rows(rows: List[UnifiedPriceRow]) -> None:
    by_key: Dict[str, List[UnifiedPriceRow]] = {}
    for r in rows:
        by_key.setdefault(r.country, []).append(r)
    for key, group in by_key.items():
        group.sort(key=lambda x: x.last_update)
        print(
            f"[{key}] rows={len(group)} "
            f"range={group[0].last_update.isoformat()}->{group[-1].last_update.isoformat()} "
            f"latest={group[-1].current_price}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch WTI spot/futures latest N rows and upsert into MySQL table global_gasoline_prices."
    )
    parser.add_argument(
        "--action",
        choices=["init-db", "sync"],
        required=True,
        help="init-db: create table; sync: fetch and write data",
    )
    parser.add_argument("--limit", type=int, default=20, help="Latest rows for each source.")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout seconds.")
    parser.add_argument("--out", default="wti_spot_futures_latest20.csv", help="CSV output path.")
    parser.add_argument("--to-mysql", action="store_true", help="Upsert crawled rows into MySQL.")
    args = parser.parse_args()

    if not DB_ENABLED:
        raise RuntimeError("MySQL未启用：请安装 SQLAlchemy 并配置 MYSQL_URL。")

    if args.action == "init-db":
        init_mysql_table()
        print("[OK] MySQL table global_gasoline_prices initialized.")
        return 0

    rows = build_unified_rows(limit=max(1, int(args.limit)), timeout=max(5, int(args.timeout)))
    write_csv(args.out, rows)
    print(f"[OK] saved CSV rows: {len(rows)} -> {args.out}")
    summarize_rows(rows)

    if args.to_mysql:
        n = upsert_mysql(rows)
        print(f"[OK] upserted MySQL rows: {n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

