"""Normalize DATABASE_URL for asyncpg (no psycopg2)."""

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

CLOUD_DB_HOSTS = ("neon.tech", "render.com", "supabase.co")

# Query params that asyncpg/SQLAlchemy must not receive via URL
_STRIP_QUERY_KEYS = ("sslmode", "ssl", "channel_binding")


def _needs_ssl(host: str, query: dict[str, list[str]]) -> bool:
    sslmode = query.get("sslmode", [""])[0]
    if sslmode in ("require", "verify-ca", "verify-full"):
        return True
    ssl_val = query.get("ssl", [""])[0].lower()
    if ssl_val in ("require", "true", "1", "prefer"):
        return True
    is_local = host in ("localhost", "127.0.0.1", "db") or host.endswith(".local")
    if not is_local and any(marker in host for marker in CLOUD_DB_HOSTS):
        return True
    return False


def parse_database_url(url: str) -> tuple[str, dict]:
    """Return (normalized_url, connect_args) for asyncpg."""
    if not url:
        return url, {}

    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]

    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    host = parsed.hostname or ""

    connect_args: dict = {}
    if _needs_ssl(host, query):
        connect_args["ssl"] = True

    for key in _STRIP_QUERY_KEYS:
        query.pop(key, None)

    new_query = urlencode({k: v[0] for k, v in query.items()}, doseq=False)
    clean_url = urlunparse(parsed._replace(query=new_query))
    return clean_url, connect_args


def normalize_database_url(url: str) -> str:
    """Convert any postgres URL to postgresql+asyncpg with asyncpg-safe query params."""
    return parse_database_url(url)[0]


def get_connect_args(url: str) -> dict:
    """connect_args for create_async_engine (SSL for Neon/cloud)."""
    return parse_database_url(url)[1]
