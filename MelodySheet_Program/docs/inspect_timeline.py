"""기준 곡 시계를 읽어 기댓값과 비교한다. 영상은 만들지 않는다.

패키지 루트(MelodySheet_Program/)에서:
    python docs/inspect_timeline.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine.score_timeline import build_score_timeline

INPUT = os.path.join(ROOT, "InputData", "2026-08-14", "Input01")
XML = os.path.join(INPUT, "Sunday Slow Motion.musicxml")
LY = os.path.join(INPUT, "Sunday Slow Motion.ly")
MID = os.path.join(INPUT, "Sunday Slow Motion.mid")

EXPECT_N = 90
EXPECT_END = 202.723
EXPECT_TEMPO = {1: 115, 40: 68, 50: 100, 61: 136, 77: 107}
EXPECT_M1_DUR = 2.087


def check(ok: bool, label: str, detail: str = "") -> None:
    flag = "ok  " if ok else "FAIL"
    extra = f"  ({detail})" if detail else ""
    print(f"{flag} {label}{extra}")


def main() -> None:
    print(f"cwd 힌트: 이 스크립트는 Input01 XML을 연다")
    print(f"xml  exists={os.path.isfile(XML)}  path={XML}")
    if not os.path.isfile(XML):
        print("FAIL  MusicXML 없음. docs/07-막혔을-때.md")
        sys.exit(1)

    tl = build_score_timeline(XML, LY if os.path.isfile(LY) else None, MID if os.path.isfile(MID) else None)
    by_num = {m.number: m for m in tl.measures}

    check(tl.n_measures == EXPECT_N, f"마디 {tl.n_measures}", f"기대 {EXPECT_N}")
    check(abs(tl.music_end - EXPECT_END) < 0.05, f"music_end {tl.music_end:.3f}s", f"기대 {EXPECT_END}s")
    check("musicxml" in (tl.source or ""), f"source={tl.source}")

    for num, bpm in EXPECT_TEMPO.items():
        m = by_num.get(num)
        if m is None:
            check(False, f"마디{num} 없음")
            continue
        check(abs(m.tempo_bpm - bpm) < 0.6, f"마디{num} 템포 {m.tempo_bpm:.0f}", f"기대 {bpm}")

    m1 = by_num.get(1)
    if m1:
        check(
            abs(m1.duration_sec - EXPECT_M1_DUR) < 0.01,
            f"마디1 길이 {m1.duration_sec:.3f}s",
            f"손계산 4*60/115={EXPECT_M1_DUR}s",
        )

    # 첼로 입구 근처: 마디 14 시작은 13마디 * 2.087s
    m14 = by_num.get(14)
    if m14:
        print(f"info 마디14 시작 {m14.start_sec:.3f}s (첼로 첫 음은 이 마디 안)")

    print("손계산: 4/4 · BPM 115 → 한 마디 = 4 * 60 / 115 = 2.087s")


if __name__ == "__main__":
    main()
