# Input01 — Sunday Slow Motion (기준 세트)

Kim Sanghoon, Klangio 채보. 엔진 회귀의 정답 입력이다.

| 파일 | 내용 |
|---|---|
| `Sunday Slow Motion.pdf` | 8페이지 총보 |
| `Sunday Slow Motion.mp3` | 약 209.9초 |
| `Sunday Slow Motion.mid` | 5트랙. 피아노×2, Violin 40 (157음, 첫 35.3s), Cello 42 (163음, 첫 29.7s), Contrabass 43 (85음, 첫 32.0s) |
| `Sunday Slow Motion.musicxml` | 90마디, divisions=12, 4/4. P0~P3 |
| `Sunday Slow Motion.ly` | 같은 조판. 템포·성부 음표. 첼로 `NotesPartTwoStaffZero`, 베이스 `NotesPartThreeStaffZero` (`\clef "bass_8"`) |
| `Sunday Slow Motion.gp5` | Guitar Pro. 코드가 읽지 않음 |

## 시계 (MusicXML)

| 마디 | BPM |
|---|---|
| 1 | 115 |
| 40 | 68 |
| 50 | 100 |
| 61 | 136 |
| 77 | 107 |

`music_end ≈ 202.723s`. 음원보다 약 7초 짧다.

## 재구현 시 이 폴더로 확인할 것

- 타임라인 90마디, 끝 202.7초 근처
- 바이올린 LCS 약 97%, 온셋 약 1~2%
- 첼로 LCS 약 95%, 온셋 0%, m23 겹음 A2+C3
- 베이스 음표 가방 85/85, 온셋 약 1%, 첫 음 D3 (MIDI 50)

GUI 자동 채움은 **오늘 날짜** Input01을 우선한다. 오늘은 2026-08-15 이므로 창은 `2026-08-15/Input01` 을 연다. 이 폴더로 돌리려면 찾아보기로 지정하거나 `test_render.py` 를 쓴다.
