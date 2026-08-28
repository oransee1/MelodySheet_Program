import os
import sys
import cv2
import numpy as np

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from engine.sheet_processor import convert_pdf_to_multi_page_image
from engine.score_layout import _runs_from_mask

pdf_path = r"c:\Users\DiCiA\PycharmProjects\음원+악보병합 프로젝트\MelodySheet_Program\MelodySheet_Program\InputData\2026-08-17\Input01\Lazy Saturday Suns.pdf"
dpi = 200

sheet_img, page_y_positions = convert_pdf_to_multi_page_image(pdf_path, dpi=dpi)
cv_img = np.array(sheet_img)
gray = cv2.cvtColor(cv_img, cv2.COLOR_RGB2GRAY)
if not page_y_positions:
    page_y_positions = [0, gray.shape[0]]

def recursive_split_runs(a, b, active_array, merge_gap_for_runs, max_sys_h):
    if b - a <= max_sys_h:
        return [(a, b)]
        
    local_active = active_array[a:b]
    runs = _runs_from_mask(local_active, merge_gap_for_runs)
    
    if len(runs) < 2:
        return [(a, b)]
        
    max_gap_size = -1
    max_gap_idx = -1
    for j in range(len(runs) - 1):
        gap = runs[j+1][0] - runs[j][1]
        if gap > max_gap_size:
            max_gap_size = gap
            max_gap_idx = j
            
    if max_gap_idx == -1:
        return [(a, b)]
        
    split_a = a + runs[0][0]
    split_b = a + runs[max_gap_idx][1]
    
    split_c = a + runs[max_gap_idx+1][0]
    split_d = a + runs[-1][1]
    
    return recursive_split_runs(split_a, split_b, active_array, merge_gap_for_runs, max_sys_h) + \
           recursive_split_runs(split_c, split_d, active_array, merge_gap_for_runs, max_sys_h)

for i in range(len(page_y_positions) - 1):
    y0 = page_y_positions[i]
    y1 = page_y_positions[i + 1]
    page_gray = gray[y0:y1]
    h, w = page_gray.shape

    header = int(dpi * 1.08) if i == 0 else int(dpi * 0.28)
    footer = int(dpi * 0.78)
    y_lo = min(header, h // 5)
    y_hi = max(y_lo + 1, h - footer)
    band = page_gray[y_lo:y_hi]
    x0, x1 = int(w * 0.12), int(w * 0.96)
    ink = band[:, x0:x1] < 160
    row = ink.mean(axis=1).astype(np.float64)
    k = max(5, int(dpi * 0.04))
    smooth = np.convolve(row, np.ones(k) / k, mode="same")
    thr = max(0.010, float(np.median(smooth) + 0.70 * np.std(smooth)))
    if thr > 0.055: thr = 0.018
    active = smooth > thr

    merge_gap = int(dpi * 0.45)
    regions = _runs_from_mask(active, merge_gap)
    print(f"\n--- Page {i+1} ---")
    print("Initial regions:", regions)

    max_sys_h = int(dpi * 2.4)
    split_regions = []
    for a, b in regions:
        if b - a > max_sys_h:
            pieces = recursive_split_runs(a, b, active, int(dpi * 0.15), max_sys_h)
            split_regions.extend(pieces)
        else:
            split_regions.append((a, b))
            
    print("Split regions:", split_regions)

    min_h = int(dpi * 0.80)
    filtered = [(a, b) for a, b in split_regions if (b - a) >= min_h]
    print("Filtered:", filtered)
