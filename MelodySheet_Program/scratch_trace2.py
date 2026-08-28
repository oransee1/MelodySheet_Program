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
            print(f"Region {a}-{b} is tall ({b-a} > {max_sys_h})")
            local_active = active[a : b]
            local_runs = _runs_from_mask(local_active, int(dpi * 0.15))
            
            # Use ONLY the fallback logic
            local_gaps = []
            for j in range(len(local_runs) - 1):
                gap_size = local_runs[j+1][0] - local_runs[j][1]
                local_gaps.append((gap_size, j))
            
            N = max(2, int(round((b - a) / (dpi * 2.0))))
            num_splits = min(N - 1, len(local_gaps))
            print(f"  N={N}, num_splits={num_splits}, local_runs={local_runs}, local_gaps={local_gaps}")
            if num_splits > 0:
                local_gaps.sort(reverse=True, key=lambda x: x[0])
                split_indices = [g[1] for g in local_gaps[:num_splits]]
                split_indices.sort()
                
                start_run_idx = 0
                for split_idx in split_indices:
                    sys_a = a + local_runs[start_run_idx][0]
                    sys_b = a + local_runs[split_idx][1]
                    split_regions.append((sys_a, sys_b))
                    print(f"    Added {(sys_a, sys_b)} (height {sys_b - sys_a})")
                    start_run_idx = split_idx + 1
                sys_a = a + local_runs[start_run_idx][0]
                sys_b = a + local_runs[-1][1]
                split_regions.append((sys_a, sys_b))
                print(f"    Added {(sys_a, sys_b)} (height {sys_b - sys_a})")
            else:
                split_regions.append((a, b))
        else:
            split_regions.append((a, b))

    print("Split regions:", split_regions)
