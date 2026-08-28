import os
import cv2
import numpy as np
from engine.pdf_stitcher import convert_pdf_to_multi_page_image
from engine.score_layout import ScoreLayout, _detect_page_systems

pdf_path = r"c:\Users\DiCiA\PycharmProjects\음원+악보병합 프로젝트\MelodySheet_Program\MelodySheet_Program\InputData\2026-08-17\Input01\Lazy Saturday Suns.pdf"
dpi = 200

sheet_img, page_y_positions = convert_pdf_to_multi_page_image(pdf_path, dpi=dpi)

gray = cv2.cvtColor(sheet_img, cv2.COLOR_BGR2GRAY)
regions_all = []
if not page_y_positions:
    page_y_positions = [0, gray.shape[0]]

print(f"Page Y positions: {page_y_positions}")

for i in range(len(page_y_positions) - 1):
    y0 = page_y_positions[i]
    y1 = page_y_positions[i + 1]
    page_gray = gray[y0:y1]
    
    print(f"\n--- Page {i+1} ---")
    print(f"y0: {y0}, y1: {y1}, height: {y1 - y0}")
    
    sys_regions = _detect_page_systems(page_gray, dpi, i)
    print(f"Detected {len(sys_regions)} systems:")
    for j, (r_a, r_b) in enumerate(sys_regions):
        print(f"  Sys {j}: local({r_a}, {r_b}) -> global({y0 + r_a}, {y0 + r_b}), height={r_b - r_a}")

