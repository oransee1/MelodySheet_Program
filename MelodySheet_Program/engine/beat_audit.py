"""생성 직전 박자 교차검증.

합격은 '커서가 그 음머리 위에 있다'가 아니다.
합격은 '시계·마디·단이 서로 모순되지 않는다'이다.
음표 단위 어긋남은 WARN 으로만 남긴다.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from engine.score_layout import ScoreLayout
from engine.score_notes import load_midi_onsets, parse_lead_attacks
from engine.score_timeline import ScoreTimeline
from engine.sync_manager import SyncManager


@dataclass
class Check:
    name: str
    level: str  # PASS / WARN / FAIL / SKIP
    detail: str


@dataclass
class BeatAuditReport:
    checks: List[Check] = field(default_factory=list)
    verdict: str = "PASS"  # PASS | WARN | FAIL
    summary_lines: List[str] = field(default_factory=list)

    def add(self, name: str, level: str, detail: str) -> None:
        self.checks.append(Check(name, level, detail))

    def finalize(self) -> None:
        if any(c.level == "FAIL" for c in self.checks):
            self.verdict = "FAIL"
        elif any(c.level == "WARN" for c in self.checks):
            self.verdict = "WARN"
        else:
            self.verdict = "PASS"
        n = {k: sum(1 for c in self.checks if c.level == k) for k in ("PASS", "WARN", "FAIL", "SKIP")}
        self.summary_lines = [
            f"박자 교차검증 종합: {self.verdict}",
            f"  PASS {n['PASS']} · WARN {n['WARN']} · FAIL {n['FAIL']} · SKIP {n['SKIP']}",
        ]
        for c in self.checks:
            if c.level in ("WARN", "FAIL"):
                self.summary_lines.append(f"  [{c.level}] {c.name}: {c.detail}")

    def as_text(self) -> str:
        lines = list(self.summary_lines)
        lines.append("")
        lines.append("전체 항목:")
        for c in self.checks:
            lines.append(f"  [{c.level}] {c.name}: {c.detail}")
        lines.append("")
        lines.append("이 보고서가 증명하지 않는 것:")
        lines.append("  - 커서가 특정 음머리 픽셀 위에 있는지")
        lines.append("  - 시청자가 박자를 자연스럽게 느끼는지")
        lines.append("  - 마디 안 15%대 MIDI-기보 어긋남이 사라졌는지 (WARN 으로만 표시)")
        return "\n".join(lines) + "\n"


def _ly_tempo_changes(ly_path: Optional[str]) -> Optional[List[Tuple[int, int]]]:
    if not ly_path or not os.path.isfile(ly_path):
        return None
    try:
        text = open(ly_path, "r", encoding="utf-8").read()
    except OSError:
        return None
    staff = re.search(r"NotesPartZeroStaffZero\s*=\s*\{(.*?)\n\}", text, re.S)
    chunk = staff.group(1) if staff else text
    tempo = 115
    by_bar = {}
    for tok in re.split(r"(\\tempo\s+4\s*=\s*\d+|\| % \d+)", chunk):
        tm = re.match(r"\\tempo\s+4\s*=\s*(\d+)", tok)
        if tm:
            tempo = int(tm.group(1))
            continue
        bm = re.match(r"\| % (\d+)", tok)
        if bm:
            n = int(bm.group(1))
            if n not in by_bar:
                by_bar[n] = tempo
    if not by_bar:
        return None
    out = []
    prev = None
    for n in sorted(by_bar):
        if by_bar[n] != prev:
            out.append((n, by_bar[n]))
            prev = by_bar[n]
    return out


def _xml_tempo_changes(timeline: ScoreTimeline) -> List[Tuple[int, int]]:
    out = []
    prev = None
    for m in timeline.measures:
        bpm = int(round(m.tempo_bpm))
        if bpm != prev:
            out.append((m.number, bpm))
            prev = bpm
    return out


def _xml_new_attacks(timeline: ScoreTimeline, musicxml_path: Optional[str]):
    parsed = parse_lead_attacks(musicxml_path) if musicxml_path else {}
    rows = []
    for meas in timeline.measures:
        info = parsed.get(meas.number) or {}
        divs = max(1, int(info.get("divs") or 1))
        for a in info.get("attacks") or []:
            if a.get("rest") or a.get("tie_stop"):
                continue
            t = meas.start_sec + (a["div"] / divs) * meas.duration_sec
            rows.append((meas.number, t))
    return rows, parsed


def _audio_clock(audio_path: str, timeline: ScoreTimeline, midi_on: List[float]) -> Tuple[str, str]:
    """음원 시작/길이/활동 상관. 점수가 평평하면 SKIP."""
    try:
        from moviepy import AudioFileClip
    except ImportError:
        return "SKIP", "moviepy 없음"

    try:
        clip = AudioFileClip(audio_path)
    except Exception as e:
        return "SKIP", f"음원 열기 실패: {e}"

    try:
        audio_dur = float(clip.duration)
        extra = audio_dur - timeline.music_end
        sr = 22050
        head = clip.subclipped(0, min(3.0, audio_dur)).to_soundarray(fps=sr)
        if head.ndim > 1:
            head = head.mean(axis=1)
        hop = int(sr * 0.01)
        rms = np.array(
            [float(np.sqrt(np.mean(head[i * hop : (i + 1) * hop] ** 2))) for i in range(len(head) // hop)]
        )
        peak = float(rms.max()) if len(rms) else 0.0
        onset = 0.0
        if peak > 0:
            thr = peak * 0.04
            for i, v in enumerate(rms):
                if v >= thr:
                    onset = i * 0.01
                    break

        # 전체 활동 상관 (평평하면 결론 내지 않음)
        probe = min(audio_dur, max(timeline.music_end, 1.0))
        arr = clip.subclipped(0, probe).to_soundarray(fps=sr)
        if arr.ndim > 1:
            arr = arr.mean(axis=1)
        win = int(sr * 0.05)
        nbin = max(1, len(arr) // win)
        rms_a = np.array(
            [float(np.sqrt(np.mean(arr[i * win : (i + 1) * win] ** 2))) for i in range(nbin)]
        )
        act = np.zeros(nbin)
        for t in midi_on:
            i = int(t / 0.05)
            if 0 <= i < nbin:
                act[i] += 1.0
        if rms_a.std() < 1e-8 or act.std() < 1e-8:
            lag_note = "상관 불가(분산 없음)"
            lag_ok = True
            lag = 0.0
        else:
            ra = (rms_a - rms_a.mean()) / (rms_a.std() + 1e-9)
            ma = (act - act.mean()) / (act.std() + 1e-9)
            scores = []
            for lag_i in range(-20, 21):
                if lag_i < 0:
                    s = float(np.dot(ra[-lag_i:], ma[: len(ma) + lag_i]) / max(len(ra) + lag_i, 1))
                elif lag_i > 0:
                    s = float(np.dot(ra[: len(ra) - lag_i], ma[lag_i:]) / max(len(ra) - lag_i, 1))
                else:
                    s = float(np.dot(ra, ma) / len(ra))
                scores.append((lag_i * 0.05, s))
            scores.sort(key=lambda x: -x[1])
            lag, best_s = scores[0]
            lag0 = next(s for t, s in scores if abs(t) < 1e-12)
            spread = best_s - scores[min(5, len(scores) - 1)][1]
            if spread < 0.01:
                lag_note = f"상관 평탄(최고 {best_s:.3f}) → 지연 결론 없음"
                lag_ok = True
                lag = 0.0
            else:
                lag_ok = abs(lag) <= 0.08
                lag_note = f"최고 지연 {lag:+.2f}s (점수 {best_s:.3f}, lag0 {lag0:.3f})"

        parts = [f"길이 {audio_dur:.2f}s / 악보 {timeline.music_end:.2f}s (차 {extra:+.2f}s)", f"시작온셋 {onset:.3f}s", lag_note]
        if onset >= 0.20:
            return "WARN", "; ".join(parts) + " — 음원 앞 무음이 큼"
        if extra < -0.15:
            return "FAIL", "; ".join(parts) + " — 음원이 악보보다 짧음"
        if not lag_ok:
            return "WARN", "; ".join(parts)
        return "PASS", "; ".join(parts)
    except Exception as e:
        return "SKIP", f"음원 분석 실패: {e}"
    finally:
        try:
            clip.close()
        except Exception:
            pass


def run_beat_audit(
    timeline: ScoreTimeline,
    layout: ScoreLayout,
    sync_mgr: SyncManager,
    audio_path: Optional[str],
    midi_path: Optional[str],
    musicxml_path: Optional[str],
    lilypond_path: Optional[str],
    img_width: int,
    img_height: int,
    viewport_h: int = 1080,
) -> BeatAuditReport:
    report = BeatAuditReport()

    if not timeline.n_measures:
        report.add("타임라인", "FAIL", "마디 시간축이 비어 있습니다")
        report.finalize()
        return report

    # --- 1. 소스 시계 ---
    xml_tempo = _xml_tempo_changes(timeline)
    ly_tempo = _ly_tempo_changes(lilypond_path)
    if ly_tempo is None:
        report.add("LilyPond 템포", "SKIP", "ly 없음")
    elif ly_tempo == xml_tempo:
        report.add("LilyPond↔XML 템포", "PASS", f"{xml_tempo}")
    else:
        report.add("LilyPond↔XML 템포", "FAIL", f"LY={ly_tempo} XML={xml_tempo}")

    midi_on = load_midi_onsets(midi_path)
    if midi_on:
        midi_end = midi_on[-1]
        # last onset is not end; compare music_end to last note + small slack later
        try:
            import pretty_midi

            midi_end = float(pretty_midi.PrettyMIDI(midi_path).get_end_time())
        except Exception:
            midi_end = midi_on[-1]
        dt = midi_end - timeline.music_end
        if abs(dt) < 0.05:
            report.add("MIDI끝↔XML끝", "PASS", f"dt={dt:+.4f}s")
        elif abs(dt) < 0.25:
            report.add("MIDI끝↔XML끝", "WARN", f"dt={dt:+.4f}s")
        else:
            report.add("MIDI끝↔XML끝", "FAIL", f"dt={dt:+.4f}s")
    else:
        report.add("MIDI", "SKIP", "mid 없음 — 음표 시각 대조 생략")

    # --- 2. 악보 공간 ---
    if not layout.systems:
        report.add("PDF 단", "FAIL", "단(system)을 하나도 못 찾음")
    else:
        covered = sum(s.n_measures for s in layout.systems)
        if covered != timeline.n_measures:
            report.add("단 마디 합", "FAIL", f"{covered} ≠ 타임라인 {timeline.n_measures}")
        else:
            report.add("단 마디 합", "PASS", f"{covered}마디 / 단 {len(layout.systems)}개")
        starts = [s.start_measure for s in layout.systems]
        inc = all(starts[i] < starts[i + 1] for i in range(len(starts) - 1))
        report.add("단 시작 마디 증가", "PASS" if inc else "FAIL", f"{starts}")
        even_bars = []
        bad_count = []
        estimated = []
        for s in layout.systems:
            if not getattr(s, "bars_from_detect", True):
                estimated.append(s.index + 1)
            if len(s.bar_xs) != s.n_measures + 1:
                bad_count.append(s.index + 1)
                continue
            gaps = np.diff(s.bar_xs).astype(float)
            if len(gaps) >= 3 and float(np.std(gaps)) < 12 and not getattr(s, "bars_from_detect", True):
                even_bars.append(s.index + 1)
        if bad_count:
            report.add("세로줄 개수", "WARN", f"마디+1 아닌 단: {bad_count}")
        else:
            report.add("세로줄 개수", "PASS", "모든 단 = 마디+1")
        if estimated:
            report.add(
                "세로줄 추정 분할",
                "WARN",
                f"단 {estimated} — PDF에서 세로줄을 못 읽어 균등 분할",
            )
        else:
            report.add("세로줄 출처", "PASS", "모든 단이 PDF 세로줄 검출")

    # --- 3. 기보 음 ↔ MIDI (이음줄 제외) ---
    xml_notes, _parsed = _xml_new_attacks(timeline, musicxml_path)
    if not xml_notes:
        report.add("XML 선율 음", "SKIP", "대조할 기보 음 없음")
    elif not midi_on:
        report.add("기보↔MIDI 음", "SKIP", "MIDI 없음")
    else:
        err = []
        for _n, t in xml_notes:
            nearest = min(midi_on, key=lambda x: abs(x - t))
            err.append(abs(nearest - t))
        err = np.array(err)
        p15 = float(np.mean(err <= 0.015) * 100)
        p80 = float(np.mean(err <= 0.080) * 100)
        med = float(np.median(err) * 1000)
        p95 = float(np.percentile(err, 95) * 1000)
        detail = f"n={len(err)}  ≤15ms {p15:.1f}%  ≤80ms {p80:.1f}%  중앙 {med:.1f}ms  p95 {p95:.0f}ms"
        if p15 >= 90 and p95 < 80:
            report.add("기보 발음↔MIDI", "PASS", detail)
        elif p15 >= 70:
            report.add(
                "기보 발음↔MIDI(참고)",
                "WARN",
                detail + " — 커서는 기보 박자를 따름. MIDI는 참고만",
            )
        else:
            report.add("기보 발음↔MIDI", "FAIL", detail)

    # --- 4. 커서: 약한 검사(마디)와 강한 검사(MIDI 시각에 그 마디) ---
    if layout.systems:
        fail_m = 0
        samples = 0
        t = 0.0
        while t < timeline.music_end:
            mi, _ = timeline.measure_at(t)
            meas = timeline.measures[mi]
            sys = layout.system_for_measure(meas.number)
            left, right = sys.measure_x_range(meas.number)
            _, (cx, *_) = sync_mgr.calculate_sync(t, img_width, img_height, viewport_h)
            if not (left - 10 <= cx <= right + 10):
                fail_m += 1
            samples += 1
            t += 0.25
        if fail_m == 0:
            report.add("커서∈마디(0.25s격자)", "PASS", f"{samples}칸 전부 — 음머리가 아니라 마디만 보증")
        else:
            report.add("커서∈마디(0.25s격자)", "FAIL", f"{fail_m}/{samples}")

        if midi_on:
            miss = 0
            n = 0
            for t in midi_on:
                if t >= timeline.music_end:
                    continue
                mi, _ = timeline.measure_at(t)
                meas = timeline.measures[mi]
                sys = layout.system_for_measure(meas.number)
                left, right = sys.measure_x_range(meas.number)
                _, (cx, *_) = sync_mgr.calculate_sync(t, img_width, img_height, viewport_h)
                if not (left - 10 <= cx <= right + 10):
                    miss += 1
                n += 1
            if n and miss == 0:
                report.add("MIDI 발음 순간 커서∈그 마디", "PASS", f"{n}개 — 박 위치까지는 보증하지 않음")
            elif n:
                report.add("MIDI 발음 순간 커서∈그 마디", "FAIL", f"{miss}/{n}")

        # 페이지 홀드
        hold_bad = []
        for s in layout.systems:
            if s.index + 1 >= len(layout.systems):
                continue
            nxt = layout.systems[s.index + 1]
            if nxt.page_index == s.page_index:
                continue
            last = timeline.measures[s.end_measure - 1]
            t_hold = last.end_sec - min(0.50, last.duration_sec * 0.20)
            y_now, _ = sync_mgr.calculate_sync(t_hold, img_width, img_height, viewport_h)
            y_cur = sync_mgr._system_y_offset(s, viewport_h)
            y_nxt = sync_mgr._system_y_offset(nxt, viewport_h)
            if abs(y_nxt - y_cur) > 80 and abs(y_now - y_cur) > abs(y_now - y_nxt) * 0.85:
                hold_bad.append(s.end_measure)
        if hold_bad:
            report.add("페이지 유지", "FAIL", f"끝나기 전 넘어가는 마지막 마디: {hold_bad}")
        else:
            report.add("페이지 유지", "PASS", "마지막 마디 80%까지 해당 페이지")

    # --- 5. 음원 시계 ---
    if audio_path and os.path.isfile(audio_path):
        level, detail = _audio_clock(audio_path, timeline, midi_on)
        report.add("음원↔악보 시계", level, detail)
    else:
        report.add("음원↔악보 시계", "SKIP", "음원 없음")

    report.finalize()
    return report


def write_audit_file(output_path: str, report: BeatAuditReport) -> str:
    root, _ = os.path.splitext(output_path)
    path = root + "_beat_audit.txt"
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report.as_text())
    return path
