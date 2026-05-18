# Schweiz Herren-Nati – ICS-Kalender

Abonnierbarer Kalender mit Spielplan und Resultaten der Schweizer Eishockey-Nationalmannschaft (Herren).

**Kein offizielles Angebot** von SIHF oder IIHF. Daten stammen aus öffentlich zugänglichen Quellen und können sich jederzeit ändern.

## Kalender abonnieren

GitHub Pages (Organisation `codeplay-CH`):

```
https://codeplay-ch.github.io/iihf-swiss-hockey-men-schedule/calendar.ics
```

Übersicht: https://codeplay-ch.github.io/iihf-swiss-hockey-men-schedule/

Wichtig: Die Root-URL ohne `calendar.ics` liefert keine Kalenderdatei.

### Google Kalender

1. «Andere Kalender» → «Per URL»
2. URL oben einfügen → «Kalender hinzufügen»

### Apple Kalender

1. «Abo hinzufügen …»
2. URL einfügen

Der Kalender wird automatisch aktualisiert, wenn die GitHub Action neue Daten schreibt.

## Datenquellen

| Quelle | Inhalt |
|--------|--------|
| [SIHF Spielplan](https://m.sihf.ch/de/national-teams/mens-national-team/schedule/) | Spielplan (EHT, Olympia, WM-Vorbereitung, WM, …) |
| [IIHF Realtime API](https://realtime.iihf.com/gamestate/GetLatestScoresState/{eventId}) | Live-Resultate (undokumentiert) |
| [IIHF Hydra Stats](https://stats.iihf.com/Hydra/) | Resultate für abgeschlossene IIHF-Spiele |

**Resultate automatisch:** IIHF-Turniere (Olympia `991`, WM `969`).

**Nur Spielplan:** EHT, WM-Vorbereitung, interne Camps (SIHF liefert keine Scores).

## Lokal ausführen

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

Ausgabe: `data/games.json`, `public/calendar.ics`

## Konfiguration

[`config/events.yaml`](config/events.yaml) – SIHF-URL, IIHF-Event-IDs, Zeitzone, Camps ein-/ausblenden.

## Lizenz

MIT (siehe LICENSE, falls vorhanden). Nutzung auf eigene Verantwortung.
