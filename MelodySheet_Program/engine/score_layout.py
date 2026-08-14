"""PDF 악보에서 단(system) · 오선 · 마디 세로줄을 읽는다.

MusicXML에는 new-system/new-page가 없는 경우가 많아
시각 레이아웃의 진실은 렌더된 PDF 픽셀이다.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import numpy as np
import pymupdf as fitz


@dataclass
class StaffBand:
    y0: int
    y1: int


@dataclass
class SystemLayout:
    index: int
    page_index: int
    y0: int
    y1: int
    x_left: int
    x_right: int
    start_measure: int
    end_measure: int
    bar_xs: List[int] = field(default_factory=list)
    staves: List[StaffBand] = field(default_factory=list)
    bars_from_detect: bool = True

    @property
    def n_measures(self) -> int:
        return max(0, self.end_measure - self.start_measure + 1)

    def contains_measure(self, number: int) -> bool:
        return self.start_measure <= number <= self.end_measure

    def measure_x_range(self, number: int) -> Tuple[int, int]:
        local = number - self.start_measure
        if self.bar_xs and len(self.bar_xs) >= self.n_measures + 1:
            i = min(max(local, 0), len(self.bar_xs) - 2)
            return int(self.bar_xs[i]), int(self.bar_xs[i + 1])
        n = max(self.n_measures, 1)
        span = max(1, self.x_right - self.x_left)
        left = self.x_left + int(span * local / n)
        right = self.x_left + int(span * (local + 1) / n)
        return left, right


@dataclass
class ScoreLayout:
    systems: List[SystemLayout] = field(default_factory=list)
    img_width: int = 0
    img_height: int = 0
    dpi: int = 200
    page_y_positions: List[int] = field(default_factory=list)

    def system_for_measure(self, number: int) -> Optional[SystemLayout]:
        for sys in self.systems:
            if sys.contains_measure(number):
                return sys
        if not self.systems:
            return None
        if number < self.systems[0].start_measure:
            return self.systems[0]
        return self.systems[-1]

    def scaled(self, factor: float) -> "ScoreLayout":
        if abs(factor - 1.0) < 1e-9:
            return self

        def s(v: int) -> int:
            return int(round(v * factor))

        systems = []
        for sys in self.systems:
            systems.append(
                SystemLayout(
                    index=sys.index,
                    page_index=sys.page_index,
                    y0=s(sys.y0),
                    y1=s(sys.y1),
                    x_left=s(sys.x_left),
                    x_right=s(sys.x_right),
                    start_measure=sys.start_measure,
                    end_measure=sys.end_measure,
                    bar_xs=[s(x) for x in sys.bar_xs],
                    staves=[StaffBand(s(st.y0), s(st.y1)) for st in sys.staves],
                    bars_from_detect=sys.bars_from_detect,
                )
            )
        return ScoreLayout(
            systems=systems,
            img_width=s(self.img_width),
            img_height=s(self.img_height),
            dpi=self.dpi,
            page_y_positions=[s(y) for y in self.page_y_positions],
        )


def _page_index_of_y(y: int, page_y_positions: Sequence[int]) -> int:
    if not page_y_positions:
        return 0
    for i in range(len(page_y_positions) - 1):
        if page_y_positions[i] <= y < page_y_positions[i + 1]:
            return i
    return max(0, len(page_y_positions) - 2)


def _runs_from_mask(active: np.ndarray, merge_gap: int) -> List[Tuple[int, int]]:
    regions: List[Tuple[int, int]] = []
    in_run = False
    start = 0
    last_active = -10**9
    for y, on in enumerate(active):
        if on:
            if not in_run:
                if regions and y - last_active <= merge_gap:
                    start = regions.pop()[0]
                else:
                    start = y
                in_run = True
            last_active = y
        elif in_run and (y - last_active) > merge_gap:
            regions.append((start, last_active + 1))
            in_run = False
    if in_run:
        regions.append((start, last_active + 1))
    return regions


def _detect_page_systems(gray_page: np.ndarray, dpi: int, page_index: int) -> List[Tuple[int, int]]:
    """한 페이지에서 앙상블 단(여러 오선 묶음)의 y 범위를 찾는다."""
    h, w = gray_page.shape
    header = int(dpi * (1.08 if page_index == 0 else 0.28))
    footer = int(dpi * 0.78)
    y_lo = min(header, h // 5)
    y_hi = max(y_lo + 1, h - footer)
    band = gray_page[y_lo:y_hi]
    if band.size == 0:
        return []

    x0, x1 = int(w * 0.12), int(w * 0.96)
    ink = band[:, x0:x1] < 160
    row = ink.mean(axis=1).astype(np.float64)
    k = max(5, int(dpi * 0.04))
    smooth = np.convolve(row, np.ones(k) / k, mode="same")
    thr = max(0.010, float(np.median(smooth) + 0.70 * np.std(smooth)))
    if thr > 0.055:
        thr = 0.018
    active = smooth > thr

    merge_gap = int(dpi * 0.70)  # 악기 사이는 합치고, 단 사이 큰 여백만 가른다
    regions = _runs_from_mask(active, merge_gap)
    regions = [(a + y_lo, b + y_lo) for a, b in regions]

    min_h = int(dpi * 1.70)  # 5줄 앙상블 단은 이보다 훨씬 크다
    regions = [(a, b) for a, b in regions if (b - a) >= min_h]

    # 잘린 작은 조각이 남으면 가장 가까운 이웃에 붙인다
    if len(regions) >= 3:
        heights = [b - a for a, b in regions]
        med_h = float(np.median(heights))
        kept: List[Tuple[int, int]] = []
        for a, b in regions:
            if kept and (b - a) < med_h * 0.55:
                pa, _pb = kept[-1]
                kept[-1] = (pa, b)
            else:
                kept.append((a, b))
        regions = kept

    # 페이지에 단이 하나뿐인데 세로로 길면, 가운데 가장 큰 여백에서 둘로 가른다
    page_body = y_hi - y_lo
    if len(regions) == 1 and (regions[0][1] - regions[0][0]) > page_body * 0.72:
        a, b = regions[0]
        local = smooth[a - y_lo : b - y_lo]
        mid0, mid1 = int(len(local) * 0.35), int(len(local) * 0.65)
        if mid1 > mid0:
            split = mid0 + int(np.argmin(local[mid0:mid1]))
            regions = [(a, a + split), (a + split, b)]
            regions = [(ra, rb) for ra, rb in regions if (rb - ra) >= min_h]

    return regions


def _piano_staves_from_system(y0: int, y1: int, dpi: int = 200) -> List[StaffBand]:
    """단 상단의 피아노 대보표.

    푸터가 섞여 단이 길어지면 비율 창이 아래로 밀리므로,
    5줄 앙상블 높이(~4.2in)로 잘라 그 안의 8~40%만 본다.
    """
    h = min(max(1, y1 - y0), int(dpi * 4.20))
    p0 = y0 + int(h * 0.08)
    p1 = y0 + int(h * 0.40)
    if p1 - p0 < int(dpi * 0.7):
        p1 = min(y1 - 2, p0 + int(dpi * 1.2))
    mid = (p0 + p1) // 2
    return [StaffBand(p0, mid), StaffBand(mid, p1)]


def _detect_barlines(gray: np.ndarray, staves: Sequence[StaffBand], img_w: int) -> List[int]:
    if not staves:
        return []
    # 피아노 대보표(위 두 오선)를 관통하는지 본다. 음표 줄기는 한 오선만 지난다.
    if len(staves) >= 2:
        y0 = staves[0].y0
        y1 = staves[1].y1
    else:
        y0, y1 = staves[0].y0, staves[0].y1
    y0 = max(0, y0)
    y1 = min(gray.shape[0], y1)
    if y1 - y0 < 8:
        return []

    band = gray[y0:y1, :]
    ink = band < 135
    bh, bw = ink.shape
    min_run = int(bh * 0.72)

    cands: List[int] = []
    for x in range(bw):
        col = ink[:, x]
        longest = 0
        cur = 0
        for v in col:
            if v:
                cur += 1
                if cur > longest:
                    longest = cur
            else:
                cur = 0
        if longest >= min_run and float(col.mean()) > 0.28:
            cands.append(x)

    if not cands:
        return []

    clusters: List[List[int]] = [[cands[0]]]
    for x in cands[1:]:
        if x - clusters[-1][-1] <= 4:
            clusters[-1].append(x)
        else:
            clusters.append([x])

    bars = [int(np.median(cl)) for cl in clusters]
    left_cut = int(img_w * 0.03)
    bars = [x for x in bars if x >= left_cut]

    merged: List[int] = []
    for x in bars:
        if not merged or x - merged[-1] > 10:
            merged.append(x)
        else:
            merged[-1] = (merged[-1] + x) // 2
    return merged


def _extract_measure_numbers(
    pdf_path: str, page_y_positions: Sequence[int], dpi: int
) -> List[Tuple[int, int, int]]:
    """(stitched_y, measure_number, page_index) 목록. 왼쪽 작은 마디 번호만."""
    out: List[Tuple[int, int, int]] = []
    if not os.path.isfile(pdf_path):
        return out
    scale = dpi / 72.0
    doc = fitz.open(pdf_path)
    try:
        for pi, page in enumerate(doc):
            page_top = page_y_positions[pi] if pi < len(page_y_positions) else 0
            for w in page.get_text("words"):
                text = (w[4] or "").strip()
                if not text.isdigit():
                    continue
                x0, y0, x1, y1 = w[0], w[1], w[2], w[3]
                if x0 > 32:
                    continue
                size = y1 - y0
                if size < 7.0 or size > 10.5:
                    continue
                if y0 < 50:
                    continue
                n = int(text)
                if n < 1 or n > 400:
                    continue
                img_y = int(page_top + y0 * scale)
                out.append((img_y, n, pi))
    finally:
        doc.close()
    out.sort(key=lambda t: (t[2], t[0]))
    return out


def _assign_measures(
    systems: List[SystemLayout], numbers: Sequence[Tuple[int, int, int]], total_measures: int
) -> None:
    # 각 단에 가장 가까운 왼쪽 마디 번호를 붙인다.
    assigned = [None] * len(systems)
    used = set()
    for img_y, n, _pi in numbers:
        best = None
        best_dist = 10**9
        for i, sys in enumerate(systems):
            if i in used:
                continue
            if img_y < sys.y0 - 40 or img_y > sys.y1:
                continue
            dist = abs(img_y - sys.y0)
            if dist < best_dist:
                best_dist = dist
                best = i
        if best is not None:
            assigned[best] = n
            used.add(best)

    starts: List[int] = []
    next_guess = 1
    for i, n in enumerate(assigned):
        if n is None:
            n = next_guess
        starts.append(int(n))
        next_guess = int(n) + 1

    # 단조 증가로 보정
    for i in range(1, len(starts)):
        if starts[i] <= starts[i - 1]:
            starts[i] = starts[i - 1] + 1

    for i, sys in enumerate(systems):
        sys.start_measure = starts[i]
        if i + 1 < len(starts):
            sys.end_measure = max(sys.start_measure, starts[i + 1] - 1)
        else:
            last = total_measures if total_measures else sys.start_measure
            sys.end_measure = max(sys.start_measure, last)


def _first_music_x(gray: np.ndarray, y0: int, y1: int, x_from: int, x_to: int) -> int:
    """오선을 제외한 음표/쉼표 잉크가 처음 나타나는 x."""
    x_from = max(0, x_from)
    x_to = min(gray.shape[1], x_to)
    y0 = max(0, y0)
    y1 = min(gray.shape[0], y1)
    if x_to - x_from < 10 or y1 - y0 < 8:
        return x_from
    band = gray[y0:y1, x_from:x_to]
    ink = band < 125
    row_frac = ink.mean(axis=1)
    mask = ink.copy()
    mask[row_frac > 0.38] = False
    col = mask.mean(axis=0)
    win = 6
    for x in range(0, max(1, len(col) - win)):
        if float(col[x : x + win].mean()) > 0.022:
            return x_from + x
    return x_from


def _tighten_system_y(gray: np.ndarray, y0: int, y1: int) -> Tuple[int, int]:
    h, w = gray.shape[:2]
    y0 = max(0, y0)
    y1 = min(h, y1)
    x0, x1 = int(w * 0.16), int(w * 0.95)
    band = gray[y0:y1, x0:x1]
    if band.size == 0:
        return y0, y1
    row = (band < 160).mean(axis=1)
    thr = max(0.018, float(np.median(row) * 0.9))
    ys = np.where(row > thr)[0]
    if len(ys) < 12:
        return y0, y1
    pad = max(8, int((ys[-1] - ys[0]) * 0.03))
    return y0 + int(ys[0]), min(y1, y0 + int(ys[-1]) + pad)


def _shift_first_bar(sys: SystemLayout, bars: List[int], img_w: int, gray: np.ndarray) -> List[int]:
    """단의 첫 마디 왼쪽을 음자리표 뒤의 실제 기보로 옮긴다."""
    if len(bars) < 2:
        return bars
    piano = sys.staves[:2] if sys.staves else []
    if piano:
        py0, py1 = piano[0].y0, piano[-1].y1
    else:
        py0, py1 = sys.y0 + 8, sys.y0 + max(20, (sys.y1 - sys.y0) // 3)
    if sys.start_measure == 1:
        scan_from = max(bars[0] + int(img_w * 0.04), int(img_w * 0.24))
    else:
        scan_from = max(bars[0] + int(img_w * 0.04), int(img_w * 0.10))
    scan_from = min(scan_from, bars[1] - 12)
    if scan_from <= bars[0] + 4:
        return bars
    music_x = _first_music_x(gray, py0, py1, scan_from, bars[1])
    bars = list(bars)
    if scan_from <= music_x < bars[1] - 8:
        bars[0] = music_x
    else:
        bars[0] = scan_from
    return bars


def _fill_bar_xs(sys: SystemLayout, detected: Sequence[int], img_w: int, gray: np.ndarray) -> None:
    n = sys.n_measures
    right_default = int(img_w * 0.97)
    left_default = sys.x_left

    bars = list(detected)
    chosen: List[int] = []
    if n <= 0:
        sys.bar_xs = [left_default, right_default]
        sys.x_right = right_default
        sys.bars_from_detect = False
        return

    detected_ok = False
    if len(bars) >= 2 and bars[-1] > img_w * 0.80:
        if len(bars) == n + 1:
            chosen = bars
            detected_ok = True
        elif len(bars) == n + 2:
            chosen = bars[1:]
            detected_ok = True
        elif len(bars) == n:
            chosen = [left_default] + bars
            detected_ok = True

    if len(chosen) < n + 1:
        left = left_default
        right = bars[-1] if bars and bars[-1] > img_w * 0.8 else right_default
        chosen = [int(left + (right - left) * i / n) for i in range(n + 1)]
        detected_ok = False

    chosen = _shift_first_bar(sys, chosen, img_w, gray)
    sys.bar_xs = chosen
    sys.x_left = chosen[0]
    sys.x_right = chosen[-1]
    sys.bars_from_detect = detected_ok


def analyze_score_layout(
    pdf_path: str,
    stitched_img: np.ndarray,
    page_y_positions: Sequence[int],
    dpi: int = 200,
    total_measures: int = 0,
    log_callback=None,
) -> ScoreLayout:
    def _log(msg: str) -> None:
        if log_callback:
            log_callback(msg)

    if stitched_img.ndim == 3:
        gray = stitched_img.mean(axis=2).astype(np.uint8)
    else:
        gray = stitched_img
    h, w = gray.shape[:2]

    systems: List[SystemLayout] = []
    n_pages = max(1, len(page_y_positions) - 1)
    for pi in range(n_pages):
        top = int(page_y_positions[pi])
        bot = int(page_y_positions[pi + 1]) if pi + 1 < len(page_y_positions) else h
        bot = min(bot, h)
        if bot <= top:
            continue
        page_gray = gray[top:bot]
        for a, b in _detect_page_systems(page_gray, dpi, pi):
            y0, y1 = _tighten_system_y(gray, top + a, top + b)
            chord_pad = max(10, int((y1 - y0) * 0.04))
            y0 = max(top, y0 - chord_pad)
            footer_cut = int(dpi * 1.05)
            y1 = min(y1, bot - footer_cut)
            if y1 <= y0 + int(dpi * 1.4):
                y1 = min(bot - int(dpi * 0.35), y0 + int((bot - top) * 0.48))
            gi = len(systems)
            systems.append(
                SystemLayout(
                    index=gi,
                    page_index=pi,
                    y0=y0,
                    y1=y1,
                    x_left=int(w * (0.20 if gi == 0 else 0.07)),
                    x_right=int(w * 0.97),
                    start_measure=1,
                    end_measure=1,
                    staves=_piano_staves_from_system(y0, y1, dpi),
                )
            )
    _log(f"[레이아웃] 페이지 {n_pages}장에서 단(system) {len(systems)}개 검출")

    numbers = _extract_measure_numbers(pdf_path, page_y_positions, dpi)
    _log(f"[레이아웃] PDF 마디 번호 {len(numbers)}개: {[n for _y, n, _p in numbers]}")
    _assign_measures(systems, numbers, total_measures)

    for sys in systems:
        bars = _detect_barlines(gray, sys.staves, w)
        _fill_bar_xs(sys, bars, w, gray)

    covered = sum(s.n_measures for s in systems)
    _log(
        f"[레이아웃] 단 {len(systems)}개 / 배당 마디 {covered}"
        + (f" (기대 {total_measures})" if total_measures else "")
    )
    for sys in systems:
        _log(
            f"  - P{sys.page_index + 1} 단{sys.index + 1}: "
            f"m{sys.start_measure}-{sys.end_measure} ({sys.n_measures}마디) "
            f"y={sys.y0}-{sys.y1} bars={len(sys.bar_xs)}"
        )

    return ScoreLayout(
        systems=systems,
        img_width=w,
        img_height=h,
        dpi=dpi,
        page_y_positions=list(page_y_positions),
    )
