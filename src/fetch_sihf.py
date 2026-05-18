from __future__ import annotations

import re
from datetime import datetime
from html import unescape
from zoneinfo import ZoneInfo

import httpx

from src.models import Game
from src.teams import normalize_team_code, parse_matchup

DATE_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$")
TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


def _make_game_id(date_iso: str, home: str, away: str, tournament: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", tournament.lower()).strip("-")[:40]
    return f"sihf-{date_iso}-{home}-{away}-{slug}"


def _parse_local_datetime(date_iso: str, time_hm: str, tz_name: str) -> datetime:
    year, month, day = map(int, date_iso.split("-"))
    hour, minute = map(int, time_hm.split(":"))
    return datetime(year, month, day, hour, minute, tzinfo=ZoneInfo(tz_name))


def fetch_sihf_schedule(
    url: str,
    user_agent: str,
    tz_name: str,
    include_camps: bool = True,
) -> list[Game]:
    headers = {"User-Agent": user_agent}
    response = httpx.get(url, headers=headers, timeout=30.0, follow_redirects=True)
    response.raise_for_status()
    html = response.text

    games: list[Game] = []
    parts = re.split(r"<h4[^>]*>", html, flags=re.IGNORECASE)[1:]

    for part in parts:
        title_match = re.match(r"(.*?)</h4>", part, flags=re.IGNORECASE | re.DOTALL)
        if not title_match:
            continue

        tournament = unescape(re.sub(r"<[^>]+>", "", title_match.group(1))).strip()
        tournament = re.sub(r"\s+", " ", tournament)

        if not include_camps and (
            "prospect camp" in tournament.lower() or "media day" in tournament.lower()
        ):
            continue

        body = part[title_match.end() :]
        for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", body, flags=re.IGNORECASE | re.DOTALL):
            cells = [
                unescape(re.sub(r"<[^>]+>", "", cell)).strip()
                for cell in re.findall(
                    r"<td[^>]*>(.*?)</td>", row_html, flags=re.IGNORECASE | re.DOTALL
                )
            ]
            if len(cells) < 4:
                continue

            date_raw, time_raw, matchup_raw, venue = cells[0], cells[1], cells[2], cells[3]
            date_match = DATE_RE.match(date_raw)
            time_match = TIME_RE.match(time_raw)
            if not date_match or not time_match:
                continue

            matchup = parse_matchup(matchup_raw)
            if not matchup:
                continue

            home, away = matchup
            day, month, year = date_match.groups()
            date_iso = f"{year}-{month}-{day}"
            time_hm = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
            starts_at = _parse_local_datetime(date_iso, time_hm, tz_name).isoformat()

            games.append(
                Game(
                    id=_make_game_id(date_iso, home, away, tournament),
                    date=date_iso,
                    time=time_hm,
                    starts_at=starts_at,
                    home_team=home,
                    away_team=away,
                    venue=venue,
                    tournament=tournament,
                    source="sihf",
                )
            )

    return games
