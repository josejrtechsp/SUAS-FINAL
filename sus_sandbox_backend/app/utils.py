from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

RE_COMP = re.compile(r"^\d{4}-\d{2}$")


def current_competencia(d: Optional[date] = None) -> str:
    d = d or date.today()
    return f"{d.year:04d}-{d.month:02d}"


def valid_competencia(s: str) -> bool:
    return bool(RE_COMP.match(s or ""))


def parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def today() -> date:
    return date.today()


def safe_filename(name: str) -> str:
    name = (name or "").strip()
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    if not name:
        name = "file"
    return name[:160]
