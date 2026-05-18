from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.fetch_iihf import IihfGame
from src.models import Game
from src.teams import teams_key


def _parse_starts_at(iso_value: str) -> datetime:
    return datetime.fromisoformat(iso_value)


def _minutes_apart(a: datetime, b: datetime) -> float:
    return abs((a - b).total_seconds()) / 60.0


def _has_score(game: IihfGame) -> bool:
    if game.status in ("upcoming", "scheduled"):
        return False
    return game.score_home is not None and game.score_away is not None


def _find_iihf_match(
    sihf_game: Game,
    iihf_games: list[IihfGame],
    tolerance_minutes: int,
) -> IihfGame | None:
    sihf_start = _parse_starts_at(sihf_game.starts_at)
    sihf_teams = teams_key(sihf_game.home_team, sihf_game.away_team)

    candidates: list[IihfGame] = []
    for iihf in iihf_games:
        if teams_key(iihf.home_team, iihf.away_team) != sihf_teams:
            continue
        if iihf.date != sihf_game.date:
            continue
        if _minutes_apart(_parse_starts_at(iihf.starts_at), sihf_start) > tolerance_minutes:
            continue
        candidates.append(iihf)

    if not candidates:
        return None

    candidates.sort(
        key=lambda g: (
            0 if _has_score(g) else 1,
            _minutes_apart(_parse_starts_at(g.starts_at), sihf_start),
        ),
    )
    return candidates[0]


def merge_games(
    sihf_games: list[Game],
    iihf_games: list[IihfGame],
    tolerance_minutes: int = 30,
) -> list[Game]:
    merged: list[Game] = []

    for game in sihf_games:
        if not game.involves_sui():
            continue

        output = Game(**game.to_dict())
        match = _find_iihf_match(output, iihf_games, tolerance_minutes)
        if match:
            if match.game_id:
                output.iihf_game_id = match.game_id
            output.iihf_event_id = match.event_id
            if match.venue:
                output.venue = match.venue
            if _has_score(match):
                output.score_home = match.score_home
                output.score_away = match.score_away
            if match.status:
                output.status = match.status
            output.source = "sihf+iihf"

        merged.append(output)

    merged.sort(key=lambda g: g.starts_at)
    return merged
