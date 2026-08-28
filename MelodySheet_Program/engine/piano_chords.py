"""피아노만의 화음 추출.

음원에서 피아노를 분리하는 모델은 쓰지 않는다.
Klangio MIDI의 Piano 트랙(RH+LH, program 0)이 이 음원에서 뜬 피아노 성부다.
바이올린·첼로·베이스 음은 넣지 않는다.

각 마디를 박으로 나눠, 그 순간 울리는 피아노 음정의 음급으로 화음을 붙인다.
"""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

from engine.score_notes import _strip_xmlns
from engine.score_timeline import ScoreTimeline


PC_NAMES_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# 전위된 화음: 루트 기준 pitch-class 집합
_QUALITIES: List[Tuple[frozenset, str, int]] = [
    (frozenset({0, 4, 7, 10}), "7", 4),
    (frozenset({0, 3, 7, 10}), "m7", 4),
    (frozenset({0, 4, 7, 11}), "maj7", 4),
    (frozenset({0, 3, 6, 10}), "m7b5", 4),
    (frozenset({0, 4, 7, 9}), "6", 4),
    (frozenset({0, 3, 7, 9}), "m6", 4),
    (frozenset({0, 5, 7}), "sus4", 3),
    (frozenset({0, 2, 7}), "sus2", 3),
    (frozenset({0, 3, 6}), "dim", 3),
    (frozenset({0, 4, 8}), "aug", 3),
    (frozenset({0, 4, 7}), "", 3),
    (frozenset({0, 3, 7}), "m", 3),
]


@dataclass
class BeatChord:
    measure: int
    beat: int
    time_sec: float
    pitches: List[int]
    pcs: List[int]
    label: str
    bass_pc: Optional[int]


@dataclass
class MeasureChord:
    measure: int
    start_sec: float
    written: str
    extracted: str
    beat_labels: List[str]
    match: Optional[bool]


@dataclass
class PianoChordReport:
    measures: List[MeasureChord] = field(default_factory=list)
    n_written: int = 0
    n_compared: int = 0
    n_match: int = 0
    n_root: int = 0
    source: str = ""

    def summary_lines(self) -> List[str]:
        rate = 100.0 * self.n_match / max(self.n_compared, 1)
        rrate = 100.0 * self.n_root / max(self.n_compared, 1)
        lines = [
            f"피아노 화음 추출 ({self.source})",
            f"  기보 코드 {self.n_written}마디 · 대조 {self.n_compared} · "
            f"구성음 일치 {self.n_match} ({rate:.0f}%) · 루트 일치 {self.n_root} ({rrate:.0f}%)",
        ]
        misses = [m for m in self.measures if m.match is False]
        if misses:
            sample = ", ".join(f"m{m.measure}:{m.extracted}≠{m.written}" for m in misses[:8])
            lines.append(f"  불일치 예: {sample}")
        return lines

    def as_text(self) -> str:
        lines = self.summary_lines()
        lines.append("")
        lines.append("마디  기보        추출        박별")
        for m in self.measures:
            flag = " " if m.match is None else ("=" if m.match else "x")
            beats = " ".join(m.beat_labels) if m.beat_labels else "-"
            lines.append(f"{m.measure:4d} {flag} {m.written or '-':<10} {m.extracted or '-':<10} {beats}")
        lines.append("")
        lines.append("참고: 피아노 MIDI(음원에서 분리 전사된 두 손)만 사용. 현악기는 제외.")
        return "\n".join(lines) + "\n"


