"""Normalize DATABASE_URL for asyncpg (no psycopg2)."""

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

CLOUD_DB_HOSTS = ("neon.tech", "render.com", "supabase.co")


def normalize_database_url(url: str) -> str:
    """Convert any postgres URL to postgresql+asyncpg with correct SSL params."""
    if not url:
        return url

    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]

    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)

    # asyncpg uses ssl=, not libpq sslmode=
    if "sslmode" in query:
        mode = query.pop("sslmode")[0]
        if mode == "require":
            query.setdefault("ssl", ["require"])
        elif mode in ("prefer", "allow", "disable", "verify-full", "verify-ca"):
            query.setdefault("ssl", [mode])

    host = parsed.hostname or ""
    is_local = host in ("localhost", "127.0.0.1", "db") or host.endswith(".local")
    is_cloud = any(marker in host for marker in CLOUD_DB_HOSTS)

    if is_cloud and "ssl" not in query and not is_local:
        query["ssl"] = ["require"]

    new_query = urlencode({k: v[0] for k, v in query.items()}, doseq=False)
    return urlunparse(parsed._replace(query=new_query))
