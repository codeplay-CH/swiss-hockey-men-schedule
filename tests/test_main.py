import json

from src.main import (
    apply_sihf_fallback,
    load_previous_sihf_games,
    merge_sihf_fallback_games,
)
from src.models import Game


def _game(
    game_id: str,
    source: str = "sihf",
    date: str = "2026-05-15",
    home_team: str = "SUI",
    away_team: str = "FIN",
    venue: str = "Arena",
) -> Game:
    return Game(
        id=game_id,
        date=date,
        time="20:20",
        starts_at=f"{date}T20:20:00+02:00",
        home_team=home_team,
        away_team=away_team,
        venue=venue,
        tournament="WM",
        score_home=3,
        score_away=2,
        status="completed",
        iihf_game_id="55",
        iihf_event_id=969,
        source=source,
    )


def test_load_previous_sihf_games_strips_iihf_overlay(tmp_path) -> None:
    path = tmp_path / "games.json"
    path.write_text(
        json.dumps(
            [
                _game("sihf-merged", source="sihf+iihf").to_dict(),
                _game("iihf-only", source="iihf").to_dict(),
            ]
        ),
        encoding="utf-8",
    )

    games = load_previous_sihf_games(path)

    assert len(games) == 1
    assert games[0].id == "sihf-merged"
    assert games[0].source == "sihf"
    assert games[0].score_home is None
    assert games[0].score_away is None
    assert games[0].status == "scheduled"
    assert games[0].iihf_game_id is None
    assert games[0].iihf_event_id is None


def test_apply_sihf_fallback_uses_previous_when_live_below_minimum(tmp_path) -> None:
    path = tmp_path / "games.json"
    path.write_text(
        json.dumps(
            [
                _game("previous-1").to_dict(),
                _game(
                    "previous-2",
                    date="2026-05-16",
                    home_team="SUI",
                    away_team="SWE",
                ).to_dict(),
            ]
        ),
        encoding="utf-8",
    )

    games, fallback_count = apply_sihf_fallback(
        [_game("live-1")],
        {"health_check": {"min_sihf_games": 2}},
        path,
    )

    assert fallback_count == 2
    assert [game.id for game in games] == ["live-1", "previous-2"]


def test_merge_sihf_fallback_keeps_new_live_games() -> None:
    previous_games = [
        _game("previous-1"),
        _game("previous-2", date="2026-05-16", home_team="SUI", away_team="SWE"),
    ]
    live_games = [
        _game("live-replacement", venue="Updated Arena"),
        _game("live-new", date="2026-07-30", home_team="SUI Red", away_team="SUI White"),
    ]

    games = merge_sihf_fallback_games(previous_games, live_games)

    assert [game.id for game in games] == [
        "live-replacement",
        "previous-2",
        "live-new",
    ]
    assert games[0].venue == "Updated Arena"


def test_apply_sihf_fallback_keeps_live_when_healthy(tmp_path) -> None:
    games, fallback_count = apply_sihf_fallback(
        [_game("live-1"), _game("live-2")],
        {"health_check": {"min_sihf_games": 2}},
        tmp_path / "missing.json",
    )

    assert fallback_count is None
    assert [game.id for game in games] == ["live-1", "live-2"]
