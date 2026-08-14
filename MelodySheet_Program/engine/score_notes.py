"""마디 안 커서 앵커.

MusicXML 선율(staff 1)의 발음 시각과 default-x 를 마디 세로줄에 붙인다.
Klangio XML의 default-x 는 페이지 좌표가 아니라 마디 폭 대비 기보 위치이므로
실제 픽셀 세로줄 [left, right] 에 비율로 사상한다.
"""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

from engine.score_layout import ScoreLayout
from engine.score_timeline import ScoreTimeline, _strip_xmlns


def _measure_divs(beats: int, beat_type: int, divisions: int) -> int:
    quarters = beats * (4.0 / max(beat_type, 1))
    return max(1, int(round(quarters * divisions)))


def parse_lead_attacks(musicxml_path: str) -> Dict[int, dict]:
    """마디 번호 → {divs, width, attacks:[{div, dur, rest, x}]}"""
    out: Dict[int, dict] = {}
    if not musicxml_path or not os.path.isfile(musicxml_path):
        return out
    try:
        raw = open(musicxml_path, "r", encoding="utf-8").read()
        root = ET.fromstring(_strip_xmlns(raw))
    except (OSError, ET.ParseError):
        return out

    part = root.find("part")
    if part is None:
        return out

    divisions = 12
    beats, beat_type = 4, 4
    for meas in part.findall("measure"):
        raw_num = meas.get("number") or "0"
        try:
            number = int(re.sub(r"[^\d]", "", raw_num) or 0)
        except ValueError:
            continue
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
                    beats = int(ts.findtext("beats") or beats)
                    beat_type = int(ts.findtext("beat-type") or beat_type)
                except ValueError:
                    pass
        try:
            width = float(meas.get("width") or 0.0)
        except ValueError:
            width = 0.0

        cursor = 0
        lead_voice = None
        attacks = []
        for el in list(meas):
            if el.tag == "backup":
                cursor -= int(el.findtext("duration") or 0)
                continue
            if el.tag == "forward":
                cursor += int(el.findtext("duration") or 0)
                continue
            if el.tag != "note":
                continue
            if el.find("grace") is not None or el.find("chord") is not None:
                continue
            staff = el.findtext("staff") or "1"
            if staff != "1":
                continue
            voice = el.findtext("voice") or "1"
            if lead_voice is None:
                lead_voice = voice
            dur = int(el.findtext("duration") or 0)
            if voice == lead_voice:
                dx = el.get("default-x")
                try:
                    x_val = float(dx) if dx is not None else None
                except ValueError:
                    x_val = None
                ties = [t.get("type") for t in el.findall("tie")]
                attacks.append(
                    {
                        "div": max(0, cursor),
                        "dur": max(0, dur),
                        "rest": el.find("rest") is not None,
                        "tie_stop": "stop" in ties,
                        "x": x_val,
                    }
                )
            cursor += dur

        out[number] = {
            "divs": _measure_divs(beats, beat_type, divisions),
            "width": width,
            "attacks": attacks,
        }
    return out


def _anchors_from_attacks(info: dict) -> List[Tuple[float, float]]:
    attacks = info.get("attacks") or []
    divs = max(1, int(info.get("divs") or 1))
    width = float(info.get("width") or 0.0)
    xs = [a["x"] for a in attacks if a.get("x") is not None]
    x0 = min(xs) if xs else 0.0
    x_span = (width - x0) if width > x0 + 1 else 0.0

    pts: List[Tuple[float, float]] = [(0.0, 0.0)]
    for a in attacks:
        if a.get("tie_stop"):
            continue
        t_frac = min(max(a["div"] / divs, 0.0), 1.0)
        if a.get("x") is not None and x_span > 1:
            x_frac = (float(a["x"]) - x0) / x_span
        else:
            x_frac = t_frac
        x_frac = min(max(x_frac, 0.0), 1.0)
        if t_frac <= 1e-6:
            pts[0] = (0.0, x_frac)
        else:
            if pts and abs(pts[-1][0] - t_frac) < 1e-6:
                pts[-1] = (t_frac, x_frac)
            else:
                pts.append((t_frac, x_frac))
    if pts[-1][0] < 0.999:
        pts.append((1.0, 1.0))
    else:
        pts[-1] = (1.0, 1.0)
    return pts


