# MelodySheet

PDF 악보와 음원을 합쳐, Klangio 스타일의 **스크롤 악보 영상**을 만드는 PyQt5 프로그램이다.

화면에는 세로로 이어 붙인 악보가 흐르고, 연주 시각에 맞춰 **에메랄드색 세로 커서**가 지금 마디를 가리킨다. 생성 직전 피아노 화음·바이올린·첼로·베이스가 악보와 같은 음정인지 교차검증 텍스트를 같이 쓴다.

실제 코드는 한 단계 안쪽 패키지에 있다.

```
MelodySheet_Program/                  ← 이 저장소 루트 (지금 문서)
└── MelodySheet_Program/              ← 실행·패키지 루트
    ├── main.py                       ← GUI 진입점
    ├── test_render.py                ← GUI 없이 한 곡 렌더
    ├── requirements.txt
    ├── engine/                       ← 악보·시계·렌더·감사
    ├── gui/                          ← PyQt5 창
    ├── InputData/YYYY-MM-DD/InputNN/ ← 날짜별 입력 세트
    ├── Output/YYYY-MM-DD/            ← 영상·감사 리포트
    └── Sample/                       ← 최소 미리보기 (mp3+pdf)
```

패키지 안 폴더마다 README가 있다. 처음이면 이 문서 → `MelodySheet_Program/README.md` → `engine/README.md` 순으로 읽는다.

---

## 1. 이 프로그램이 하는 일

입력은 보통 한 세트가 같이 온다 (Klangio 등 자동 채보 결과).

| 파일 | 역할 |
|---|---|
| `.pdf` | **공간의 진실.** 단(system), 페이지, 세로줄, 음머리 X |
| `.musicxml` | **시간의 진실.** 마디 수, 템포, 박자표, 기보 길이, 성부 음정, 화성 |
| `.ly` | 템포·마디 보조. PDF와 같은 조판 소스 |
| `.mid` | 연주 시각 참고. **커서 시계로 쓰지 않는다** |
| `.mp3` | 영상에 붙는 소리 |

출력은 `Output/날짜/곡이름_SheetVideo.mp4` 와 옆파일들이다.

- `*_beat_audit.txt` — 시계·마디·단이 서로 모순인지
- `*_piano_chords.txt` — 피아노 MIDI vs 기보 화성
- `*_violin_audit.txt` / `*_cello_audit.txt` / `*_bass_audit.txt` — 성부 음정·화성

---

## 2. 설계에서 절대 깨면 안 되는 것

초심자가 재구현할 때 가장 많이 틀리는 지점이다.

1. **커서는 악보에 적힌 박자를 따른다.** MIDI 노트 시각은 이 곡에서 입구가 약 2초 늦고, 지연이 일정하지 않다. MIDI로 커서를 밀면 “연주에 맞지만 악보와 틀린” 영상이 된다.
2. **PDF는 픽셀 공간만 믿는다.** 단의 y, 마디 세로줄 x, (개수가 맞을 때만) 음머리 x. 8분음표와 4분음표를 PDF만으로 구분하지 않는다. OMR 박자 분류는 이 악보에서 약 12~13/90마디만 맞았다.
3. **MusicXML 기보 길이가 마디 안 진행률이다.** `divisions=12`, 4/4이면 한 마디 48디비전. 이음줄 `tie stop`은 새 발음이 아니다. `<chord/>`는 **직전 음의 시각**에 붙는다(커서를 먼저 밀면 겹음이 다음 음과 묶인다).
4. **교차검증 숫자를 과대포장하지 않는다.** “창 3.5초 안 음정 60%”는 “틀린 음 40%”가 아니다. 시각을 무시한 음정 수열(LCS)·음표 가방을 같이 본다. 베이스는 가방 100%인데 온셋은 1%였다.
5. **페이지는 마지막 음을 듣기 전에 넘기지 않는다.** 다음 페이지 스크롤은 마지막 마디가 거의 끝난 뒤, 최대 0.4초다.

---

## 3. 생성 파이프라인 (한 줄로)

```
PDF 세로 스티치
  → MusicXML/LilyPond로 마디 시간축
  → PDF에서 단·세로줄
  → 기보 길이로 마디 안 x 앵커
  → 피아노/바이올린/첼로/베이스 감사 파일
  → 가장 큰 단이 1080p에 들어가게 스케일
  → 매 시각: 마디 → 단 → 세로줄 사이 x, 단 중앙 y
  → 인트로 3초 + 본편(음원 길이) + 아웃트로 3초 → mp4
```

자세한 모듈 계약은 `MelodySheet_Program/engine/README.md`.

---

## 4. 실행

작업 디렉터리는 **안쪽** `MelodySheet_Program/` 이다. 여기서 `python main.py` 를 실행해야 `engine`, `gui` 가 import 된다.

```text
cd MelodySheet_Program
python -m pip install -r requirements.txt
python main.py
```

GUI 없이 샘플 한 곡:

```text
python test_render.py
```

`test_render.py`는 `InputData/2026-08-14/Input01/` 을 연다.

의존성: PyQt5, PyMuPDF, OpenCV, MoviePy 2, Pillow, pretty_midi. ffmpeg가 MoviePy 인코딩에 필요하다.

---

## 5. 기준 곡 (Sunday Slow Motion)

교차검증에 쓰인 사실. 재구현 후 같은 입력으로 비슷한 숫자가 나와야 한다.

- 음원 약 209.9초, 악보 연주 길이 202.723초 (템포 115/68/100/136/107, 마디 1/40/50/61/77)
- PDF 8페이지, MusicXML 90마디, 성부 P0 Piano / P1 Violin / P2 Cello / P3 Double Bass
- MIDI GM: Piano 0, Violin 40, Cello 42, Contrabass 43
- 현악 MIDI는 악보보다 입구가 약 2.0~2.2초 늦다. 음정 수열은 거의 같고 절대시각 ±80ms는 거의 안 맞는다.

---

## 6. 처음부터 다시 만들 때

1. PDF를 페이지마다 래스터한 뒤 세로로 붙이고, 각 페이지의 y0를 기억한다.
2. MusicXML 첫 성부의 마디마다 템포·박자표로 `duration_sec = 박 수 × (60/BPM)` 을 쌓아 시간축을 만든다. MIDI 노트 시각으로 마디를 나누지 않는다.
3. 스티치 이미지에서 가로 잉크 밀도로 **단**을 찾고, 단 안에서 세로 잉크로 **마디선**을 찾는다. 오선 5줄을 각각 단으로 쪼개지 않게, 악기 사이 간격은 합친다.
4. 시각 t → 마디 번호 → 그 단의 왼쪽·오른쪽 세로줄 → 마디 안 기보 진행률로 x. y는 그 단을 화면 중앙에 두는 스크롤.
5. 페이지가 바뀌는 단의 마지막 마디가 끝나기 전에는 y를 다음 페이지로 밀지 않는다.
6. 감사는 성부별로 XML 음정 수열과 MIDI 해당 프로그램 트랙을 비교한다. 시계는 1번에서 만든 격자다.

폴더별 파일 목록과 API는 각 README에 있다.
