from __future__ import annotations

from typing import Any

from src.fetch_iihf import IihfGame
from src.models import Game


def log_build_stats(
    sihf_games: list[Game],
    iihf_games: list[IihfGame],
    merged_games: list[Game],
    config: dict[str, Any],
) -> None:
    with_iihf = sum(1 for game in merged_games if game.source == "sihf+iihf")
    with_scores = sum(
        1
        for game in merged_games
        if game.score_home is not None and game.score_away is not None
    )

    print(f"SIHF: {len(sihf_games)} games")
    for event in config.get("iihf_events", []):
        event_id = int(event["id"])
        name = event.get("name", str(event_id))
        count = sum(1 for game in iihf_games if game.event_id == event_id)
        print(f"IIHF {name} ({event_id}): {count} SUI games")
    print(f"IIHF total: {len(iihf_games)} SUI games")
    print(
        f"Merged: {len(merged_games)} games "
        f"({with_iihf} with IIHF, {with_scores} with scores)"
    )


def validate_build(
    sihf_games: list[Game],
    merged_games: list[Game],
    config: dict[str, Any],
) -> list[str]:
    health = config.get("health_check") or {}
    min_sihf = int(health.get("min_sihf_games", 10))
    min_merged = int(health.get("min_merged_games", 10))

    errors: list[str] = []

    if not sihf_games:
        errors.append("SIHF schedule is empty (parser or source may be broken)")
    elif len(sihf_games) < min_sihf:
        errors.append(
            f"SIHF returned only {len(sihf_games)} games (minimum {min_sihf})"
        )

    if not merged_games:
        errors.append("Merged schedule is empty")
    elif len(merged_games) < min_merged:
        errors.append(
            f"Merged schedule has only {len(merged_games)} games (minimum {min_merged})"
        )

    return errors
