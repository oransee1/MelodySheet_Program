# Sample — 최소 미리보기

GUI가 Input01을 못 찾을 때 쓰는 예비 음원·악보다.

- `Sunday Slow Motion.mp3`
- `Sunday Slow Motion.pdf`

**MIDI와 MusicXML은 여기 없다.** 처음부터 이 폴더에는 두 파일만 커밋되어 있다. 시계·성부 감사가 필요하면 `InputData/.../Input01` 의 `.mid` `.musicxml` `.ly` 를 써야 한다.

Sample만으로 생성하면:

- 화면은 PDF로 그려진다
- 타임라인은 MIDI/XML이 없어 부정확하거나 선형 스크롤로 떨어질 수 있다
- 성부 감사 보고서는 “MIDI 없음” / “성부 없음”에 가깝다

MIDI를 Sample에도 두고 싶다면 Input01의 `Sunday Slow Motion.mid` 를 **복사**하면 된다. 지금은 GUI 자동 채움이 Sample mid를 찾지 않는다 (`gui/main_window.py` 의 `default_midi` 목록).
