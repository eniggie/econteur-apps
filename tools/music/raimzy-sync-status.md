# RAIMZY in-game music sync: status

Written by `tools/music/sync_raimzy.py` (runs daily at 09:30 and at login via
`~/Library/LaunchAgents/com.econteur.raimzy-sync.plist`; log: `~/Library/Logs/raimzy-sync.log`).
Rule: Apple `notExplicit` only, no instrumentals, released only, master within 2 s of Apple's length
and matching Apple's preview.

## In both games (14)

- `raimaction.json`: 14 tracks
- `raimstorm.json`: 14 tracks

## Waiting for audio (9)

Clean, released songs with no verified master on this Mac yet. Drop the released WAV into
iCloud Drive `MY SONGS/<album>/` and the next run adds it to both games.

- We Gonna Make It (Colored Skin, 2022-07-07, 155.1 s, Apple 1725930506): no released master on this Mac yet
- Find Happiness and Peace (Find Happiness and Peace, 2022-07-22, 191.9 s, Apple 1635610285): no released master on this Mac yet
- Angel I Need (Colored Skin, 2022-11-11, 214.4 s, Apple 1725930516): no released master on this Mac yet
- Where You Dey (Colored Skin, 2024-02-24, 212.6 s, Apple 1725930508): no released master on this Mac yet
- Money Too Good (Colored Skin, 2024-02-24, 218.0 s, Apple 1725930511): no released master on this Mac yet
- Mama Told Me (Colored Skin, 2024-02-24, 208.2 s, Apple 1725930512): no released master on this Mac yet
- Turn by Turn (Colored Skin, 2024-02-24, 200.7 s, Apple 1725930515): no released master on this Mac yet
- Manager (Colored Skin, 2024-02-24, 196.6 s, Apple 1725930517): no released master on this Mac yet
- Osalobua (OSALOBUA, 2025-08-08, 191.0 s, Apple 1812070055): no released master on this Mac yet

## Excluded (10)

- Colored Skin (Colored Skin): Apple marks it explicit
- Africans Unite (Colored Skin): Apple marks it explicit
- Bad Energy (Colored Skin): Apple marks it explicit
- In My Country (Colored Skin): Apple marks it explicit
- F**k You to All My Exes (THE HEARTBEATBOY): Apple marks it explicit
- Never About the Money (THE HEARTBEATBOY): Apple marks it explicit
- I'm So Sick of It (THE HEARTBEATBOY): Apple marks it explicit
- Bitch I'm Black (THE HEARTBEATBOY): Apple marks it explicit
- Legacy (THE HEARTBEATBOY): Apple marks it explicit
- Deworm (THE HEARTBEATBOY): Apple marks it explicit