def load_midi_onsets(midi_path: Optional[str]) -> List[float]:
    """비타악기 노트 시작 시각(초). 음원이 따르는 실제 연주 시계."""
    if not midi_path or not os.path.isfile(midi_path):
        return []
    try:
        import pretty_midi
    except ImportError:
        return []
    try:
        pm = pretty_midi.PrettyMIDI(midi_path)
    except Exception:
        return []
    on = []
    for inst in pm.instruments:
        if inst.is_drum:
            continue
        for n in inst.notes:
            on.append(float(n.start))
    return sorted(set(round(t, 5) for t in on))


def _x_frac_of(attack: dict, info: dict) -> float:
    width = float(info.get("width") or 0.0)
    xs = [a["x"] for a in info.get("attacks") or [] if a.get("x") is not None]
    x0 = min(xs) if xs else 0.0
    x_span = (width - x0) if width > x0 + 1 else 0.0
    if attack.get("x") is not None and x_span > 1:
        return min(max((float(attack["x"]) - x0) / x_span, 0.0), 1.0)
    divs = max(1, int(info.get("divs") or 1))
    return min(max(attack["div"] / divs, 0.0), 1.0)


def _anchors_hybrid(info: dict, meas_start: float, meas_dur: float, midi_on: List[float]) -> List[Tuple[float, float]]:
    """가로는 XML 기보, 시각은 마디 안에 떨어진 MIDI onset 을 우선한다."""
    xml_pts = _anchors_from_attacks(info)
    if not midi_on or meas_dur <= 1e-6:
        return xml_pts

    lo, hi = meas_start - 0.02, meas_start + meas_dur - 0.015
    midis = [t for t in midi_on if lo <= t < hi]
    visuals = []
    divs = max(1, int(info.get("divs") or 1))
    for a in info.get("attacks") or []:
        if a.get("rest") or a.get("tie_stop"):
            continue
        visuals.append(
            {
                "t_xml": meas_start + (a["div"] / divs) * meas_dur,
                "x": _x_frac_of(a, info),
            }
        )
    if not visuals:
        return xml_pts
    if not midis:
        return xml_pts

    used_m = set()
    timed: List[Tuple[float, float]] = []
    max_pair_dt = 0.12  # 이보다 먼 MIDI는 다른 음으로 보고 기보 시각을 유지
    pairs: List[Tuple[Optional[float], dict]] = []
    if len(midis) == len(visuals) and all(
        abs(mt - v["t_xml"]) <= max_pair_dt for mt, v in zip(midis, visuals)
    ):
        pairs = [(mt, v) for mt, v in zip(midis, visuals)]
    else:
        for v in visuals:
            cand = [(abs(t - v["t_xml"]), i, t) for i, t in enumerate(midis) if i not in used_m]
            if not cand:
                pairs.append((None, v))
                continue
            cand.sort()
            dt, i, t = cand[0]
            if dt <= max_pair_dt:
                used_m.add(i)
                pairs.append((t, v))
            else:
                pairs.append((None, v))

    for t, v in pairs:
        if t is None:
            tf = min(max((v["t_xml"] - meas_start) / meas_dur, 0.0), 0.999)
        else:
            tf = min(max((t - meas_start) / meas_dur, 0.0), 0.999)
        timed.append((tf, v["x"]))
    # 쉼표는 XML 시각 그대로 넣어 빈 마디도 움직이게 한다
    for a in info.get("attacks") or []:
        if a.get("rest"):
            tf = min(max(a["div"] / divs, 0.0), 0.999)
            timed.append((tf, _x_frac_of(a, info)))

    timed.sort(key=lambda p: (p[0], p[1]))
    pts: List[Tuple[float, float]] = [(0.0, 0.0)]
    for tf, xf in timed:
        if tf <= 1e-6:
            pts[0] = (0.0, xf)
        elif abs(pts[-1][0] - tf) < 1e-4:
            pts[-1] = (tf, xf)
        else:
            pts.append((tf, xf))
    if pts[-1][0] < 0.999:
        pts.append((1.0, 1.0))
    else:
        pts[-1] = (1.0, 1.0)
    return pts


