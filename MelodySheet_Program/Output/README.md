# Output — 생성 결과

엔진이 쓰는 유일한 출력 루트다. 입력을 덮어쓰지 않는다.

```
Output/
  YYYY-MM-DD/
    곡제목_SheetVideo.mp4
    곡제목_SheetVideo_beat_audit.txt
    곡제목_SheetVideo_piano_chords.txt
    곡제목_SheetVideo_violin_audit.txt
    곡제목_SheetVideo_cello_audit.txt
    곡제목_SheetVideo_bass_audit.txt
  diag/                 ← 개발 중 프레임·단 검출 스크린샷. 제품 출력이 아님
```

날짜 폴더는 GUI/`test_render.py` 가 `datetime.now()` 로 만든다. 없으면 `os.makedirs`.

## 영상

- 1920×1080, 기본 120fps, H.264 + AAC
- 앞 3초 제목, 가운데 음원 길이만큼 악보, 뒤 3초 아웃트로
- 파일 이름이 감사 옆파일의 스템이다. `write_*_report` 는 `os.path.splitext(output_path)[0] + "_violin_audit.txt"` 형식

MoviePy가 인코딩 중 `곡이름TEMP_MPY_wvf_snd.mp4` 같은 임시 파일을 패키지 루트에 남기는 경우가 있다. 생성이 끝나면 지워도 된다. 완성본으로 재생하지 말 것.

## 감사 파일을 읽는 법

**beat_audit**  
PASS/WARN/FAIL. FAIL이어도 영상은 만든다.  
증명하지 않는 것: 커서가 특정 음머리 픽셀 위인지, 사람이 박자를 자연스럽게 느끼는지.

**piano_chords**  
기보 코드 vs 피아노 MIDI 음급. `=` 일치, `x` 불일치. 현악은 넣지 않았다.

**violin / cello / bass**  
한 줄 요약 다음, 발음마다 기보·MIDI·온셋·음정·화성·역할.  
아래쪽 “기보에 없는 MIDI”는 짝이 안 남은 연주 음이다.

숫자를 이렇게 읽는다.

| 지표 | 의미 | 이 곡에서 흔히 나오는 값 |
|---|---|---|
| 같은 음정 대응 (3.5초 창) | 창 안에서 같은 MIDI 음정을 찾음 | 현악 50~60%대 |
| 절대시각 ±80ms | 악보 격자와 동시에 침 | 0~2% |
| LCS | 순서를 유지한 채 같은 음정 수열 | 95~99% |
| 음표가방 | 중복을 센 음정 교집합 | 베이스 100% |
| 구성음 n/m | 기보 음이 그 마디 **첫** 코드에 속함 | 피아노와 별개. 연주 적중이 아님 |

창 대응이 낮고 LCS가 높으면 **같은 선율을 늦은 시계로 재생**한 것이다. “음이 틀렸다”고 쓰지 말 것.

## 재구현

출력 API는 경로 문자열 하나면 된다.

```python
root, _ = os.path.splitext(output_path)
open(root + "_violin_audit.txt", "w", encoding="utf-8")
```

인코딩 전에 감사를 쓰는 이유: 영상이 실패해도 숫자로 시계를 볼 수 있다.
