from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Game:
    id: str
    date: str
    time: str
    starts_at: str
    home_team: str
    away_team: str
    venue: str
    tournament: str
    score_home: int | None = None
    score_away: int | None = None
    status: str = "scheduled"
    iihf_game_id: str | None = None
    iihf_event_id: int | None = None
    source: str = "sihf"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Game:
        return cls(**data)

    def involves_sui(self) -> bool:
        return any(
            team == "SUI" or team.startswith("SUI ")
            for team in (self.home_team, self.away_team)
        )