def _label_from_pcs(pcs: Sequence[int], bass_pc: Optional[int] = None) -> str:
    uniq = sorted(set(int(p) % 12 for p in pcs))
    if not uniq:
        return ""
    if len(uniq) == 1:
        return PC_NAMES_FLAT[uniq[0]]
    if len(uniq) == 2:
        a, b = uniq[0], uniq[1]
        iv = (b - a) % 12
        if iv == 7:
            return PC_NAMES_FLAT[a] + "5"
        if iv == 5:
            return PC_NAMES_FLAT[b] + "5"
        if iv == 3:
            return PC_NAMES_FLAT[a] + "m"
        if iv == 4:
            return PC_NAMES_FLAT[a]
        if iv == 8:
            return PC_NAMES_FLAT[b] + "m"
        if iv == 9:
            return PC_NAMES_FLAT[b]
        root = bass_pc if bass_pc in uniq else a
        return PC_NAMES_FLAT[root]

    best = None  # (score, root, qual)
    pcset = set(uniq)
    for root in uniq:
        rel = frozenset((p - root) % 12 for p in uniq)
        for shape, qual, need in _QUALITIES:
            if not shape.issubset(rel):
                continue
            extra = len(rel - shape)
            missing = need - len(shape & rel)
            score = 10 * len(shape & rel) - 4 * extra - 6 * missing
            if bass_pc is not None and bass_pc == root:
                score += 1
            if best is None or score > best[0]:
                best = (score, root, qual)
    if best is None:
        root = bass_pc if bass_pc in pcset else uniq[0]
        return PC_NAMES_FLAT[root]
    return PC_NAMES_FLAT[best[1]] + best[2]


def _pc_set(label: str) -> Set[int]:
    """라벨 → 구성음. 루트+종류만 본다."""
    if not label:
        return set()
    m = re.match(r"^([A-G](?:b|#)?)(.*)$", label)
    if not m:
        return set()
    name, qual = m.group(1), m.group(2)
    names = {
        "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
        "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
    }
    root = names.get(name)
    if root is None:
        return set()
    shapes = {
        "": {0, 4, 7},
        "m": {0, 3, 7},
        "7": {0, 4, 7, 10},
        "m7": {0, 3, 7, 10},
        "maj7": {0, 4, 7, 11},
        "dim": {0, 3, 6},
        "aug": {0, 4, 8},
        "sus4": {0, 5, 7},
        "sus2": {0, 2, 7},
        "6": {0, 4, 7, 9},
        "m6": {0, 3, 7, 9},
        "m7b5": {0, 3, 6, 10},
        "5": {0, 7},
    }
    q = qual.replace("maj7", "maj7")
    shape = shapes.get(q, shapes.get("" if q == "" else q, {0, 4, 7} if q == "" else {0, 3, 7} if q.startswith("m") else {0, 4, 7}))
    return {(root + i) % 12 for i in shape}


