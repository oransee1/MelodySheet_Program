"""성부(바이올린·첼로 등)가 악보 음정·화성대로인지 대조.

시계는 악보 마디 격자. 비교 대상은 MusicXML 해당 성부와
MIDI에서 그 악기 트랙뿐이다. 이음줄로만 이어지는 음은 새 발음이 아니다.
"""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from engine.nonchord import classify_event_pitches, classify_tone, count_roles, fill_harmony_map
from engine.piano_chords import _pc_set, parse_written_harmonies
from engine.score_notes import _strip_xmlns
from engine.score_timeline import ScoreTimeline

ONSET_TOL = 0.080  # 절대시각 일치
PITCH_WINDOW = 3.50  # 같은 음정 탐색 폭(초). 입구가 악보보다 ~2.5초 늦는 경우 허용


@dataclass(frozen=True)
class PartSpec:
    key: str
    label: str
    name_needles: Tuple[str, ...]
    name_exclude: Tuple[str, ...]
    programs: Tuple[int, ...]
    fallback_part_id: str
    source: str
    report_suffix: str


VIOLIN = PartSpec(
    key="violin",
    label="바이올린",
    name_needles=("violin", "바이올린", "vn"),
    name_exclude=("cello", "violoncello"),
    programs=(40,),
    fallback_part_id="P1",
    source="MIDI Violin vs MusicXML P1",
    report_suffix="_violin_audit.txt",
)

CELLO = PartSpec(
    key="cello",
    label="첼로",
    name_needles=("cello", "violoncello", "첼로", "vc"),
    name_exclude=(),
    programs=(42,),
    fallback_part_id="P2",
    source="MIDI Cello vs MusicXML P2",
    report_suffix="_cello_audit.txt",
)

BASS = PartSpec(
    key="bass",
    label="베이스",
    name_needles=("double bass", "contrabass", "doublebass", "string bass", "bass", "베이스", "콘트라베이스"),
    name_exclude=("bassoon", "clarinet", "trombone"),
    programs=(43,),
    fallback_part_id="P3",
    source="MIDI Double Bass vs MusicXML P3",
    report_suffix="_bass_audit.txt",
)


def _midi_pitch(step: str, alter: float, octave: int) -> int:
    semitone = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[step[0]]
    return 12 * (octave + 1) + semitone + int(round(alter))


def _pitch_name(midi: int) -> str:
    names = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
    return f"{names[midi % 12]}{midi // 12 - 1}"


def _name_matches(name: str, spec: PartSpec) -> bool:
    n = (name or "").lower()
    if any(ex in n for ex in spec.name_exclude):
        return False
    return any(nd in n for nd in spec.name_needles)


@dataclass
class PartEvent:
    measure: int
    time_sec: float
    pitches: List[int]


@dataclass
class PartHit:
    measure: int
    time_sec: float
    written: List[int]
    played: List[int]
    onset_ok: bool
    pitch_ok: bool
    chord_ok: Optional[bool]
    written_chord: str
    roles: List[str] = field(default_factory=list)