def _anchors_from_score(
    info: dict,
    pdf_xs: Optional[List[int]],
    bar_left: Optional[int],
    bar_right: Optional[int],
) -> List[Tuple[float, float]]:
    """시각 = 악보에 적힌 음표 길이(누적 박), 가로 = PDF 음머리 또는 기보 default-x."""
    attacks = [a for a in (info.get("attacks") or []) if not a.get("tie_stop")]
    if not attacks:
        return [(0.0, 0.0), (1.0, 1.0)]
    divs = max(1, int(info.get("divs") or 1))
    notes = [a for a in attacks if not a.get("rest")]
    use_pdf = (
        pdf_xs
        and bar_left is not None
        and bar_right is not None
        and bar_right > bar_left + 4
        and len(pdf_xs) == len(notes)
    )
    span = float((bar_right - bar_left) if use_pdf else 1)
    pts: List[Tuple[float, float]] = [(0.0, 0.0)]
    ni = 0
    for a in attacks:
        t_frac = min(max(a["div"] / divs, 0.0), 1.0)
        if a.get("rest") or not use_pdf:
            x_frac = _x_frac_of(a, info)
        else:
            x_frac = min(max((pdf_xs[ni] - bar_left) / span, 0.0), 1.0)
            ni += 1
        x_frac = min(max(x_frac, 0.0), 1.0)
        if t_frac <= 1e-6:
            pts[0] = (0.0, x_frac)
        elif abs(pts[-1][0] - t_frac) < 1e-6:
            pts[-1] = (t_frac, x_frac)
        else:
            pts.append((t_frac, x_frac))
    if pts[-1][0] < 0.999:
        pts.append((1.0, 1.0))
    else:
        pts[-1] = (1.0, 1.0)
    return pts


def attach_measure_anchors(
    timeline: ScoreTimeline,
    layout: Optional[ScoreLayout],
    musicxml_path: Optional[str],
    log_callback=None,
    midi_path: Optional[str] = None,
    stitched_img: Optional[Any] = None,
) -> None:
    """마디 앵커: 박자는 악보 기보 길이, 가로는 PDF 음머리(개수가 맞을 때).

    MIDI는 쓰지 않는다. 연주 시각이 아니라 악보에 적힌 박자가 시계다.
    """
    del midi_path
    parsed = parse_lead_attacks(musicxml_path) if musicxml_path else {}
    pdf_map: Dict[int, List[int]] = {}
    if layout and layout.systems and stitched_img is not None:
        from engine.pdf_notes import collect_measure_note_xs

        pdf_map = collect_measure_note_xs(stitched_img, layout)

    used = 0
    pdf_used = 0
    for meas in timeline.measures:
        info = parsed.get(meas.number)
        sys = layout.system_for_measure(meas.number) if layout else None
        left = right = None
        if sys is not None:
            left, right = sys.measure_x_range(meas.number)
        if info and info.get("attacks"):
            heads = pdf_map.get(meas.number) or []
            notes = [a for a in info["attacks"] if not a.get("rest") and not a.get("tie_stop")]
            if heads and len(heads) == len(notes):
                pdf_used += 1
            meas.anchors = _anchors_from_score(info, heads, left, right)
            used += 1
        else:
            meas.anchors = [(0.0, 0.0), (1.0, 1.0)]
    if log_callback:
        log_callback(
            f"[음표 앵커] 악보 기보 박자 {used}/{timeline.n_measures}마디"
            f", PDF 음머리 좌표 {pdf_used}마디 (개수 일치 시만)"
        )


def interpolate_frac(anchors: List[Tuple[float, float]], t_frac: float) -> float:
    if not anchors:
        return t_frac
    t_frac = min(max(t_frac, 0.0), 1.0)
    if t_frac <= anchors[0][0]:
        return anchors[0][1]
    if t_frac >= anchors[-1][0]:
        return anchors[-1][1]
    for i in range(len(anchors) - 1):
        t0, x0 = anchors[i]
        t1, x1 = anchors[i + 1]
        if t0 <= t_frac <= t1:
            if t1 <= t0:
                return x1
            u = (t_frac - t0) / (t1 - t0)
            return x0 + (x1 - x0) * u
    return anchors[-1][1]
