from src.teams import normalize_team_code, parse_matchup, teams_key


def test_normalize_team_code_aliases_and_iso3() -> None:
    assert normalize_team_code("Switzerland") == "SUI"
    assert normalize_team_code("  finland  ") == "FIN"
    assert normalize_team_code("CAN") == "CAN"


def test_parse_matchup_hyphen_variants() -> None:
    assert parse_matchup("SUI - FIN") == ("SUI", "FIN")
    assert parse_matchup("USA – SUI") == ("USA", "SUI")
    assert parse_matchup("invalid") is None


def test_teams_key_is_order_independent() -> None:
    assert teams_key("SUI", "FIN") == teams_key("FIN", "SUI")