@dataclass
class PartAuditReport:
    n_written: int = 0
    n_played: int = 0
    n_onset: int = 0
    n_pitch: int = 0
    n_extra: int = 0
    n_chord_cmp: int = 0
    n_chord_ok: int = 0
    n_written_pitches: int = 0
    n_seq_lcs: int = 0
    n_bag: int = 0
    time_err_ms: List[float] = field(default_factory=list)
    hits: List[PartHit] = field(default_factory=list)
    extras: List[Tuple[int, float, int, str]] = field(default_factory=list)
    role_counts: dict = field(default_factory=dict)
    extra_role_counts: dict = field(default_factory=dict)
    source: str = ""
    label: str = ""

    def summary_lines(self) -> List[str]:
        ow = 100.0 * self.n_onset / max(self.n_written, 1)
        pw = 100.0 * self.n_pitch / max(self.n_written, 1)
        cw = 100.0 * self.n_chord_ok / max(self.n_chord_cmp, 1)
        if self.time_err_ms:
            te = sorted(self.time_err_ms)
            med = te[len(te) // 2]
            p95 = te[int(len(te) * 0.95) - 1] if len(te) > 1 else te[0]
            terr = f"짝지은 음 시각오차 중앙 {med:.0f}ms p95 {p95:.0f}ms"
        else:
            terr = "짝지은 음 없음"
        shorter = max(min(self.n_written_pitches, self.n_played), 1)
        sw = 100.0 * self.n_seq_lcs / shorter
        bw = 100.0 * self.n_bag / max(self.n_written_pitches, 1)
        return [
            f"{self.label} 교차검증 ({self.source})",
            f"  기보 발음 {self.n_written} · MIDI {self.n_played} · "
            f"같은 음정 대응 {self.n_pitch} ({pw:.0f}%) · 절대시각±80ms {self.n_onset} ({ow:.0f}%)",
            f"  시각 무시 음정수열 LCS {self.n_seq_lcs}/{shorter} ({sw:.0f}%) · "
            f"음표가방 {self.n_bag}/{max(self.n_written_pitches, 1)} ({bw:.0f}%)",
            f"  {terr}",
            f"  기보에 없는 MIDI {self.n_extra} · "
            f"기보음이 그 마디 화성구성음 {self.n_chord_ok}/{self.n_chord_cmp} ({cw:.0f}%)",
            f"  기보 선율 역할: " + _fmt_roles(self.role_counts),
            f"  기보 밖 MIDI 역할: " + _fmt_roles(self.extra_role_counts),
        ]

    def as_text(self) -> str:
        lines = self.summary_lines()
        lines.append("")
        lines.append("시각    마디  기보           MIDI           온셋 음정 화성 역할")
        for h in self.hits:
            wr = ",".join(_pitch_name(p) for p in h.written) or "-"
            pl = ",".join(_pitch_name(p) for p in h.played) or "-"
            o = "Y" if h.onset_ok else "n"
            p = "Y" if h.pitch_ok else "n"
            c = "-" if h.chord_ok is None else ("Y" if h.chord_ok else "n")
            role = ",".join(h.roles) if h.roles else "-"
            lines.append(
                f"{h.time_sec:7.3f} m{h.measure:<3d} {wr:<14} {pl:<14} {o}    {p}    {c}  {h.written_chord:<8} {role}"
            )
        if self.extras:
            lines.append("")
            lines.append("기보에 없는 MIDI (연주에만 있는 음):")
            for row in self.extras[:40]:
                meas, t, pitch, role = row
                lines.append(f"  t={t:.3f} m{meas} {_pitch_name(pitch)}  {role}")
        lines.append("")
        lines.append("이음줄 종료음은 새 발음이 아니다. 겹음은 한 시각의 음정 집합으로 본다.")
        return "\n".join(lines) + "\n"


def _fmt_roles(counts: dict) -> str:
    if not counts:
        return "-"
    order = ["구성음", "경과음", "보조음", "이탈음", "전타음", "전악음", "걸림음", "비화성음", "코드없음"]
    parts = [f"{k} {counts[k]}" for k in order if counts.get(k)]
    extra = [f"{k} {v}" for k, v in counts.items() if k not in order]
    return " ".join(parts + extra) if (parts or extra) else "-"


def _lcs_len(a: List[int], b: List[int]) -> int:
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return 0
    dp = [0] * (m + 1)
    for x in a:
        prev = 0
        for j, y in enumerate(b, 1):
            cur = dp[j]
            dp[j] = prev + 1 if x == y else max(dp[j], dp[j - 1])
            prev = cur
    return dp[m]


def parse_part_score(
    musicxml_path: Optional[str],
    timeline: ScoreTimeline,
    spec: PartSpec,
) -> List[PartEvent]:
    if not musicxml_path or not os.path.isfile(musicxml_path) or not timeline.n_measures:
        return []
    try:
        root = ET.fromstring(_strip_xmlns(open(musicxml_path, "r", encoding="utf-8").read()))
    except (OSError, ET.ParseError):
        return []

    part = None
    plist = root.find("part-list")
    wanted_id = None
    if plist is not None:
        for sp in plist.findall("score-part"):
            name = (sp.findtext("part-name") or "") + " " + (sp.findtext("score-instrument/instrument-name") or "")
            if _name_matches(name, spec):
                wanted_id = sp.get("id")
                break
            for mi in sp.findall("midi-instrument") + sp.findall("score-instrument"):
                prog = mi.findtext("midi-program")
                if prog:
                    try:
                        if (int(prog) - 1) in spec.programs:
                            wanted_id = sp.get("id")
                            break
                    except ValueError:
                        pass
            if wanted_id:
                break
    for p in root.findall("part"):
        if wanted_id and p.get("id") == wanted_id:
            part = p
            break
    if part is None:
        for p in root.findall("part"):
            if p.get("id") == spec.fallback_part_id:
                part = p
                break
    if part is None:
        return []

    meas_meta: Dict[int, int] = {m.number: i for i, m in enumerate(timeline.measures)}
    events: List[PartEvent] = []
    transpose_semi = 0
    for meas in part.findall("measure"):
        raw_n = meas.get("number") or ""
        try:
            num = int(re.sub(r"[^\d]", "", raw_n) or 0)
        except ValueError:
            continue
        if num not in meas_meta:
            continue
        idx = meas_meta[num]
        tl = timeline.measures[idx]
        divisions = 12
        beats, beat_type = 4, 4
        attr = meas.find("attributes")
        if attr is not None:
            if attr.findtext("divisions"):
                try:
                    divisions = int(attr.findtext("divisions"))
                except ValueError:
                    pass
            ts = attr.find("time")
            if ts is not None:
                try:
                    beats = int(ts.findtext("beats") or 4)
                    beat_type = int(ts.findtext("beat-type") or 4)
                except ValueError:
                    pass
            tr = attr.find("transpose")
            if tr is not None:
                try:
                    chromatic = int(float(tr.findtext("chromatic") or 0))
                except ValueError:
                    chromatic = 0
                try:
                    oct_ch = int(float(tr.findtext("octave-change") or 0))
                except ValueError:
                    oct_ch = 0
                transpose_semi = chromatic + 12 * oct_ch
        mdivs = max(1, int(round(beats * (4.0 / max(beat_type, 1)) * divisions)))
        cursor = 0
        last_onset: Optional[int] = None
        bucket: Dict[int, List[int]] = {}
        for el in list(meas):
            if el.tag == "backup":
                cursor -= int(el.findtext("duration") or 0)
                continue
            if el.tag == "forward":
                cursor += int(el.findtext("duration") or 0)
                continue
            if el.tag != "note" or el.find("grace") is not None:
                continue
            is_chord = el.find("chord") is not None
            dur = int(el.findtext("duration") or 0)
            if el.find("rest") is not None:
                if not is_chord:
                    cursor += dur
                    last_onset = None
                continue
            ties = [t.get("type") for t in el.findall("tie")]
            if "stop" in ties:
                # start+stop 은 이음줄 중간. 새 발음이 아니다.
                if not is_chord:
                    cursor += dur
                continue
            step = el.findtext("pitch/step")
            octv = el.findtext("pitch/octave")
            onset = last_onset if is_chord and last_onset is not None else cursor
            if step and octv:
                try:
                    alter = float(el.findtext("pitch/alter") or 0)
                    bucket.setdefault(onset, []).append(
                        _midi_pitch(step, alter, int(octv)) + transpose_semi
                    )
                except (TypeError, ValueError, KeyError):
                    pass
            if not is_chord:
                last_onset = cursor
                cursor += dur
        for div, pits in sorted(bucket.items()):
            t = tl.start_sec + (div / mdivs) * tl.duration_sec
            events.append(PartEvent(num, t, sorted(set(pits))))
    events.sort(key=lambda e: (e.time_sec, e.measure))
    return events


def load_part_midi(midi_path: str, spec: PartSpec) -> List[Tuple[float, int]]:
    import pretty_midi

    pm = pretty_midi.PrettyMIDI(midi_path)
    out = []
    for inst in pm.instruments:
        if inst.is_drum:
            continue
        name = inst.name or ""
        if inst.program not in spec.programs and not _name_matches(name, spec):
            continue
        for n in inst.notes:
            out.append((float(n.start), int(n.pitch)))
    out.sort()
    return out


def audit_part(
    timeline: ScoreTimeline,
    midi_path: Optional[str],
    musicxml_path: Optional[str],
    spec: PartSpec,
) -> PartAuditReport:
    report = PartAuditReport(source=spec.source, label=spec.label)
    written = parse_part_score(musicxml_path, timeline, spec)
    report.n_written = len(written)
    if not midi_path or not os.path.isfile(midi_path):
        report.source = f"{spec.label} MIDI 없음"
        return report
    try:
        played = load_part_midi(midi_path, spec)
    except Exception:
        report.source = f"{spec.label} MIDI를 읽지 못함"
        return report
    report.n_played = len(played)
    wr_flat = [p for ev in written for p in ev.pitches]
    md_flat = [p for _t, p in played]
    report.n_written_pitches = len(wr_flat)
    report.n_seq_lcs = _lcs_len(wr_flat, md_flat)
    report.n_bag = sum((Counter(wr_flat) & Counter(md_flat)).values())
    if not written:
        report.source = f"악보 {spec.label} 성부 없음"
        return report

    harm = fill_harmony_map(parse_written_harmonies(musicxml_path), timeline.n_measures)
    used_midi: Set[int] = set()
    role_labels: List[str] = []

    for ei, ev in enumerate(written):
        played_p: List[int] = []
        pitch_ok = False
        onset_ok = False
        for need in ev.pitches:
            cands = [
                (abs(t - ev.time_sec), i, t, p)
                for i, (t, p) in enumerate(played)
                if i not in used_midi and p == need and abs(t - ev.time_sec) <= PITCH_WINDOW
            ]
            if not cands:
                continue
            cands.sort()
            dt, i, t, p = cands[0]
            used_midi.add(i)
            played_p.append(p)
            report.time_err_ms.append(abs(dt) * 1000.0)
            if dt <= ONSET_TOL:
                onset_ok = True
        if ev.pitches and set(ev.pitches).issubset(set(played_p)):
            pitch_ok = True
        elif ev.pitches and set(played_p) & set(ev.pitches) and len(ev.pitches) == 1:
            pitch_ok = True
        chord_ok = None
        ch = harm.get(ev.measure, "")
        pcs = _pc_set(ch) if ch else set()
        if ch and ev.pitches and pcs:
            chord_ok = all((p % 12) in pcs for p in ev.pitches)
        prev_p = max(written[ei - 1].pitches) if ei > 0 and written[ei - 1].pitches else None
        next_p = max(written[ei + 1].pitches) if ei + 1 < len(written) and written[ei + 1].pitches else None
        prev_ch = _pc_set(harm.get(written[ei - 1].measure, "")) if ei > 0 else None
        next_ch = _pc_set(harm.get(written[ei + 1].measure, "")) if ei + 1 < len(written) else None
        roles = classify_event_pitches(ev.pitches, prev_p, next_p, pcs, prev_ch, next_ch)
        role_labels.extend(roles)
        if onset_ok:
            report.n_onset += 1
        if pitch_ok:
            report.n_pitch += 1
        if chord_ok is not None:
            report.n_chord_cmp += 1
            if chord_ok:
                report.n_chord_ok += 1
        report.hits.append(
            PartHit(
                measure=ev.measure,
                time_sec=ev.time_sec,
                written=ev.pitches,
                played=sorted(played_p),
                onset_ok=onset_ok,
                pitch_ok=pitch_ok,
                chord_ok=chord_ok,
                written_chord=ch,
                roles=roles,
            )
        )
    report.role_counts = count_roles(role_labels)

    meas_of = []
    for t, p in played:
        mi = 0
        for i, m in enumerate(timeline.measures):
            if m.start_sec <= t < m.end_sec:
                mi = m.number
                break
        meas_of.append(mi)
    extra_roles = []
    unused = [(i, t, p) for i, (t, p) in enumerate(played) if i not in used_midi]
    for k, (i, t, p) in enumerate(unused):
        meas_n = meas_of[i]
        ch = harm.get(meas_n, "")
        pcs = _pc_set(ch) if ch else set()
        prev_p = unused[k - 1][2] if k > 0 else None
        next_p = unused[k + 1][2] if k + 1 < len(unused) else None
        prev_ch = _pc_set(harm.get(meas_of[unused[k - 1][0]], "")) if k > 0 else None
        next_ch = _pc_set(harm.get(meas_of[unused[k + 1][0]], "")) if k + 1 < len(unused) else None
        role = classify_tone(prev_p, p, next_p, pcs, prev_ch, next_ch)
        extra_roles.append(role)
        report.n_extra += 1
        report.extras.append((meas_n, t, p, role))
    report.extra_role_counts = count_roles(extra_roles)
    return report


def write_part_report(output_path: str, report: PartAuditReport, spec: PartSpec) -> str:
    root, _ = os.path.splitext(output_path)
    path = root + spec.report_suffix
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report.as_text())
    return path
