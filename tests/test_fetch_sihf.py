from __future__ import annotations

import httpx
import pytest

from src.fetch_sihf import fetch_sihf_schedule

SIHF_HTML_FIXTURE = """
<html><body>
<h4>15.05.2026 - 31.05.2026 IIHF Ice Hockey World Championship</h4>
<table>
<tr>
  <td>26.05.2026</td>
  <td>20:20</td>
  <td>SUI - FIN</td>
  <td>Swiss Life Arena, Zurich, SUI</td>
</tr>
</table>
<h4>01.01.2026 Prospect Camp</h4>
<table>
<tr>
  <td>02.01.2026</td>
  <td>10:00</td>
  <td>SUI - FIN</td>
  <td>Camp</td>
</tr>
</table>
</body></html>
"""


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


def test_fetch_sihf_parses_table_row(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, **kwargs: object) -> _FakeResponse:
        return _FakeResponse(SIHF_HTML_FIXTURE)

    monkeypatch.setattr(httpx, "get", fake_get)

    games = fetch_sihf_schedule(
        "https://example.test/schedule",
        user_agent="test",
        tz_name="Europe/Zurich",
        include_camps=False,
    )

    assert len(games) == 1
    game = games[0]
    assert game.home_team == "SUI"
    assert game.away_team == "FIN"
    assert game.date == "2026-05-26"
    assert game.time == "20:20"
    assert game.venue == "Swiss Life Arena, Zurich, SUI"


def test_fetch_sihf_skips_camps_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, **kwargs: object) -> _FakeResponse:
        return _FakeResponse(SIHF_HTML_FIXTURE)

    monkeypatch.setattr(httpx, "get", fake_get)

    games = fetch_sihf_schedule(
        "https://example.test/schedule",
        user_agent="test",
        tz_name="Europe/Zurich",
        include_camps=False,
    )
    assert all("prospect camp" not in g.tournament.lower() for g in games)
