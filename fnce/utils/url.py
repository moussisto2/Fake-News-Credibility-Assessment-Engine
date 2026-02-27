from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse


_DOMAIN_RE = re.compile(r"^[a-z0-9.-]+\.[a-z]{2,}$", re.IGNORECASE)


def extract_domain(url: str) -> str:
    """
    Extract normalized domain from a URL:
      - strips scheme
      - strips path/query/fragment
      - strips leading 'www.'
    Returns "" if not parseable.
    """
    if not url:
        return ""
    u = url.strip()
    if not u:
        return ""

    # Allow user to paste "example.com/article"
    if "://" not in u:
        u = "https://" + u

    try:
        parsed = urlparse(u)
        host = (parsed.netloc or "").strip().lower()
        if not host:
            return ""
        if host.startswith("www."):
            host = host[4:]
        # Strip possible port
        host = host.split(":")[0].strip()
        if not host or not _DOMAIN_RE.match(host):
            return ""
        return host
    except Exception:
        return ""


def _data_path(filename: str) -> Path:
    """
    Locate fnce/data/<filename> on filesystem.
    Works when running from repo (Streamlit / python -m).
    """
    # fnce/utils/url.py -> fnce/utils -> fnce
    base = Path(__file__).resolve().parents[1]
    return base / "data" / filename


@lru_cache(maxsize=1)
def load_source_domains() -> dict[str, set[str]]:
    """
    Loads domain allowlists from fnce/data/source_domains.json
    Returns a dict of sets: { "reputable": {...}, "sports_reputable": {...} }
    """
    path = _data_path("source_domains.json")
    if not path.exists():
        # Safe fallback: empty lists => everything becomes unverified unless manual toggle is used
        return {"reputable": set(), "sports_reputable": set()}

    raw = json.loads(path.read_text(encoding="utf-8"))
    reputable = set(d.lower().strip() for d in raw.get("reputable", []) if isinstance(d, str))
    sports_rep = set(d.lower().strip() for d in raw.get("sports_reputable", []) if isinstance(d, str))

    return {"reputable": reputable, "sports_reputable": sports_rep}


def is_reputable_domain(domain: str) -> bool:
    """
    Strong positive if domain is in reputable OR sports_reputable allowlists.
    """
    if not domain:
        return False
    domain = domain.lower().strip()
    db = load_source_domains()
    return (domain in db["reputable"]) or (domain in db["sports_reputable"])
