import argparse
import csv
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

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


BASE_URL = "https://www.globalpetrolprices.com"
LIST_URL = f"{BASE_URL}/gasoline_prices/"


@dataclass
class GasolinePriceRow:
    country: str
    page_url: str
    current_price: Optional[float]
    measure: Optional[str]
    last_update: Optional[str]
    fetched_at: str
    source: str = "globalpetrolprices"


def build_session(timeout: int) -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
    )
    s.request_timeout = timeout  # type: ignore[attr-defined]
    return s


def _request_text(session: requests.Session, url: str) -> str:
    timeout = getattr(session, "request_timeout", 20)
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def get_country_urls(session: requests.Session) -> List[str]:
    html = _request_text(session, LIST_URL)
    soup = BeautifulSoup(html, "html.parser")

    urls = set()
    for a in soup.select("a.graph_outside_link[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue
        if re.match(r"^/[A-Za-z0-9\-]+/gasoline_prices/$", href):
            urls.add(urljoin(BASE_URL, href))
    return sorted(urls)


def parse_country_page(session: requests.Session, url: str) -> GasolinePriceRow:
    html = _request_text(session, url)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    country = url.rstrip("/").split("/")[-2].replace("-", " ")
    m_h1 = soup.find("h1")
    if m_h1:
        # e.g. "USA Gasoline prices, 20-Apr-2026"
        country = m_h1.get_text(" ", strip=True).split(" Gasoline prices")[0].strip()

    info = {}
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for tr in rows:
            cells = tr.find_all(["th", "td"])
            if len(cells) < 2:
                continue
            k = cells[0].get_text(" ", strip=True).lower()
            v = cells[1].get_text(" ", strip=True)
            if k not in info:
                info[k] = v

    current_price = _to_float(info.get("current price"))
    measure = info.get("measure")
    last_update = info.get("last update")

    # Some country pages use a currency matrix table (AFN/USD/EUR) instead of the standard summary table.
    if current_price is None:
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            for tr in rows:
                cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
                if len(cells) >= 2 and cells[0].upper() == "USD":
                    current_price = _to_float(cells[1])
                    measure = "USD/Liter"
                    break
            if current_price is not None:
                break
    if not last_update:
        m = re.search(r"updated on (\d{2}-[A-Za-z]{3}-\d{4})", text, re.IGNORECASE)
        if m:
            last_update = datetime.strptime(m.group(1), "%d-%b-%Y").strftime("%Y-%m-%d")

    if not last_update and m_h1:
        # e.g. "... 20-Apr-2026"
        m = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", m_h1.get_text(" ", strip=True))
        if m:
            last_update = datetime.strptime(m.group(1), "%d-%b-%Y").strftime("%Y-%m-%d")

    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return GasolinePriceRow(
        country=country,
        page_url=url,
        current_price=current_price,
        measure=measure,
        last_update=last_update,
        fetched_at=fetched_at,
    )


def _to_float(v: Optional[str]) -> Optional[float]:
    if not v:
        return None
    v = v.replace(",", "").strip()
    try:
        return float(v)
    except ValueError:
        return None


def write_csv(path: str, rows: List[GasolinePriceRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "country",
                "current_price",
                "measure",
                "last_update",
                "page_url",
                "source",
                "fetched_at",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r.__dict__)


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


def upsert_mysql(rows: List[GasolinePriceRow]) -> int:
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
            last_update = datetime.strptime(r.fetched_at[:10], "%Y-%m-%d").date()
            if r.last_update:
                try:
                    last_update = datetime.strptime(r.last_update, "%Y-%m-%d").date()
                except ValueError:
                    pass
            conn.execute(
                sql,
                {
                    "country": r.country,
                    "last_update": last_update,
                    "current_price": r.current_price,
                    "measure": r.measure,
                    "page_url": r.page_url,
                    "source": r.source,
                    "fetched_at": r.fetched_at,
                },
            )
            n += 1
    return n


def main() -> int:
    parser = argparse.ArgumentParser(description="Crawl global gasoline prices by country.")
    parser.add_argument("--out", default="global_gasoline_prices.csv", help="CSV output path.")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout seconds.")
    parser.add_argument("--sleep-ms", type=int, default=200, help="Delay between country requests.")
    parser.add_argument("--limit", type=int, default=0, help="For debug: crawl only first N countries.")
    parser.add_argument("--to-mysql", action="store_true", help="Upsert crawled rows into MySQL.")
    parser.add_argument("--init-mysql", action="store_true", help="Initialize MySQL table and exit.")
    args = parser.parse_args()

    if args.init_mysql:
        _require_db_enabled()
        init_mysql_table()
        print("[OK] MySQL table global_gasoline_prices initialized.")
        return 0

    session = build_session(args.timeout)
    urls = get_country_urls(session)
    if args.limit > 0:
        urls = urls[: args.limit]

    rows: List[GasolinePriceRow] = []
    for i, url in enumerate(urls, 1):
        try:
            row = parse_country_page(session, url)
            rows.append(row)
            print(f"[{i}/{len(urls)}] {row.country}: {row.current_price} {row.measure}")
        except Exception as e:
            print(f"[WARN] failed: {url} -> {e}")
        time.sleep(max(args.sleep_ms, 0) / 1000.0)

    write_csv(args.out, rows)
    print(f"[OK] saved CSV rows: {len(rows)} -> {args.out}")

    if args.to_mysql:
        _require_db_enabled()
        n = upsert_mysql(rows)
        print(f"[OK] upserted MySQL rows: {n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
