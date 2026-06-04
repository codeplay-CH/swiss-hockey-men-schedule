from __future__ import annotations

import json
import sys
from pathlib import Path

from src.build_ics import write_ics
from src.config_loader import ROOT, load_config
from src.discover_iihf import resolve_iihf_events, schedule_urls_by_event_id
from src.fetch_iihf import fetch_all_iihf_games
from src.fetch_sihf import fetch_sihf_schedule
from src.health import build_warnings, log_build_stats, validate_build
from src.merge import merge_games
from src.models import Game

DATA_PATH = ROOT / "data" / "games.json"
ICS_PATH = ROOT / "public" / "calendar.ics"


def _min_sihf_games(config: dict) -> int:
    health = config.get("health_check") or {}
    return int(health.get("min_sihf_games", 10))


def _strip_iihf_overlay(game: Game) -> Game:
    output = Game(**game.to_dict())
    output.score_home = None
    output.score_away = None
    output.status = "scheduled"
    output.iihf_game_id = None
    output.iihf_event_id = None
    output.source = "sihf"
    return output


def load_previous_sihf_games(path: Path = DATA_PATH) -> list[Game]:
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    games: list[Game] = []
    for item in data:
        if item.get("source") not in {"sihf", "sihf+iihf"}:
            continue
        games.append(_strip_iihf_overlay(Game.from_dict(item)))
    return games


def apply_sihf_fallback(
    live_sihf_games: list[Game],
    config: dict,
    previous_path: Path = DATA_PATH,
) -> tuple[list[Game], int | None]:
    min_sihf = _min_sihf_games(config)
    if len(live_sihf_games) >= min_sihf:
        return live_sihf_games, None

    previous_sihf_games = load_previous_sihf_games(previous_path)
    if len(previous_sihf_games) >= min_sihf:
        return previous_sihf_games, len(previous_sihf_games)

    return live_sihf_games, None


def main() -> int:
    config = load_config()
    tz_name = config.get("timezone", "Europe/Zurich")
    sihf_cfg = config["sihf"]
    user_agent = sihf_cfg.get("user_agent", "iihf-swiss-hockey-men-schedule/1.0")
    include_camps = bool(config.get("include_camps", True))
    tolerance = int(config.get("match_time_tolerance_minutes", 30))

    live_sihf_games = fetch_sihf_schedule(
        url=sihf_cfg["schedule_url"],
        user_agent=user_agent,
        tz_name=tz_name,
        include_camps=include_camps,
    )
    sihf_games, fallback_count = apply_sihf_fallback(live_sihf_games, config)
    if fallback_count is not None:
        print(
            f"WARNING: SIHF live returned only {len(live_sihf_games)} games; "
            f"using {fallback_count} previous SIHF games from {DATA_PATH}"
        )

    iihf_events = resolve_iihf_events(config, sihf_games, user_agent)
    discovered = [event for event in iihf_events if event.get("discovered")]
    if discovered:
        for event in discovered:
            print(
                f"Discovered IIHF event {event['id']}: "
                f"{event.get('hydra_title', event['name'])}"
            )

    iihf_games = fetch_all_iihf_games(
        events=iihf_events,
        user_agent=user_agent,
        tz_name=tz_name,
    )
    games = merge_games(sihf_games, iihf_games, tolerance_minutes=tolerance)

    log_build_stats(sihf_games, iihf_games, games, config)
    for message in build_warnings(live_sihf_games, games, config):
        print(f"WARNING: {message}")

    errors = validate_build(sihf_games, games, config)
    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps([game.to_dict() for game in games], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    write_ics(
        games,
        ICS_PATH,
        calendar_name=config.get("calendar_name", "Swiss Hockey Men"),
        tz_name=tz_name,
        iihf_schedule_urls=schedule_urls_by_event_id(iihf_events),
    )

    print(f"Wrote {len(games)} games to {DATA_PATH} and {ICS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
