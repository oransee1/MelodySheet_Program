# MelodySheet_Program (실행 패키지)

이 폴더가 **작업 디렉터리**다. `python main.py` 는 여기서 실행한다. 상위 저장소 README는 철학과 파이프라인, 이 문서는 파일 배치와 실행이다.

악보·MIDI 용어가 낯설면 먼저 [`docs/README.md`](docs/README.md) 학습 경로를 따른다. 루트 문서는 중급자용 명세서에 가깝다.

## 왜 폴더가 두 겹인가

PyCharm 프로젝트가 바깥 `MelodySheet_Program` 이고, 소스 루트가 안쪽에 한 번 더 있다. import 경로는 안쪽 기준이다 (`from engine.video_renderer import VideoRenderer`). 바깥에서 `python MelodySheet_Program/main.py` 를 치면 `engine` 을 못 찾는다.

## 파일

| 경로 | 하는 일 |
|---|---|
| `main.py` | `QApplication` → `gui.main_window.MainWindow`. 로직 없음 |
| `test_render.py` | GUI 없이 `InputData/2026-08-14/Input01` 로 `VideoRenderer.render()` |
| `requirements.txt` | PyQt5, PyMuPDF, opencv-python, moviepy≥2, Pillow, pydub, pretty_midi |
| `engine/` | 악보 분석, 시계, 커서, 인코딩, 교차검증 |
| `gui/` | 경로 입력, fps, 로그, 백그라운드 렌더 스레드 |
| `InputData/` | `YYYY-MM-DD/InputNN/` 입력 세트 |
| `Output/` | `YYYY-MM-DD/` 영상과 `*_audit.txt` |
| `Sample/` | mp3+pdf만. MIDI·MusicXML은 Input01에 있다 |

`__pycache__/` 는 바이트코드다. 문서로 읽지 말고, 버전마다 다시 생긴다.

## 실행 순서

1. 이 폴더로 `cd`
2. `python -m pip install -r requirements.txt` (ffmpeg는 별도)
3. `python main.py`
4. 창이 뜨면 오늘 날짜 `InputData/.../Input01/Sunday Slow Motion.*` 와 `Output/오늘/` 을 자동으로 채운다
5. 프레임레이트 기본은 120. 싱크 방식 기본은 Klangio 에메랄드 커서
6. 생성하면 로그에 타임라인·단 수·피아노/현악 감사 요약이 찍히고, 그다음 프레임 인코딩

GUI 없이 같은 엔진만 돌리려면 `test_render.py` 의 `input_dir` 만 바꾸면 된다.

## 새 곡을 넣는 법

1. `InputData/YYYY-MM-DD/Input01/` 을 만든다 (날짜는 생성일).
2. 같은 파일 이름으로 `.pdf .mp3 .mid .musicxml .ly` 를 넣는다. 스템이 같아야 sidecar 탐색이 된다.
3. GUI를 그날 켜면 자동 채움. 아니면 찾아보기로 지정.
4. 출력은 `Output/YYYY-MM-DD/제목_SheetVideo.mp4`.

MusicXML이 없으면 타임라인은 LilyPond, 그것도 없으면 MIDI로 떨어진다. MIDI만 있으면 템포 변화가 한 개일 때 길이를 마디 수로 균등 분할한다. **가능하면 MusicXML을 넣어라.**

## 재구현 시 이 폴더에 필요한 최소 골격

```
main.py
requirements.txt
engine/__init__.py
engine/sheet_processor.py    # PDF → 스티치 이미지
engine/score_timeline.py     # 마디 초
engine/score_layout.py       # 단·세로줄
engine/score_notes.py        # 마디 안 앵커
engine/sync_manager.py       # t → (y, 커서)
engine/video_renderer.py     # 위 것들을 모아 mp4
gui/main_window.py           # 없어도 test_render로 대체 가능
```

감사(`part_audit`, `piano_chords`, `beat_audit`)는 영상 없이도 동작한다. 먼저 시계와 커서를 맞춘 뒤 붙이는 편이 안전하다.
