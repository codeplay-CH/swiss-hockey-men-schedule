from __future__ import annotations

import json
import sys
from pathlib import Path

from src.build_ics import write_ics
from src.config_loader import ROOT, load_config
from src.fetch_iihf import fetch_all_iihf_games
from src.fetch_sihf import fetch_sihf_schedule
from src.health import log_build_stats, validate_build
from src.merge import merge_games

DATA_PATH = ROOT / "data" / "games.json"
ICS_PATH = ROOT / "public" / "calendar.ics"


def main() -> int:
    config = load_config()
    tz_name = config.get("timezone", "Europe/Zurich")
    sihf_cfg = config["sihf"]
    user_agent = sihf_cfg.get("user_agent", "iihf-swiss-hockey-men-schedule/1.0")
    include_camps = bool(config.get("include_camps", True))
    tolerance = int(config.get("match_time_tolerance_minutes", 30))

    sihf_games = fetch_sihf_schedule(
        url=sihf_cfg["schedule_url"],
        user_agent=user_agent,
        tz_name=tz_name,
        include_camps=include_camps,
    )
    iihf_games = fetch_all_iihf_games(
        events=config.get("iihf_events", []),
        user_agent=user_agent,
        tz_name=tz_name,
    )
    games = merge_games(sihf_games, iihf_games, tolerance_minutes=tolerance)

    log_build_stats(sihf_games, iihf_games, games, config)
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
        calendar_name=config.get("calendar_name", "Schweiz Herren-Nati"),
        tz_name=tz_name,
    )

    print(f"Wrote {len(games)} games to {DATA_PATH} and {ICS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
