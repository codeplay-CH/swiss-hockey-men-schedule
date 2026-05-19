from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from src.teams import normalize_team_code

REALTIME_URL = "https://realtime.iihf.com/gamestate/GetLatestScoresState/{event_id}"
DATE_TIME_RE = re.compile(
    r"(\d{1,2}\s+\w+\s+\d{4}),\s*\w+\s+(\d{1,2}:\d{2})",
)
SCORE_RE = re.compile(r"^(\d+)\s*-\s*(\d+)")


@dataclass
class IihfGame:
    event_id: int
    game_id: str | None
    game_number: str | None
    starts_at: str
    date: str
    time: str
    home_team: str
    away_team: str
    venue: str
    score_home: int | None
    score_away: int | None
    status: str
    tournament: str


def _parse_local_datetime(date_part: str, time_part: str, tz_name: str) -> datetime:
    from zoneinfo import ZoneInfo

    dt = datetime.strptime(f"{date_part} {time_part}", "%d %b %Y %H:%M")
    return dt.replace(tzinfo=ZoneInfo(tz_name))


def _safe_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_realtime_game(raw: dict, event_id: int, tournament: str, tz_name: str) -> IihfGame | None:
    from zoneinfo import ZoneInfo

    home = raw.get("HomeTeam") or {}
    guest = raw.get("GuestTeam") or {}
    home_code = normalize_team_code(home.get("TeamCode", ""))
    away_code = normalize_team_code(guest.get("TeamCode", ""))
    if home_code in ("", "TBD") or away_code in ("", "TBD"):
        return None

    utc_raw = raw.get("GameDateTimeUTC") or raw.get("GameDateTime")
    if not utc_raw:
        return None

    utc_text = utc_raw.replace("Z", "+00:00")
    if "+" not in utc_text and "T" in utc_text:
        utc_text += "+00:00"
    starts_utc = datetime.fromisoformat(utc_text)
    starts_local = starts_utc.astimezone(ZoneInfo(tz_name))

    return IihfGame(
        event_id=event_id,
        game_id=str(raw.get("GameId")) if raw.get("GameId") else None,
        game_number=str(raw.get("GameNumber")) if raw.get("GameNumber") else None,
        starts_at=starts_local.isoformat(),
        date=starts_local.date().isoformat(),
        time=starts_local.strftime("%H:%M"),
        home_team=home_code,
        away_team=away_code,
        venue=(raw.get("Venue") or "").strip(),
        score_home=_safe_int(home.get("Points")),
        score_away=_safe_int(guest.get("Points")),
        status=(raw.get("Status") or "scheduled").lower(),
        tournament=tournament,
    )


def _parse_hydra_row(cells: list[str], event_id: int, tournament: str, tz_name: str) -> IihfGame | None:
    # Completed rows: date, venue, round, home, "-", away, score, status (8+).
    # Scheduled rows: same but only "Scheduled" (or similar) after away (7).
    if len(cells) < 7:
        return None

    date_match = DATE_TIME_RE.search(cells[0])
    if not date_match:
        return None

    venue = cells[1] if len(cells) > 1 else ""
    round_info = cells[2] if len(cells) > 2 else ""

    home_idx = 3
    if cells[home_idx] == "-":
        return None
    home = normalize_team_code(cells[home_idx])
    away = normalize_team_code(cells[home_idx + 2] if cells[home_idx + 1] == "-" else cells[home_idx + 1])
    if home in ("TBD", "QF", "W(QF)", "L(SF)", "W(SF)") or away in ("TBD", "QF", "W(QF)", "L(SF)", "W(SF)"):
        return None

    result_idx = home_idx + 3
    result_text = cells[result_idx] if len(cells) > result_idx else ""
    if len(cells) > result_idx + 1:
        status_text = cells[result_idx + 1]
    elif SCORE_RE.match(result_text.strip()):
        status_text = "game completed"
    else:
        status_text = result_text
        result_text = ""

    score_home: int | None = None
    score_away: int | None = None
    score_match = SCORE_RE.match(result_text.strip())
    if score_match:
        score_home = int(score_match.group(1))
        score_away = int(score_match.group(2))

    status = status_text.strip().lower().replace(" ", "_")
    if status == "game_completed":
        status = "completed"
    elif status == "pre_game_ended":
        status = "upcoming"

    starts_local = _parse_local_datetime(date_match.group(1), date_match.group(2), tz_name)
    game_number = round_info.split()[0] if round_info else None

    return IihfGame(
        event_id=event_id,
        game_id=None,
        game_number=game_number,
        starts_at=starts_local.isoformat(),
        date=starts_local.date().isoformat(),
        time=starts_local.strftime("%H:%M"),
        home_team=home,
        away_team=away,
        venue=venue,
        score_home=score_home,
        score_away=score_away,
        status=status,
        tournament=tournament,
    )


