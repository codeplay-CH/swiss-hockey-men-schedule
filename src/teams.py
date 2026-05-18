from __future__ import annotations

import re

# IIHF / SIHF three-letter codes used in matching.
TEAM_ALIASES: dict[str, str] = {
    "UNITED STATES": "USA",
    "US": "USA",
    "SWITZERLAND": "SUI",
    "CZECHIA": "CZE",
    "CZECH REPUBLIC": "CZE",
    "GREAT BRITAIN": "GBR",
    "GERMANY": "GER",
    "FINLAND": "FIN",
    "SWEDEN": "SWE",
    "SLOVAKIA": "SVK",
    "SLOVENIA": "SLO",
    "CANADA": "CAN",
    "LATVIA": "LAT",
    "AUSTRIA": "AUT",
    "HUNGARY": "HUN",
    "NORWAY": "NOR",
    "DENMARK": "DEN",
    "ITALY": "ITA",
    "FRANCE": "FRA",
}


def normalize_team_code(raw: str) -> str:
    text = re.sub(r"\s+", " ", raw.strip().upper())
    if text in TEAM_ALIASES:
        return TEAM_ALIASES[text]
    if len(text) == 3 and text.isalpha():
        return text
    if text.startswith("SUI "):
        return text
    return text


def parse_matchup(description: str) -> tuple[str, str] | None:
    text = re.sub(r"\s+", " ", description.strip())
    for sep in (" - ", " – ", " — "):
        if sep in text:
            home, away = text.split(sep, 1)
            return normalize_team_code(home), normalize_team_code(away)
    return None


def teams_key(home: str, away: str) -> frozenset[str]:
    return frozenset({normalize_team_code(home), normalize_team_code(away)})
