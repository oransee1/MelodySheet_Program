"""구성음이 아닌 선율음을 종류별로 나눈다.

마디 코드(구성음 집합)와 앞·뒤 음정을 본다.
확실하지 않으면 '비화성음'으로만 표시한다.
"""
from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Set


def _step(a: int, b: int) -> bool:
    return 1 <= abs(a - b) <= 2


def _leap(a: int, b: int) -> bool:
    return abs(a - b) >= 3


def _dir(a: int, b: int) -> int:
    if b > a:
        return 1
    if b < a:
        return -1
    return 0


def classify_tone(
    prev_p: Optional[int],
    curr_p: int,
    next_p: Optional[int],
    chord_pcs: Set[int],
    prev_chord: Optional[Set[int]] = None,
    next_chord: Optional[Set[int]] = None,
) -> str:
    """한 음정의 역할. 반환은 한글 짧은 표지."""
    pc = curr_p % 12
    if chord_pcs and pc in chord_pcs:
        return "구성음"
    if not chord_pcs:
        return "코드없음"

    prev_ct = prev_p is not None and (prev_p % 12) in chord_pcs
    next_ct = next_p is not None and (next_p % 12) in chord_pcs

    # 걸림음: 앞 화성의 구성음 → 지금 비화성 → 아래로 2도 해결
    if (
        prev_p is not None
        and prev_p == curr_p
        and prev_chord
        and pc in prev_chord
        and next_p is not None
        and _step(curr_p, next_p)
        and next_ct
        and next_p < curr_p
    ):
        return "걸림음"

    # 전악음: 다음 화성 구성음이 한 박 일찍
    if next_chord and pc in next_chord and pc not in chord_pcs:
        return "전악음"

    if prev_p is not None and next_p is not None:
        d1, d2 = _dir(prev_p, curr_p), _dir(curr_p, next_p)
        if _step(prev_p, curr_p) and _step(curr_p, next_p) and d1 == d2 and d1 != 0:
            if prev_ct or next_ct:
                return "경과음"
            return "경과음"
        if prev_ct and next_p == prev_p and _step(prev_p, curr_p):
            return "보조음"
        if prev_ct and next_ct and _step(prev_p, curr_p) and _step(curr_p, next_p) and d1 != d2:
            return "보조음"
        if _step(prev_p, curr_p) and _leap(curr_p, next_p) and d1 != 0 and d1 == -d2:
            return "이탈음"
        if _leap(prev_p, curr_p) and _step(curr_p, next_p) and next_ct:
            return "전타음"

    if prev_p is not None and next_p is None and prev_ct and _step(prev_p, curr_p):
        return "보조음"
    if next_p is not None and prev_p is None and next_ct and _step(curr_p, next_p):
        return "경과음"

    return "비화성음"


def classify_event_pitches(
    pitches: Sequence[int],
    prev_pitch: Optional[int],
    next_pitch: Optional[int],
    chord_pcs: Set[int],
    prev_chord: Optional[Set[int]] = None,
    next_chord: Optional[Set[int]] = None,
) -> List[str]:
    """겹음은 음마다 분류. 선율 맥락은 가장 높은 음( impromptu 상성)을 쓴다."""
    if not pitches:
        return []
    top = max(pitches)
    out = []
    for p in pitches:
        pr = prev_pitch if p == top else None
        nx = next_pitch if p == top else None
        out.append(classify_tone(pr, p, nx, chord_pcs, prev_chord, next_chord))
    return out


def fill_harmony_map(written: dict, n_measures: int) -> dict:
    """코드가 비어 있는 마디는 직전 코드를 이어 받는다."""
    out = {}
    last = ""
    for n in range(1, n_measures + 1):
        if written.get(n):
            last = written[n]
        out[n] = last
    return out


def count_roles(labels: Iterable[str]) -> dict:
    acc = {}
    for lab in labels:
        acc[lab] = acc.get(lab, 0) + 1
    return acc
