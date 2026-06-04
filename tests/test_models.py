from src.models import Game


def _game(home_team: str, away_team: str) -> Game:
    return Game(
        id="game",
        date="2026-07-30",
        time="16:30",
        starts_at="2026-07-30T16:30:00+02:00",
        home_team=home_team,
        away_team=away_team,
        venue="Davos / SUI",
        tournament="Prospect Camp",
    )


def test_involves_sui_accepts_sui_variants() -> None:
    assert _game("SUI Red", "SUI White").involves_sui()


def test_involves_sui_rejects_non_sui_game() -> None:
    assert not _game("FIN", "SWE").involves_sui()
