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

y0 = page_y_positions[0]
y1 = page_y_positions[1]
page_gray = gray[y0:y1]
h, w = page_gray.shape

header = int(dpi * 1.08)
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

# Extract staves with a very small merge gap
merge_gap_staves = int(dpi * 0.05) # 10 pixels
runs = _runs_from_mask(active, merge_gap_staves)

print(f"All runs (gap={merge_gap_staves}):")
for r in runs:
    print(f"  {r}, height={r[1]-r[0]}")

# Filter for staves
min_staff_h = int(dpi * 0.12) # 24 pixels
max_staff_h = int(dpi * 0.60) # 120 pixels
staves = [r for r in runs if min_staff_h <= (r[1] - r[0]) <= max_staff_h]

print(f"\nFiltered staves ({min_staff_h} to {max_staff_h}):")
for r in staves:
    print(f"  {r}, height={r[1]-r[0]}")

