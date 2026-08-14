# gui — PyQt5 껍데기

엔진을 모른다. 경로·옵션을 모아 `VideoRenderer` 에 넘기고, 로그와 진행률을 보여 준다.

## 파일

- `__init__.py` — 빈 패키지 표시
- `main_window.py` — 창 하나, 렌더 스레드 하나

`__pycache__/` 는 생성물이다.

## 창 구성 (`MainWindow`)

어두운 테마 (`DARK_STYLE`). 위에서 아래로:

1. **파일**
   - 음원 `.mp3/.wav`
   - 악보 `.pdf/.png/.jpg`
   - 옵션 MIDI `.mid` (찾아보기 필터에 musicxml/gp5/ly 도 있음. 렌더러는 확장자가 mid가 아니면 옆의 mid를 다시 찾는다)
   - 출력 `.mp4`
2. **메타**
   - 제목, 아티스트 (인트로·헤더·아웃트로에 그대로)
   - 시각화: `klangio` (에메랄드 커서) / `scroll` (커서 없음, 스크롤만)
   - 프레임레이트: 120 (기본) / 60 / 30
3. 생성 버튼, 진행 바, 로그

## 자동 채움

실행 파일이 있는 패키지 루트 기준으로:

```
InputData/{오늘}/Input01/Sunday Slow Motion.{mp3,pdf,mid}
InputData/{오늘}/Sunday Slow Motion.{...}          # 날짜 폴더 직하도 시도
Sample/Sunday Slow Motion.{mp3,pdf}                 # MIDI는 Sample에 없음
~/Downloads, ~/Desktop
Output/{오늘}/Sunday_Slow_Motion_SheetVideo.mp4
```

MIDI는 Input01 → 날짜 폴더 → Downloads 순이다. Sample에는 mid를 두지 않았다.

## 스레드 (`RenderThread`)

`QThread`. UI 스레드에서 MoviePy/OpenCV를 돌리면 창이 죽는다.

- `progress_signal(int)` — 렌더러 콜백. 본편에서 대략 50~95
- `log_signal(str)` — 엔진 `log_callback`
- `finished_signal(bool, str)` — 성공 시 경로, 실패 시 예외 문자열

생성 중 버튼은 비활성화. 예외는 삼키지 않고 로그와 메시지 박스로 보낸다.

## 재구현

최소 GUI는 네 경로 + 실행 버튼이면 된다. 자동 채움과 다크 테마는 편의다.  
엔진 계약:

```python
VideoRenderer(
    pdf_path, audio_path, output_path,
    title=..., artist=...,
    sync_mode="klangio" | "scroll",
    midi_path=... or None,
    fps=120,
    progress_callback=lambda p: ...,
    log_callback=lambda msg: ...,
).render()
```

`main.py` 는 `QApplication` 과 `MainWindow.show()` 만 한다.