def _row_cells(tr) -> list[str]:
    return [td.get_text(" ", strip=True) for td in tr.find_all("td") if td.get_text(strip=True)]


def _is_game_row(cells: list[str]) -> bool:
    if not cells:
        return False
    first = cells[0]
    if "GAMES & RESULTS" in first or len(first) > 80:
        return False
    return bool(DATE_TIME_RE.search(first))


def fetch_hydra_games(
    hydra_url: str,
    event_id: int,
    tournament: str,
    user_agent: str,
    tz_name: str,
) -> list[IihfGame]:
    headers = {"User-Agent": user_agent}
    response = httpx.get(hydra_url, headers=headers, timeout=30.0, follow_redirects=True)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    games: list[IihfGame] = []
    for tr in soup.find_all("tr"):
        cells = _row_cells(tr)
        if not _is_game_row(cells):
            continue

        compact = [cells[0], cells[1] if len(cells) > 1 else ""]
        rest = cells[2:]
        if rest and re.match(r"^\d+\s+\w+", rest[0]):
            compact.append(rest[0])
            rest = rest[1:]
        if len(rest) < 3 or rest[1] != "-":
            continue

        compact.extend(rest[:4])
        if len(rest) > 4:
            compact.extend(rest[4:6])

        parsed = _parse_hydra_row(compact, event_id, tournament, tz_name)
        if parsed:
            games.append(parsed)

    return games


def fetch_realtime_games(
    event_id: int,
    tournament: str,
    user_agent: str,
    tz_name: str,
) -> list[IihfGame]:
    headers = {"User-Agent": user_agent}
    url = REALTIME_URL.format(event_id=event_id)
    response = httpx.get(url, headers=headers, timeout=30.0)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        return []

    games: list[IihfGame] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        parsed = _parse_realtime_game(item, event_id, tournament, tz_name)
        if parsed:
            games.append(parsed)
    return games


def fetch_all_iihf_games(
    events: list[dict],
    user_agent: str,
    tz_name: str,
) -> list[IihfGame]:
    by_key: dict[tuple[int, str, str, str], IihfGame] = {}

    for event in events:
        event_id = int(event["id"])
        tournament = event["name"]
        hydra_url = event["hydra_url"]

        for game in fetch_hydra_games(hydra_url, event_id, tournament, user_agent, tz_name):
            if game.home_team != "SUI" and game.away_team != "SUI":
                continue
            key = (event_id, game.date, game.home_team, game.away_team)
            by_key[key] = game

        for game in fetch_realtime_games(event_id, tournament, user_agent, tz_name):
            if game.home_team != "SUI" and game.away_team != "SUI":
                continue
            key = (event_id, game.date, game.home_team, game.away_team)
            existing = by_key.get(key)
            if existing:
                if game.game_id:
                    existing.game_id = game.game_id
                if game.score_home is not None:
                    existing.score_home = game.score_home
                if game.score_away is not None:
                    existing.score_away = game.score_away
                if game.status:
                    existing.status = game.status
                if game.venue:
                    existing.venue = game.venue
            else:
                by_key[key] = game

    return list(by_key.values())
