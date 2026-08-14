# engine — 악보 시계, 레이아웃, 렌더, 교차검증

GUI가 경로만 넘기면 여기서 영상이 만들어진다. 모듈은 **데이터 방향이 한 줄**이다. 서로 순환 import 하지 않도록 아래 층을 지킨다.

처음 읽으면 [`../docs/README.md`](../docs/README.md) 가 더 느리다. 이 파일은 모듈 계약이다. 함수 한 줄마다 주석이 달려 있지는 않다.

```
sheet_processor          PDF 픽셀
score_timeline           마디 → 초 (MusicXML > LilyPond > MIDI)
score_layout             단·세로줄 (PDF)
score_notes / pdf_notes  마디 안 x 앵커 (기보 길이 + 음머리)
sync_manager             t → 스크롤 y, 커서 사각형
piano_chords / nonchord / part_audit   감사 (렌더를 import 하지 않음)
  violin_audit / cello_audit / bass_audit   얇은 래퍼
beat_audit               시계·레이아웃·커서 모순
video_renderer           위 전부를 호출하고 MoviePy로 인코딩
```

`video_renderer` 만 전체를 알고, 감사 모듈은 타임라인과 경로만 받는다.

---

## 1. 시간축 `score_timeline.py`

### 자료구조

- `MeasureSpan`: `number`, `start_sec`, `duration_sec`, `tempo_bpm`, `anchors: List[(t_frac, x_frac)]`
- `x_frac_at(t)`: 마디 안 시각 → 0~1. 앵커가 두 개 미만이면 시간 선형
- `ScoreTimeline.measure_at(t)`: 이분 탐색으로 (마디 인덱스, 마디 안 진행률)
- `music_end`: 마지막 마디 `end_sec`. 음원 길이와 다를 수 있다 (이 곡 202.723 vs 209.9)

### 우선순위

`build_score_timeline(musicxml, lilypond, midi)`:

1. MusicXML 첫 `<part>` 의 각 `<measure>`. `<sound tempo>` 와 `<time>` 을 읽는다.  
   `duration = beats × (4/beat-type) × (60/tempo)`
2. 실패하면 LilyPond `NotesPartZeroStaffZero` 의 `\tempo 4 = N` 과 `| % 마디`
3. 그래도 없으면 MIDI 길이 / 마디 수. 템포 이벤트가 하나면 **균등 분할** (Klangio는 템포를 노트 시각에 구워 넣고 메타 템포는 초기값만 남기는 경우가 있다)

MIDI 노트 온셋으로 마디 경계를 만들지 않는다.

### sidecar

`find_sidecar(path, (".musicxml", ".xml"))`: 같은 스템, 없으면 같은 폴더의 그 확장자 하나.

Sunday Slow Motion 템포(검증됨): 마디 1=115, 40=68, 50=100, 61=136, 77=107.

---

## 2. 공간 `sheet_processor.py` + `score_layout.py`

### 스티치

`convert_pdf_to_multi_page_image(pdf, dpi=200)`  
각 페이지를 72dpi 기준 `zoom = dpi/72` 로 래스터하고 세로로 붙인다. 반환 `(PIL.Image, page_y_positions)`.  
`page_y_positions[i]` 는 i번째 페이지의 위쪽 y. 마지막 원소는 전체 높이.

단·세로줄은 **이 스티치와 같은 DPI** 에서 읽어야 커서가 맞는다.

### 단 검출 (`analyze_score_layout`)

페이지마다:

- 머리글·바닥글 crop (첫 페이지 머리 약 1.08in, 이후 0.28in, 바닥 0.78in)
- 가로 잉크 비율을 세로로 투영 → 임계값 넘는 구간이 단
- `merge_gap ≈ 0.70in`: 악기 사이(피아노 큰보표 + 바이올린 + 첼로 + 베이스)는 한 단으로 합친다. 이 값이 작으면 오선 5줄이 각각 단이 된다

각 `SystemLayout`: `page_index`, `y0/y1`, `x_left/x_right`, `start_measure~end_measure`, `bar_xs`.

마디 번호는 시간축의 총 마디 수를 단에 순서대로 나눈다. MusicXML `print new-system` 이 없는 경우가 많아 PDF 단 수가 진실이다.

### 세로줄

단 안에서 세로 잉크 투영. 첫 마디는 음자리표 뒤를 건너뛰고 스캔한다 (1단은 너비의 약 24%부터, 이후 약 10%). 실패하면 단을 마디 수로 균등 분할하고 `bars_from_detect=False`.

`measure_x_range(n)` → `(left, right)` 픽셀.

---

## 3. 마디 안 진행 `score_notes.py` + `pdf_notes.py`

`attach_measure_anchors(timeline, layout, musicxml, midi_path=None, stitched_img=...)`

- 박자(언제) = MusicXML 기보 duration / 마디 divisions. **MIDI 시계 사용 금지** (`midi_path` 는 의도적으로 버린다).
- 가로(어디) = PDF 음머리 x. **개수가 기보 발음 수와 같을 때만**. 아니면 default-x 또는 시간 선형 `(0,0)~(1,1)`
- 이음줄 종료·쉼표는 앵커에 안 넣는다
- `<chord/>` 음은 새 시각이 아니다

