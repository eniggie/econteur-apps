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

- We Gonna Make It (Colored Skin, 2022-07-07, 155.1 s, Apple 1725930506): no verified master; checked bl (1).wav: 156.9 s, preview match 0.16 (cached); LOAD_2026-09-02 01-14-37_RECORDING.wav: 156.7 s, preview match 0.15 (cached); LOAD_2026-09-02 01-17-31_RECORDING.wav: 156.8 s, preview match 0.17 (cached); LOAD_2026-09-02 01-42-42_RECORDING.wav: 153.2 s, preview match 0.15 (cached) (+14 more)
- Find Happiness and Peace (Find Happiness and Peace, 2022-07-22, 191.9 s, Apple 1635610285): no verified master; checked NIGERIANS.wav: 190.4 s, preview match 0.25 @ 78s; NIGERIANS.wav: 190.4 s, preview match 0.29 @ 141s; YOU ARE WHAT YOU EAT MIX.wav: 191.9 s, preview match 0.34 @ 136s; YOU ARE WHAT YOU EAT1.wav: 191.9 s, preview match 0.32 @ 136s; NIGERIA.wav: 190.4 s, preview match 0.25 (cached); PAPARAZZI.wav: 191.8 s, preview match 0.26 (cached) (+22 more)
- Angel I Need (Colored Skin, 2022-11-11, 214.4 s, Apple 1725930516): no verified master; checked BLACK GOLD.wav: 215.0 s, preview match 0.15 @ 117s; LOVE TO SOUL xxx.WAV: 214.9 s, preview match 0.17 @ 4s; MY HEART.wav: 214.3 s, preview match 0.16 @ 151s; DON'T LET NOBODY.wav: 214.1 s, preview match 0.15 @ 166s; TURN BY TURN (RELOADED).wav: 213.4 s, preview match 0.16 @ 170s; 8. GET YOUR MONEY RIGHT.wav: 216.4 s, preview match 0.20 (cached) (+20 more)
- Where You Dey (Colored Skin, 2024-02-24, 212.6 s, Apple 1725930508): no verified master; checked MY HEART.wav: 214.3 s, preview match 0.26 @ 3s; DON'T LET NOBODY.wav: 214.1 s, preview match 0.18 @ 43s; TURN BY TURN (RELOADED).wav: 213.4 s, preview match 0.16 @ 51s; 1_Money  (18)_(Bass).wav: 211.8 s, preview match 0.19 (cached); 1_Money  (18)_(Drums).wav: 211.8 s, preview match 0.19 (cached); 1_Money  (18)_(Other).wav: 211.8 s, preview match 0.24 (cached) (+10 more)
- Money Too Good (Colored Skin, 2024-02-24, 218.0 s, Apple 1725930511): no verified master; checked LIVE YOUR LIFE.wav: 217.4 s, preview match 0.13 @ 18s; Trauma.wav: 219.9 s, preview match 0.14 @ 133s; WE ARE AFRICANS.wav: 218.2 s, preview match 0.12 @ 126s; 8. GET YOUR MONEY RIGHT.wav: 216.4 s, preview match 0.19 (cached); bbg.wav: 217.9 s, preview match 0.17 (cached); bbq.wav: 216.1 s, preview match 0.14 (cached) (+10 more)
- Mama Told Me (Colored Skin, 2024-02-24, 208.2 s, Apple 1725930512): no verified master; checked RAIMZY.WAV: 208.5 s, preview match 0.20 @ 150s; Trauma (1).wav: 208.6 s, preview match 0.24 @ 117s; 8. LEGACY OVER LUXURY .wav: 209.2 s, preview match 0.24 (cached); 2. TWO THOUSAND AND ELEVEN.wav: 209.1 s, preview match 0.24 (cached); 8. SUCCESS IS GIVEN.wav: 207.8 s, preview match 0.19 (cached); 2. MAMA ( FOR OUR MOTHERS ).wav: 208.0 s, preview match 0.28 (cached) (+29 more)
- Turn by Turn (Colored Skin, 2024-02-24, 200.7 s, Apple 1725930515): no verified master; checked LET ME LOVE (DEMO VERSION ACOUSTIC).wav: 200.9 s, preview match 0.18 (cached); LET ME LOVE (DEMO VERSION).wav: 200.9 s, preview match 0.14 (cached); OPEN YOUR HART (DEMO VERSION).wav: 198.9 s, preview match 0.14 (cached); OPEN YOUR HART(DEMO VERSION ACOUSTIC).wav: 198.9 s, preview match 0.17 (cached); 4. FUCK YOU TO ALL MY EXES.wav: 201.3 s, preview match 0.16 (cached); FUCK YOU EXES (RAIMZY VOICE).WAV: 201.0 s, preview match 0.15 (cached) (+23 more)
- Manager (Colored Skin, 2024-02-24, 196.6 s, Apple 1725930517): no verified master; checked You Are What You Eat 2.wav: 197.7 s, preview match 0.18 @ 146s; Love Got Subscription.wav: 197.2 s, preview match 0.15 @ 65s; I’M SAYING SORRY (RELOADED).wav: 198.5 s, preview match 0.22 @ 110s; 4. WAR OR PEACE.wav: 197.9 s, preview match 0.18 (cached); 6. I’M SO SICK OF IT.wav: 197.3 s, preview match 0.15 (cached); SUCCESS IS GIVEN_2025-05-16 23-30-42_Insert 8.wav: 195.3 s, preview match 0.16 (cached) (+11 more)
- Osalobua (OSALOBUA, 2025-08-08, 191.0 s, Apple 1812070055): no verified master; checked NIGERIANS.wav: 190.4 s, preview match 0.29 @ 2s; NIGERIANS.wav: 190.4 s, preview match 0.23 @ 37s; YOU ARE WHAT YOU EAT MIX.wav: 191.9 s, preview match 0.35 @ 122s; YOU ARE WHAT YOU EAT1.wav: 191.9 s, preview match 0.29 @ 122s; NIGERIA.wav: 190.4 s, preview match 0.29 (cached); PAPARAZZI.wav: 191.8 s, preview match 0.22 (cached) (+19 more)

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
