from src.fetch_iihf import IihfGame
from src.merge import merge_games
from src.models import Game


def test_merge_matches_scheduled_wm_game_from_hydra() -> None:
    sihf = Game(
        id="sihf-2026-05-26-SUI-FIN-wm",
        date="2026-05-26",
        time="20:20",
        starts_at="2026-05-26T20:20:00+02:00",
        home_team="SUI",
        away_team="FIN",
        venue="Swiss Life Arena, Zurich, SUI",
        tournament="2026 IIHF Ice Hockey World Championship",
    )
    iihf = IihfGame(
        event_id=969,
        game_id=None,
        game_number="55",
        starts_at="2026-05-26T20:20:00+02:00",
        date="2026-05-26",
        time="20:20",
        home_team="SUI",
        away_team="FIN",
        venue="Zurich Swiss Life Arena",
        score_home=None,
        score_away=None,
        status="scheduled",
        tournament="WM",
    )

    merged = merge_games([sihf], [iihf], tolerance_minutes=30)
    assert len(merged) == 1
    game = merged[0]
    assert game.source == "sihf+iihf"
    assert game.iihf_event_id == 969
    assert game.status == "scheduled"


def test_merge_includes_iihf_only_playoff_game() -> None:
    """Playoff games known to IIHF but not yet listed by SIHF must appear in output."""
    iihf = IihfGame(
        event_id=969,
        game_id="12345",
        game_number="59",
        starts_at="2026-05-28T20:20:00+02:00",
        date="2026-05-28",
        time="20:20",
        home_team="SUI",
        away_team="SWE",
        venue="Zurich Swiss Life Arena",
        score_home=None,
        score_away=None,
        status="scheduled",
        tournament="WM 2026",
    )

    merged = merge_games([], [iihf], tolerance_minutes=30)
    assert len(merged) == 1
    game = merged[0]
    assert game.source == "iihf"
    assert game.home_team == "SUI"
    assert game.away_team == "SWE"
    assert game.date == "2026-05-28"
    assert game.iihf_event_id == 969
    assert game.iihf_game_id == "12345"
    assert game.status == "scheduled"


def test_merge_iihf_only_non_sui_game_excluded() -> None:
    """IIHF games without SUI involvement must not appear when SIHF has no entry."""
    iihf = IihfGame(
        event_id=969,
        game_id="99",
        game_number="57",
        starts_at="2026-05-28T16:20:00+02:00",
        date="2026-05-28",
        time="16:20",
        home_team="FIN",
        away_team="CZE",
        venue="Zurich Swiss Life Arena",
        score_home=None,
        score_away=None,
        status="scheduled",
        tournament="WM 2026",
    )

    merged = merge_games([], [iihf])
    assert merged == []


def test_merge_no_duplicate_when_sihf_and_iihf_both_present() -> None:
    """A game present in both SIHF and IIHF must appear exactly once."""
    sihf = Game(
        id="sihf-2026-05-26-SUI-FIN-wm",
        date="2026-05-26",
        time="20:20",
        starts_at="2026-05-26T20:20:00+02:00",
        home_team="SUI",
        away_team="FIN",
        venue="Zurich",
        tournament="WM 2026",
    )
    iihf = IihfGame(
        event_id=969,
        game_id="55",
        game_number="55",
        starts_at="2026-05-26T20:20:00+02:00",
        date="2026-05-26",
        time="20:20",
        home_team="SUI",
        away_team="FIN",
        venue="Zurich Swiss Life Arena",
        score_home=3,
        score_away=2,
        status="completed",
        tournament="WM 2026",
    )

    merged = merge_games([sihf], [iihf])
    assert len(merged) == 1
    assert merged[0].source == "sihf+iihf"


def test_merge_applies_scores_when_available() -> None:
    sihf = Game(
        id="sihf-2026-05-18-GER-SUI-wm",
        date="2026-05-18",
        time="20:20",
        starts_at="2026-05-18T20:20:00+02:00",
        home_team="GER",
        away_team="SUI",
        venue="Zurich",
        tournament="WM",
    )
    iihf = IihfGame(
        event_id=969,
        game_id=None,
        game_number="19",
        starts_at="2026-05-18T20:20:00+02:00",
        date="2026-05-18",
        time="20:20",
        home_team="GER",
        away_team="SUI",
        venue="Zurich Swiss Life Arena",
        score_home=1,
        score_away=6,
        status="completed",
        tournament="WM",
    )

    merged = merge_games([sihf], [iihf])
    game = merged[0]
    assert game.score_home == 1
    assert game.score_away == 6
    assert game.status == "completed"
