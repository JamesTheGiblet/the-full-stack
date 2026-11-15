#!/usr/bin/env python3
"""hal_v3.py — strict layer over hal_v2.py: refuse a stale authoriser score.

Function:
    HAL layer v3 (hardening 6.2). hal.py and hal_v2.py are not edited.

    A seal trusts the authoriser's λ in a signed Leighton score file,
    but nothing checked how old that score was: a score from months ago
    sealed exactly like today's (the-saboteur v2, threat 11). λ decays
    towards neutral, so an old score overstates (or understates) the
    authoriser's standing now.

    `python hal_v3.py seal ... [--max-score-age-days N]` reads the
    score file's `as_of` (ISO 8601 UTC) before anything else and
    refuses, with a named FAILED line and exit 1, a score that is:
      - older than N days (default 30: decided by the VS Code AI on
        James's "yes", 2026-11-15; his to change);
      - dated more than 5 minutes in the future;
      - missing a valid `as_of`.
    A fresh score goes on to hal_v2 (signature check, exit-code fix)
    unchanged. Every other command is hal_v2's.

    Usage: python hal_v3.py seal [hal.py seal's arguments] [--max-score-age-days N]

Tier:     P15 (HAL), v3 layer
Depends:  hal_v2.py
Version:  1.0.0-dev
Licence:  MSL-1.0
"""

import json
import pathlib
import sys
from datetime import datetime, timedelta, timezone

import forge_core
import hal_v2

DEFAULT_MAX_SCORE_AGE_DAYS = 30
FUTURE_SLACK = timedelta(minutes=5)


def score_freshness(score_path, max_age_days=DEFAULT_MAX_SCORE_AGE_DAYS, now=None):
    """None if the score is fresh, else the reason it is refused."""
    now = now or datetime.now(timezone.utc)
    try:
        score = json.loads(pathlib.Path(score_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"authoriser score file unreadable: {score_path}: {exc}"
    as_of = score.get("as_of") if isinstance(score, dict) else None
    try:
        when = forge_core.parse_iso_utc(as_of)
    except (TypeError, ValueError):
        return f"authoriser score has no valid as_of (ISO 8601 UTC): {as_of!r}"
    if when > now + FUTURE_SLACK:
        return f"authoriser score as_of {as_of} is in the future"
    age = now - when
    if age > timedelta(days=max_age_days):
        return (f"authoriser score is stale: as_of {as_of} is {age.days} days old "
                f"(max {max_age_days}; --max-score-age-days)")
    return None


def _take_option(argv, name):
    """Remove `name N` / `name=N` from argv; return (value or None, argv)."""
    out, value, skip = [], None, False
    for i, a in enumerate(argv):
        if skip:
            skip = False
            continue
        if a == name and i + 1 < len(argv):
            value, skip = argv[i + 1], True
        elif a.startswith(name + "="):
            value = a.split("=", 1)[1]
        else:
            out.append(a)
    return value, out


def main():
    raw, rest = _take_option(sys.argv[1:], "--max-score-age-days")
    sys.argv = [sys.argv[0], *rest]
    if rest[:1] == ["seal"]:
        try:
            max_age = DEFAULT_MAX_SCORE_AGE_DAYS if raw is None else int(raw)
            if max_age < 0:
                raise ValueError
        except ValueError:
            print(f"FAILED  --max-score-age-days must be a whole number of days >= 0: {raw!r}")
            return 1
        score, _ = _take_option(rest, "--authoriser-score-file")
        if score is not None:
            reason = score_freshness(score, max_age)
            if reason:
                print(f"FAILED  {reason}")
                return 1
    return hal_v2.main()


if __name__ == "__main__":
    sys.exit(main())
