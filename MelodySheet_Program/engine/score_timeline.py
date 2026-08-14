"""마디 단위 연주 시간축.

MusicXML 템포/박자표를 우선하고, 없으면 LilyPond·MIDI 순으로 보조한다.
음원 길이가 아니라 '악보가 실제로 흐르는 초'를 만든다.
"""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class MeasureSpan:
    number: int
    start_sec: float
    duration_sec: float
    tempo_bpm: float
    anchors: List[Tuple[float, float]] = field(default_factory=list)

    @property
    def end_sec(self) -> float:
        return self.start_sec + self.duration_sec

    def x_frac_at(self, t: float) -> float:
        """마디 안 시각 t → 가로 진행률(0~1). 앵커가 없으면 시간 선형."""
        u = (t - self.start_sec) / max(self.duration_sec, 1e-6)
        u = min(max(u, 0.0), 1.0)
        pts = self.anchors
        if len(pts) < 2:
            return u
        if u <= pts[0][0]:
            return pts[0][1]
        if u >= pts[-1][0]:
            return pts[-1][1]
        for i in range(len(pts) - 1):
            t0, x0 = pts[i]
            t1, x1 = pts[i + 1]
            if t0 <= u <= t1:
                if t1 <= t0:
                    return x1
                return x0 + (x1 - x0) * (u - t0) / (t1 - t0)
        return pts[-1][1]


@dataclass
class ScoreTimeline:
    measures: List[MeasureSpan] = field(default_factory=list)
    source: str = ""

    @property
    def n_measures(self) -> int:
        return len(self.measures)

    @property
    def music_end(self) -> float:
        if not self.measures:
            return 0.0
        return self.measures[-1].end_sec

    def measure_at(self, t: float) -> Tuple[int, float]:
        """t초가 속한 마디 인덱스(0-based)와 마디 내부 진행률(0~1)."""
        if not self.measures:
            return 0, 0.0
        if t <= self.measures[0].start_sec:
            return 0, 0.0
        if t >= self.measures[-1].end_sec:
            return len(self.measures) - 1, 1.0

        lo, hi = 0, len(self.measures) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            m = self.measures[mid]
            if t < m.start_sec:
                hi = mid - 1
            elif t >= m.end_sec:
                lo = mid + 1
            else:
                intra = (t - m.start_sec) / max(m.duration_sec, 1e-6)
                return mid, min(max(intra, 0.0), 1.0)
        idx = min(max(lo, 0), len(self.measures) - 1)
        return idx, 1.0 if t >= self.measures[idx].end_sec else 0.0


def find_sidecar(base_path: Optional[str], extensions: Tuple[str, ...]) -> Optional[str]:
    """pdf/mid 등과 같은 스템의 옆파일 경로를 찾는다."""
    if not base_path:
        return None
    stem, _ = os.path.splitext(base_path)
    for ext in extensions:
        cand = stem + ext
        if os.path.isfile(cand):
            return cand
    parent = os.path.dirname(base_path)
    if not parent or not os.path.isdir(parent):
        return None
    wanted = {e.lower() for e in extensions}
    for name in os.listdir(parent):
        if os.path.splitext(name)[1].lower() in wanted:
            return os.path.join(parent, name)
    return None


def _strip_xmlns(xml_text: str) -> str:
    return re.sub(r'\sxmlns="[^"]+"', "", xml_text, count=1)


def build_timeline_from_musicxml(path: str) -> Optional[ScoreTimeline]:
    try:
        raw = open(path, "r", encoding="utf-8").read()
    except OSError:
        return None
    try:
        root = ET.fromstring(_strip_xmlns(raw))
    except ET.ParseError:
        return None

    part = root.find("part")
    if part is None:
        return None
    measures = part.findall("measure")
    if not measures:
        return None

    tempo = 120.0
    beats, beat_type = 4, 4
    t = 0.0
    spans: List[MeasureSpan] = []

    for meas in measures:
        raw_num = meas.get("number") or str(len(spans) + 1)
        try:
            number = int(re.sub(r"[^\d]", "", raw_num) or len(spans) + 1)
        except ValueError:
            number = len(spans) + 1

        for direction in meas.findall("direction"):
            sound = direction.find("sound")
            if sound is not None and sound.get("tempo"):
                try:
                    tempo = float(sound.get("tempo"))
                except ValueError:
                    pass

        attr = meas.find("attributes")
        if attr is not None:
            ts = attr.find("time")
            if ts is not None:
                try:
                    beats = int(ts.findtext("beats") or beats)
                    beat_type = int(ts.findtext("beat-type") or beat_type)
                except ValueError:
                    pass

        quarters = beats * (4.0 / max(beat_type, 1))
        dur = quarters * (60.0 / max(tempo, 1.0))
        spans.append(MeasureSpan(number=number, start_sec=t, duration_sec=dur, tempo_bpm=tempo))
        t += dur

    if not spans:
        return None
    return ScoreTimeline(measures=spans, source=f"musicxml:{os.path.basename(path)}")