def chords_compatible(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    sa, sb = _pc_set(a), _pc_set(b)
    if not sa or not sb:
        return False
    # 같은 족: 삼화음 ⊂ 7화음
    return sa.issubset(sb) or sb.issubset(sa)


def parse_written_harmonies(musicxml_path: Optional[str]) -> Dict[int, str]:
    """마디 번호 → 그 마디 첫 기보 코드."""
    out: Dict[int, str] = {}
    if not musicxml_path or not os.path.isfile(musicxml_path):
        return out
    try:
        raw = open(musicxml_path, "r", encoding="utf-8").read()
        root = ET.fromstring(_strip_xmlns(raw))
    except (OSError, ET.ParseError):
        return out
    kind_map = {
        "major": "",
        "minor": "m",
        "dominant": "7",
        "dominant-seventh": "7",
        "major-seventh": "maj7",
        "minor-seventh": "m7",
        "diminished": "dim",
        "augmented": "aug",
        "suspended-fourth": "sus4",
        "suspended-second": "sus2",
        "major-sixth": "6",
        "minor-sixth": "m6",
        "half-diminished": "m7b5",
    }
    for part in root.findall("part"):
        for meas in part.findall("measure"):
            raw_n = meas.get("number") or ""
            try:
                num = int(re.sub(r"[^\d]", "", raw_n) or 0)
            except ValueError:
                continue
            h = meas.find("harmony")
            if h is None:
                continue
            if num in out:
                continue
            step = h.findtext("root/root-step")
            if not step:
                continue
            try:
                alt = int(float(h.findtext("root/root-alter") or 0))
            except ValueError:
                alt = 0
            kind = (h.findtext("kind") or "major").strip()
            names = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
            pc = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[step[0]]
            pc = (pc + alt) % 12
            out[num] = names[pc] + kind_map.get(kind, "")
    return out


def _load_piano_notes(midi_path: str) -> List[Tuple[float, float, int]]:
    """(start, end, pitch) 피아노만."""
    import pretty_midi

    pm = pretty_midi.PrettyMIDI(midi_path)
    notes = []
    for inst in pm.instruments:
        if inst.is_drum:
            continue
        name = (inst.name or "").lower()
        piano = inst.program <= 7 or "piano" in name or "kbd" in name
        if not piano:
            continue
        for n in inst.notes:
            notes.append((float(n.start), float(n.end), int(n.pitch)))
    notes.sort(key=lambda x: x[0])
    return notes


def _sounding(notes: Sequence[Tuple[float, float, int]], t: float, slack: float = 0.02) -> List[int]:
    return [p for s, e, p in notes if s - slack <= t < e]


def extract_piano_chords(
    timeline: ScoreTimeline,
    midi_path: Optional[str],
    musicxml_path: Optional[str] = None,
    beats_per_measure: int = 4,
) -> PianoChordReport:
    written = parse_written_harmonies(musicxml_path)
    report = PianoChordReport(n_written=len(written), source="MIDI Piano RH+LH")
    if not midi_path or not os.path.isfile(midi_path) or not timeline.n_measures:
        return report
    try:
        piano = _load_piano_notes(midi_path)
    except Exception:
        report.source = "피아노 MIDI를 읽지 못함"
        return report
    if not piano:
        report.source = "피아노 트랙 없음"
        return report

    for meas in timeline.measures:
        beat_labs = []
        beat_chords: List[str] = []
        for b in range(beats_per_measure):
            t = meas.start_sec + (b + 0.20) * (meas.duration_sec / beats_per_measure)
            pits = _sounding(piano, t)
            pcs = sorted({p % 12 for p in pits})
            bass = min(pits) % 12 if pits else None
            lab = _label_from_pcs(pcs, bass) if len(pcs) >= 2 else ""
            beat_labs.append(lab or "-")
            if lab:
                beat_chords.append(lab)
        # 마디 전체: 일정 시간 이상 울린 음급만 모아 대표 화음
        dur_w = [0.0] * 12
        lowest = None
        for s, e, p in piano:
            ov0 = max(s, meas.start_sec)
            ov1 = min(e, meas.end_sec)
            if ov1 - ov0 < 0.03:
                continue
            dur_w[p % 12] += ov1 - ov0
            if lowest is None or p < lowest[0]:
                lowest = (p, ov1 - ov0)
        thresh = meas.duration_sec * 0.12
        pcs_m = [i for i, d in enumerate(dur_w) if d >= thresh]
        bass = (lowest[0] % 12) if lowest else None
        if len(pcs_m) >= 2:
            extracted = _label_from_pcs(pcs_m, bass)
        elif beat_chords:
            extracted = Counter(beat_chords).most_common(1)[0][0]
        else:
            extracted = ""
        wr = written.get(meas.number, "")
        match = None
        if wr and extracted:
            match = chords_compatible(wr, extracted)
        report.measures.append(
            MeasureChord(
                measure=meas.number,
                start_sec=meas.start_sec,
                written=wr,
                extracted=extracted,
                beat_labels=beat_labs,
                match=match,
            )
        )
        if match is not None:
            report.n_compared += 1
            if match:
                report.n_match += 1
            ra = re.match(r"^([A-G](?:b|#)?)", wr)
            rb = re.match(r"^([A-G](?:b|#)?)", extracted)
            if ra and rb and ra.group(1) == rb.group(1):
                report.n_root += 1
    return report


def write_chord_report(output_path: str, report: PianoChordReport) -> str:
    root, _ = os.path.splitext(output_path)
    path = root + "_piano_chords.txt"
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report.as_text())
    return path
