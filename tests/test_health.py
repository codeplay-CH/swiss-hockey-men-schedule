from src.health import validate_build
from src.models import Game


def _game(game_id: str) -> Game:
    return Game(
        id=game_id,
        date="2026-05-15",
        time="20:20",
        starts_at="2026-05-15T20:20:00+02:00",
        home_team="SUI",
        away_team="FIN",
        venue="Arena",
        tournament="WM",
    )


def test_validate_build_passes_with_enough_games() -> None:
    games = [_game(f"g{i}") for i in range(10)]
    assert validate_build(games, games, {"health_check": {"min_sihf_games": 10}}) == []


def test_validate_build_fails_when_sihf_empty() -> None:
    errors = validate_build([], [_game("g1")], {})
    assert any("SIHF schedule is empty" in err for err in errors)


def test_validate_build_fails_below_minimum() -> None:
    games = [_game("g1") for _ in range(3)]
    errors = validate_build(games, games, {"health_check": {"min_merged_games": 10}})
    assert len(errors) == 2
