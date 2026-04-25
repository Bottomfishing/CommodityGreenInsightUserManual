import argparse
import os
from datetime import datetime
from typing import Dict, List

from wti_yahoo_realtime import get_recent_history, get_realtime_quote

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


def init_db() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS wti_daily_prices (
                    trade_date DATE PRIMARY KEY,
                    open_price DECIMAL(12,4) NULL,
                    high_price DECIMAL(12,4) NULL,
                    low_price DECIMAL(12,4) NULL,
                    close_price DECIMAL(12,4) NOT NULL,
                    volume BIGINT NULL,
                    source VARCHAR(32) NOT NULL DEFAULT 'yahoo_chart',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS wti_realtime_snapshots (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    symbol VARCHAR(16) NOT NULL,
                    market_time DATETIME NULL,
                    market_price DECIMAL(12,4) NULL,
                    market_change DECIMAL(12,4) NULL,
                    market_change_percent DECIMAL(12,6) NULL,
                    currency VARCHAR(16) NULL,
                    exchange_name VARCHAR(128) NULL,
                    source VARCHAR(32) NOT NULL DEFAULT 'yahoo_chart',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    KEY idx_symbol_created (symbol, created_at),
                    KEY idx_market_time (market_time)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
        )


def upsert_daily(conn, rows: List[Dict]) -> int:
    sql = text(
        """
    INSERT INTO wti_daily_prices
    (trade_date, open_price, high_price, low_price, close_price, volume, source)
    VALUES (:trade_date, :open_price, :high_price, :low_price, :close_price, :volume, 'yahoo_chart')
    ON DUPLICATE KEY UPDATE
        open_price = VALUES(open_price),
        high_price = VALUES(high_price),
        low_price = VALUES(low_price),
        close_price = VALUES(close_price),
        volume = VALUES(volume),
        source = VALUES(source);
    """
    )
    count = 0
    for r in rows:
        conn.execute(
            sql,
            {
                "trade_date": r["date"],
                "open_price": r.get("open"),
                "high_price": r.get("high"),
                "low_price": r.get("low"),
                "close_price": r.get("close"),
                "volume": r.get("volume"),
            },
        )
        count += 1
    return count


def insert_realtime(conn, quote: Dict) -> None:
    market_time = quote.get("regularMarketTime")
    market_dt = None
    if market_time:
        market_dt = datetime.strptime(market_time, "%Y-%m-%d %H:%M:%S")

    conn.execute(
        text(
            """
        INSERT INTO wti_realtime_snapshots
        (symbol, market_time, market_price, market_change, market_change_percent, currency, exchange_name, source)
        VALUES (:symbol, :market_time, :market_price, :market_change, :market_change_percent, :currency, :exchange_name, 'yahoo_chart');
        """
        ),
        {
            "symbol": quote.get("symbol"),
            "market_time": market_dt,
            "market_price": quote.get("regularMarketPrice"),
            "market_change": quote.get("regularMarketChange"),
            "market_change_percent": quote.get("regularMarketChangePercent"),
            "currency": quote.get("currency"),
            "exchange_name": quote.get("exchange"),
        },
    )


def run_sync(days: int) -> None:
    _require_db_enabled()
    history = get_recent_history(days=days)
    quote = get_realtime_quote()

    engine = get_engine()
    with engine.begin() as conn:
        n = upsert_daily(conn, history)
        insert_realtime(conn, quote)

    print(f"[OK] upserted daily rows: {n}")
    print(
        "[OK] inserted realtime snapshot:"
        f" {quote.get('symbol')} {quote.get('regularMarketPrice')} @ {quote.get('regularMarketTime')}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync WTI Yahoo data to MySQL.")
    parser.add_argument(
        "--action",
        choices=["init-db", "sync"],
        required=True,
        help="init-db: create tables; sync: fetch and write data",
    )
    parser.add_argument("--days", type=int, default=20, help="Daily rows to upsert when sync.")
    args = parser.parse_args()
    if not DB_ENABLED:
        raise RuntimeError("MySQL未启用：请安装 SQLAlchemy 并配置 MYSQL_URL。")

    if args.action == "init-db":
        init_db()
        print("[OK] database tables initialized.")
        return 0

    run_sync(days=args.days)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
