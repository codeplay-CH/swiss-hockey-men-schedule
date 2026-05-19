from src.fetch_iihf import _parse_hydra_row


def test_parse_hydra_row_completed_game() -> None:
    cells = [
        "18 May 2026, Mon 20:20 GMT+2",
        "Zurich Swiss Life Arena",
        "19 PRE",
        "GER",
        "-",
        "SUI",
        "1 - 6 ( 0 - 0 , 0 - 5 , 1 - 1 )",
        "Game Completed",
    ]
    game = _parse_hydra_row(cells, 969, "WM", "Europe/Zurich")
    assert game is not None
    assert game.home_team == "GER"
    assert game.away_team == "SUI"
    assert game.score_home == 1
    assert game.score_away == 6
    assert game.status == "completed"
    assert game.date == "2026-05-18"


def test_parse_hydra_row_scheduled_game() -> None:
    cells = [
        "26 May 2026, Tue 20:20 GMT+2",
        "Zurich Swiss Life Arena",
        "55 PRE",
        "SUI",
        "-",
        "FIN",
        "Scheduled",
    ]
    game = _parse_hydra_row(cells, 969, "WM", "Europe/Zurich")
    assert game is not None
    assert game.home_team == "SUI"
    assert game.away_team == "FIN"
    assert game.score_home is None
    assert game.score_away is None
    assert game.status == "scheduled"
    assert game.game_number == "55"
    assert game.starts_at == "2026-05-26T20:20:00+02:00"


def test_parse_hydra_row_too_few_cells() -> None:
    assert _parse_hydra_row(["26 May 2026, Tue 20:20"], 969, "WM", "Europe/Zurich") is None
