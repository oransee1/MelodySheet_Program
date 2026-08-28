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

    part = None
    part_list = root.find("part-list")
    if part_list is not None:
        for score_part in part_list.findall("score-part"):
            pname = score_part.findtext("part-name") or ""
            if "piano" in pname.lower() or "피아노" in pname:
                pid = score_part.get("id")
                part = root.find(f"part[@id='{pid}']")
                break
    if part is None:
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
        attacks_by_div = {}
        for el in list(meas):
            if el.tag == "backup":
                cursor -= int(el.findtext("duration") or 0)
                cursor = max(0, cursor)
                continue
            if el.tag == "forward":
                cursor += int(el.findtext("duration") or 0)
                continue
            if el.tag != "note":
                continue
            if el.find("grace") is not None:
                continue

            dur = int(el.findtext("duration") or 0)
            is_chord = el.find("chord") is not None
            is_rest = el.find("rest") is not None
            note_div = max(0, cursor - dur) if is_chord else cursor

            dx = el.get("default-x")
            try:
                x_val = float(dx) if dx is not None else None
            except ValueError:
                x_val = None

            ties = [t.get("type") for t in el.findall("tie")]
            is_tie_stop = "stop" in ties

            if not is_tie_stop and not is_rest:
                if note_div not in attacks_by_div:
                    attacks_by_div[note_div] = {
                        "div": note_div,
                        "dur": dur,
                        "rest": False,
                        "tie_stop": False,
                        "x": x_val,
                    }
                elif x_val is not None and (attacks_by_div[note_div]["x"] is None or x_val < attacks_by_div[note_div]["x"]):
                    attacks_by_div[note_div]["x"] = x_val
            elif is_rest and note_div not in attacks_by_div:
                attacks_by_div[note_div] = {
                    "div": note_div,
                    "dur": dur,
                    "rest": True,
                    "tie_stop": False,
                    "x": x_val,
                }

            if not is_chord:
                cursor += dur

        sorted_attacks = [attacks_by_div[d] for d in sorted(attacks_by_div.keys())]
        out[number] = {
            "divs": _measure_divs(beats, beat_type, divisions),
            "width": width,
            "attacks": sorted_attacks,
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
    divs = max(1, int(info.get("divs") or 1))
    t_frac = min(max(attack.get("div", 0) / divs, 0.0), 1.0)
    attacks = info.get("attacks") or []
    xs = [float(a["x"]) for a in attacks if a.get("x") is not None and not a.get("rest")]
    if not xs or attack.get("x") is None or attack.get("rest"):
        return t_frac
    min_x = min(xs)
    max_x = max(xs)
    if max_x <= min_x:
        return 0.15 + t_frac * 0.70
    norm = (float(attack["x"]) - min_x) / (max_x - min_x)
    pad_left = 0.08
    pad_right = 0.12
    return min(max(pad_left + norm * (1.0 - pad_left - pad_right), 0.0), 1.0)


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
        if pts:
            xf = max(xf, pts[-1][1])
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
    meas_start: float = 0.0,
    meas_dur: float = 0.0,
    midi_on: Optional[List[float]] = None,
) -> List[Tuple[float, float]]:
    """시각 = 실제 MIDI 연주 시각 (우선) 또는 악보 누적 박, 가로 = PDF 기보 위치 (우선) 또는 MusicXML."""
    attacks = [a for a in (info.get("attacks") or []) if not a.get("tie_stop")]
    attacks.sort(key=lambda a: a.get("div", 0))
    if not attacks:
        return [(0.0, 0.0), (1.0, 1.0)]
    divs = max(1, int(info.get("divs") or 1))

    notes_only = [a for a in attacks if not a.get("rest")]
    span = float(bar_right - bar_left) if (bar_left is not None and bar_right is not None and bar_right > bar_left) else 0.0

    # MIDI와 XML 매칭을 위한 준비
    midis = []
    if midi_on and meas_dur > 1e-6:
        lo, hi = meas_start - 0.02, meas_start + meas_dur - 0.015
        midis = [t for t in midi_on if lo <= t < hi]

    timed_visuals = []
    used_m = set()
    used_pdf = set()
    max_pair_dt = 0.12

    for a in attacks:
        xml_t_frac = min(max(a["div"] / divs, 0.0), 1.0)
        t_xml = meas_start + xml_t_frac * meas_dur

        # 가로 좌표 (X) 결정
        if not a.get("rest") and pdf_xs and span > 0:
            if len(pdf_xs) == len(notes_only):
                note_idx = notes_only.index(a) if a in notes_only else 0
                x_frac = (pdf_xs[note_idx] - bar_left) / span
            else:
                expected_x = bar_left + _x_frac_of(a, info) * span
                cands = [(abs(px - expected_x), idx, px) for idx, px in enumerate(pdf_xs) if idx not in used_pdf]
                if cands:
                    cands.sort()
                    best_dt, best_idx, best_px = cands[0]
                    if best_dt < span * 0.4:
                        used_pdf.add(best_idx)
                        x_frac = (best_px - bar_left) / span
                    else:
                        x_frac = _x_frac_of(a, info)
                else:
                    x_frac = _x_frac_of(a, info)
        else:
            x_frac = _x_frac_of(a, info)
        x_frac = min(max(x_frac, 0.0), 1.0)

        # 시간 좌표 (T) 결정
        t_frac = xml_t_frac
        if not a.get("rest") and midis:
            cand = [(abs(t - t_xml), idx, t) for idx, t in enumerate(midis) if idx not in used_m]
            if cand:
                cand.sort()
                dt, idx, t = cand[0]
                if dt <= max_pair_dt:
                    used_m.add(idx)
                    t_frac = min(max((t - meas_start) / meas_dur, 0.0), 0.999)

        timed_visuals.append((t_frac, x_frac))

    timed_visuals.sort(key=lambda p: (p[0], p[1]))

    pts: List[Tuple[float, float]] = [(0.0, 0.0)]
    for tf, xf in timed_visuals:
        if pts:
            xf = max(xf, pts[-1][1])
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


def attach_measure_anchors(
    timeline: ScoreTimeline,
    layout: Optional[ScoreLayout],
    musicxml_path: Optional[str],
    log_callback=None,
    midi_path: Optional[str] = None,
    stitched_img: Optional[Any] = None,
    pdf_path: Optional[str] = None,
) -> None:
    """마디 앵커: 박자는 악보 기보 길이 + MIDI 보정, 가로는 PDF 음머리 + XML 보정."""
    midi_on = load_midi_onsets(midi_path)
    parsed = parse_lead_attacks(musicxml_path) if musicxml_path else {}
    pdf_map: Dict[int, List[int]] = {}
    if layout and layout.systems and (stitched_img is not None or pdf_path is not None):
        from engine.pdf_notes import collect_measure_note_xs

        gray = stitched_img if stitched_img is not None else np.zeros((10, 10), dtype=np.uint8)
        pdf_map = collect_measure_note_xs(gray, layout, pdf_path=pdf_path)

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
            if heads:
                pdf_used += 1
            meas.anchors = _anchors_from_score(
                info, heads, left, right,
                meas_start=meas.start_sec,
                meas_dur=meas.duration_sec,
                midi_on=midi_on
            )
            used += 1
        else:
            meas.anchors = [(0.0, 0.0), (1.0, 1.0)]
    if log_callback:
        log_callback(
            f"[음표 앵커] 악보 기보 박자(+MIDI 연동) {used}/{timeline.n_measures}마디"
            f", PDF 음머리 좌표 {pdf_used}마디"
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
