# InputData — 날짜별 입력 세트

채보 결과(PDF, 음원, MIDI, MusicXML, LilyPond, Guitar Pro)를 곡·날짜 단위로 둔다. 프로그램은 여기를 읽어 영상을 만든다. 출력은 쓰지 않는다.

## 폴더 규칙

```
InputData/
  YYYY-MM-DD/          ← 작업을 시작한 날짜
    Input01/           ← 그날을 첫 번째 세트
      곡이름.pdf
      곡이름.mp3
      곡이름.mid
      곡이름.musicxml
      곡이름.ly
      곡이름.gp5       ← 선택. 엔진은 직접 읽지 않음
    Input02/           ← 둘째 세트 (비어 있어도 자리를 남긴다)
```

- 날짜는 로컬 달력 `YYYY-MM-DD`. GUI는 **오늘** 날짜의 `Input01` 을 먼저 찾는다.
- 같은 세트의 파일 이름은 스템이 같아야 한다. 렌더러가 `Sunday Slow Motion.pdf` 옆에서 `.musicxml` `.ly` `.mid` 를 찾기 때문이다.
- `Input02` 가 비어 있으면 그날 두 번째 곡이 아직 없다는 뜻이다. 지워도 동작에는 영향 없다.

## 각 확장자가 엔진에서 하는 일

| 확장자 | 필수 | 쓰임 |
|---|---|---|
| `.pdf` | 예 | 화면. 단·세로줄·음머리 X |
| `.mp3` | 예 | 영상 오디오. 앞 무음만 오프셋 |
| `.musicxml` | 강력 권장 | 마디 시계, 성부 음정, 화성, 기보 길이 |
| `.ly` | 권장 | 템포·마디 보조, PDF와 같은 조판 |
| `.mid` | 권장 | 피아노/성부 감사. **커서 시계 아님** |
| `.gp5` | 아니오 | 사람이 Guitar Pro로 열어 보는 원본 |

XML 성부 id (이 프로젝트 기준 곡):

- P0 Piano
- P1 Violin
- P2 Cello
- P3 Double Bass

MIDI GM program: Piano 0, Violin 40, Cello 42, Contrabass 43.

더블베이스 PDF/LilyPond는 `bass_8` (기보가 실음보다 한 옥타브 위)이어도, 이 세트의 XML·MIDI 음정은 **기보 높이**로 맞춰져 있다. 감사 코드가 함부로 -12 하지 않는 이유다.

## 새 날짜를 만드는 법

1. `InputData/2026-08-16/Input01/` 생성
2. 파일 여섯 개를 같은 이름으로 복사 또는보내기
3. 그날 GUI를 연다. 자동 채움이 Input01을 가리킨다

다른 곡이면 스템만 바꾸고, GUI에서 찾아보기로 고르면 된다. 자동 채움 파일명은 현재 `Sunday Slow Motion` 으로 고정되어 있다 (`gui/main_window.py`).
