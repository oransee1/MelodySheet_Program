"""PDF 악보에서 음머리 X와 페이지 템포 표기를 읽는다."""
from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

import numpy as np

from engine.score_layout import ScoreLayout



def detect_note_xs(gray: np.ndarray, x0: int, x1: int, y0: int, y1: int) -> List[int]:
    """한 마디 창에서 음머리 후보 X (오선·줄기 제거 후 덩어리)."""
    try:
        import cv2
    except ImportError:
        return []
    x0, x1 = max(0, x0), min(gray.shape[1], x1)
    y0, y1 = max(0, y0), min(gray.shape[0], y1)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return []
    band = gray[y0:y1, x0:x1]
    _, bw = cv2.threshold(band, 145, 255, cv2.THRESH_BINARY_INV)
    hk = cv2.getStructuringElement(cv2.MORPH_RECT, (max(24, band.shape[1] // 10), 1))
    staff = cv2.morphologyEx(bw, cv2.MORPH_OPEN, hk)
    notes = cv2.subtract(bw, staff)
    vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(14, band.shape[0] // 5)))
    stems = cv2.morphologyEx(notes, cv2.MORPH_OPEN, vk)
    heads = cv2.subtract(notes, stems)
    heads = cv2.morphologyEx(heads, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    _n, _lab, stats, cents = cv2.connectedComponentsWithStats(heads, 8)
    xs = []
    for i in range(1, _n):
        x, y, w, h, area = stats[i]
        if area < 14 or area > 500:
            continue
        if w < 4 or h < 4 or w > 36 or h > 36:
            continue
        asp = w / max(h, 1.0)
        if asp > 2.8 or asp < 0.35:
            continue
        xs.append(x0 + int(round(cents[i][0])))
    xs.sort()
    merged: List[int] = []
    for x in xs:
        if not merged or x - merged[-1] > 10:
            merged.append(x)
        else:
            merged[-1] = (merged[-1] + x) // 2
    return merged


def collect_measure_note_xs(
    gray: np.ndarray,
    layout: ScoreLayout,
    pdf_path: Optional[str] = None,
) -> Dict[int, List[int]]:
    """마디 번호 → PDF 음머리 X 목록 (PyMuPDF 벡터 글리프 우선 + CV 형태학 보조)."""
    out: Dict[int, List[int]] = {}

    # 1. PyMuPDF 벡터 폰트(Emmentaler 등) 글리프에서 정확한 음표 X 좌표 추출
    if pdf_path and os.path.isfile(pdf_path):
        try:
            import json
            import pymupdf
            doc = pymupdf.open(pdf_path)
            scale = layout.dpi / 72.0
            glyph_map: Dict[int, List[Tuple[float, float]]] = {}
            for pi, page in enumerate(doc):
                page_top = layout.page_y_positions[pi] if pi < len(layout.page_y_positions) else 0
                data = json.loads(page.get_text("rawjson"))
                for b in data.get("blocks", []):
                    for l in b.get("lines", []):
                        for s in l.get("spans", []):
                            if "Emmentaler" in s.get("font", ""):
                                for c in s.get("chars", []):
                                    bbox = [x * scale for x in c["bbox"]]
                                    cx = (bbox[0] + bbox[2]) / 2.0
                                    cy = page_top + (bbox[1] + bbox[3]) / 2.0
                                    glyph_map.setdefault(pi, []).append((cx, cy))
            doc.close()

            for sys in layout.systems:
                pi = sys.page_index
                p_glyphs = glyph_map.get(pi, [])
                ty0 = sys.staves[0].y0 if sys.staves else sys.y0
                ty1 = sys.staves[-1].y1 if sys.staves else sys.y1
                for num in range(sys.start_measure, sys.end_measure + 1):
                    left, right = sys.measure_x_range(num)
                    m_glyphs = [cx for cx, cy in p_glyphs if left <= cx < right and ty0 - 15 <= cy <= ty1 + 15]
                    if m_glyphs:
                        xs = sorted(list(set(int(round(x)) for x in m_glyphs)))
                        merged = []
                        for x in xs:
                            if not merged or x - merged[-1] > 8:
                                merged.append(x)
                            else:
                                merged[-1] = (merged[-1] + x) // 2
                        out[num] = merged
                    else:
                        out[num] = []
        except Exception:
            pass

    if gray.ndim == 3:
        gray = gray.mean(axis=2).astype(np.uint8)
    for sys in layout.systems:
        if sys.staves:
            y0, y1 = sys.staves[0].y0, sys.staves[-1].y1
        else:
            h = max(1, sys.y1 - sys.y0)
            y0, y1 = sys.y0 + int(h * 0.08), sys.y0 + int(h * 0.40)
        for num in range(sys.start_measure, sys.end_measure + 1):
            if num not in out or not out[num]:
                left, right = sys.measure_x_range(num)
                cv_notes = detect_note_xs(gray, left, right, y0 - 8, y1 + 8)
                if cv_notes:
                    out[num] = cv_notes
    return out



def extract_pdf_tempos(pdf_path: str) -> List[Tuple[int, int, float]]:
    """페이지에서 '= 115' 형태 메트로놈. (page_index, bpm, pdf_y)."""
    import os
    import pymupdf

    found: List[Tuple[int, int, float]] = []
    if not os.path.isfile(pdf_path):
        return found
    doc = pymupdf.open(pdf_path)
    try:
        for pi, page in enumerate(doc):
            words = page.get_text("words")
            for i, w in enumerate(words):
                if (w[4] or "").strip() != "=":
                    continue
                if i + 1 >= len(words):
                    continue
                nxt = (words[i + 1][4] or "").strip()
                if nxt.isdigit() and 20 <= int(nxt) <= 300:
                    found.append((pi, int(nxt), float(w[1])))
    finally:
        doc.close()
    return found