`pdf_notes.collect_measure_note_xs`: 오선 근처 원형 블롭. 박자 종류 분류에 쓰지 말 것.

---

## 4. 커서 `sync_manager.py`

`calculate_sync(elapsed, img_w, img_h, viewport_h) → (y_offset, (x, y, w, h))`

1. `t = elapsed - audio_offset` (오프셋은 앞 무음만. 다성 상관은 점수가 평탄해서 쓰지 않는다)
2. `measure_at(t)` → 마디
3. `system_for_measure` → 단
4. `x = left + (right-left) * x_frac_at(t)`
5. y는 그 단을 화면 세로 중앙에 두는 값 `_system_y_offset`
6. 다음 단이 **같은 페이지**면 마지막 마디의 뒤 30%에서 y를 다음 단으로 선형 보간
7. **다른 페이지**면 마지막 마디 끝 `min(0.4s, 12% 마디)` 에서만 보간. 그 전에는 현재 페이지 유지

커서는 폭 16, 단 높이만큼의 반투명 에메랄드 막대 `(BGR 200,211,76)`, 알파 0.55.  
반환 좌표는 **화면 기준**. 시트 x에 `x_offset` 을 더해 그린다.

레이아웃이 없으면 이미지 전체를 시간에 따라 선형 스크롤하는 대체 경로.

---

## 5. 렌더 `video_renderer.py`

해상도 1920×1080, 기본 120fps.

`render()` 순서:

1. 음원 길이, PDF 스티치 dpi=200
2. sidecar XML/LY/MID
3. timeline → layout → anchors
4. 피아노·바이올린·첼로·베이스 감사 파일 기록 (인코딩 전)
5. 가장 큰 단이 `1080-120` 안에 들어가게 스케일. 레이아웃도 `layout.scaled(scale)`
6. 앞 무음 오프셋 (피크의 3%, 0.18초 미만은 0)
7. `run_beat_audit` 후 `*_beat_audit.txt`
8. 인트로 3초 / 본편=음원 길이 / 아웃트로 3초를 `concatenate_videoclips`
9. `libx264` + `aac`, MoviePy 2

본편 한 프레임: 회색 배경 → 시트 슬라이스 → 커서 오버레이 → 상단 42px 헤더.

음원보다 악보가 짧으면 마지막 마디에 커서가 머문 채 소리가 더 간다. 그 반대를 음원 속도로 맞추지 않는다.

---

## 6. 교차검증

### 박자 `beat_audit.py`

합격을 “커서가 음머리 위”로 정의하지 않는다.  
합격은 **시계·마디 수·단 배정·페이지 홀드가 모순이 아님**이다. 음표 단위 MIDI 어긋남은 WARN.

### 피아노 `piano_chords.py`

음원 분리 모델을 쓰지 않는다. MIDI program ≤ 7 (또는 이름 piano).  
마디마다 기보 `<harmony>` vs 그 마디에 울린 피아노 음급. 구성음 집합 / 루트.

### 성부 `part_audit.py`

공통 엔진. 래퍼만 악기마다 있다.

| 스펙 | XML | MIDI program | 이름 |
|---|---|---|---|
| VIOLIN | P1, violin (cello 제외) | 40 | violin |
| CELLO | P2 | 42 | cello, violoncello |
| BASS | P3 | 43 | double bass 등. bassoon 제외 |

규칙:

- 이음줄에 `stop` 이 있으면 새 발음이 아니다 (`start+stop` 포함)
- `<chord/>` 는 **이전 온셋 시각**에 붙인다. 커서를 먼저 밀면 m23이 A2+F3로 잘못 묶인다
- 같은 음정, `|Δt| ≤ 3.5s` 로 짝. ±80ms 이면 온셋 일치
- 시각 무시 LCS, 음표 가방 교집합을 보고서에 쓴다
- 구성음 여부는 **그 마디 첫 기보 코드** (피아노 성부 화성). 마디 안 코드가 여러 개면 과소평가된다
- 베이스 XML에 `clef-octave-change=-1` 이 있어도, 이 곡 MIDI는 기보 높이(D3=50)다. `<transpose>` 가 있을 때만 반음을 더한다. 함부로 -12 하지 말 것

`nonchord.py`: 구성음 / 경과 / 보조 / 이탈 / 전타 / 전악 / 걸림 / 비화성. 애매하면 비화성.

---

## 7. 재구현 체크리스트

- [ ] 90마디, music_end ≈ 202.723s (이 곡 XML)
- [ ] 단 수가 페이지당 오선 묶음이지, 오선 5개가 아니다
- [ ] 커서가 마디 세로줄 사이에 있다 (음머리 위까지는 요구하지 않음)
- [ ] 페이지가 마지막 마디 80% 이전에 넘어가지 않는다
- [ ] 첼로 m23 겹음이 LilyPond `<c a,>` = A2+C3 와 같다
- [ ] 베이스 첫 음 XML·MIDI 모두 D3, -12 하면 LCS가 무너진다
- [ ] 현악 온셋 ±80ms 가 한 자리 % 여도, LCS·가방이 높으면 “다른 곡”이 아니라 “늦은 같은 선율”이다

테스트 진입: 상위 `test_render.py`, 또는 타임라인만 `build_score_timeline(...)`.