def build_timeline_from_lilypond(path: str) -> Optional[ScoreTimeline]:
    try:
        text = open(path, "r", encoding="utf-8").read()
    except OSError:
        return None

    # 첫 음표 스태프의 마디 번호와 그 앞의 tempo 지시
    staff_match = re.search(
        r"NotesPartZeroStaffZero\s*=\s*\{(?P<body>.*?)\n\}",
        text,
        flags=re.S,
    )
    body = staff_match.group("body") if staff_match else text

    tempo = 120.0
    m = re.search(r"\\tempo\s+4\s*=\s*(\d+)", body)
    if m:
        tempo = float(m.group(1))

    spans: List[MeasureSpan] = []
    t = 0.0
    pending_tempo = tempo
    # 한 줄에 tempo 후 마디 주석이 오는 패턴
    tokens = re.split(r"(\| % \d+|\\tempo\s+4\s*=\s*\d+)", body)
    for tok in tokens:
        tm = re.match(r"\\tempo\s+4\s*=\s*(\d+)", tok)
        if tm:
            pending_tempo = float(tm.group(1))
            continue
        bm = re.match(r"\| % (\d+)", tok)
        if not bm:
            continue
        tempo = pending_tempo
        number = int(bm.group(1))
        dur = 4.0 * (60.0 / max(tempo, 1.0))
        spans.append(MeasureSpan(number=number, start_sec=t, duration_sec=dur, tempo_bpm=tempo))
        t += dur

    if not spans:
        return None
    return ScoreTimeline(measures=spans, source=f"lilypond:{os.path.basename(path)}")


def build_timeline_from_midi(path: str, n_measures: Optional[int] = None) -> Optional[ScoreTimeline]:
    try:
        import pretty_midi
    except ImportError:
        return None
    if not os.path.isfile(path):
        return None
    try:
        pm = pretty_midi.PrettyMIDI(path)
    except Exception:
        return None

    end = float(pm.get_end_time())
    if end <= 0:
        return None

    times, tempi = pm.get_tempo_changes()
    bpm0 = float(tempi[0]) if len(tempi) else 120.0
    n = n_measures
    if not n:
        downbeats = pm.get_downbeats()
        n = max(1, len(downbeats) - 1) if len(downbeats) > 1 else max(1, int(round(end / (4 * 60.0 / bpm0))))

    # MIDI 템포 이벤트가 하나뿐이면 실제 연주 길이를 마디 수에 균등 분배한다.
    # (Klangio MIDI는 템포 변화를 노트 시각에 구워 넣고 메타 템포는 초기를 유지하는 경우가 있다.)
    if len(tempi) <= 1:
        dur = end / n
        spans = [
            MeasureSpan(number=i + 1, start_sec=i * dur, duration_sec=dur, tempo_bpm=bpm0)
            for i in range(n)
        ]
        return ScoreTimeline(measures=spans, source=f"midi-even:{os.path.basename(path)}")

    # 템포 맵이 있으면 박자표 기준 마디를 적분
    beats, beat_type = 4, 4
    if pm.time_signature_changes:
        ts0 = pm.time_signature_changes[0]
        beats, beat_type = ts0.numerator, ts0.denominator
    quarters = beats * (4.0 / max(beat_type, 1))
    spans = []
    t = 0.0
    tempo_idx = 0
    for i in range(n):
        while tempo_idx + 1 < len(times) and times[tempo_idx + 1] <= t + 1e-6:
            tempo_idx += 1
        bpm = float(tempi[tempo_idx])
        dur = quarters * (60.0 / max(bpm, 1.0))
        spans.append(MeasureSpan(number=i + 1, start_sec=t, duration_sec=dur, tempo_bpm=bpm))
        t += dur
    return ScoreTimeline(measures=spans, source=f"midi-tempo:{os.path.basename(path)}")


def build_score_timeline(
    musicxml_path: Optional[str] = None,
    lilypond_path: Optional[str] = None,
    midi_path: Optional[str] = None,
    n_measures: Optional[int] = None,
    log_callback=None,
) -> ScoreTimeline:
    def _log(msg: str) -> None:
        if log_callback:
            log_callback(msg)

    if musicxml_path and os.path.isfile(musicxml_path):
        tl = build_timeline_from_musicxml(musicxml_path)
        if tl:
            _log(f"[타임라인] MusicXML {tl.n_measures}마디, 연주길이 {tl.music_end:.3f}s ({tl.source})")
            return tl

    if lilypond_path and os.path.isfile(lilypond_path):
        tl = build_timeline_from_lilypond(lilypond_path)
        if tl:
            _log(f"[타임라인] LilyPond {tl.n_measures}마디, 연주길이 {tl.music_end:.3f}s ({tl.source})")
            return tl

    if midi_path and os.path.isfile(midi_path):
        tl = build_timeline_from_midi(midi_path, n_measures=n_measures)
        if tl:
            _log(f"[타임라인] MIDI 보조 {tl.n_measures}마디, 연주길이 {tl.music_end:.3f}s ({tl.source})")
            return tl

    _log("[타임라인] 악보 시간축을 만들지 못했습니다. 음원 선형 진행으로 대체합니다.")
    return ScoreTimeline(measures=[], source="empty")
