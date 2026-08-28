import os
import sys
import cv2
import numpy as np

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from engine.sheet_processor import convert_pdf_to_multi_page_image
from engine.score_layout import _detect_page_systems

pdf_path = r"c:\Users\DiCiA\PycharmProjects\음원+악보병합 프로젝트\MelodySheet_Program\MelodySheet_Program\InputData\2-Watercolor Bus Stop\Watercolor Bus Stop.pdf"
dpi = 200

sheet_img, page_y_positions = convert_pdf_to_multi_page_image(pdf_path, dpi=dpi)
cv_img = np.array(sheet_img)
gray = cv2.cvtColor(cv_img, cv2.COLOR_RGB2GRAY)
if not page_y_positions:
    page_y_positions = [0, gray.shape[0]]

y0 = page_y_positions[0]
y1 = page_y_positions[1]
page_gray = gray[y0:y1]

systems = _detect_page_systems(page_gray, dpi, 0)
for sys_idx, (sy0, sy1) in enumerate(systems):
    sys_img = page_gray[sy0:sy1]
    
    ink = sys_img < 160
    row_sum = ink.sum(axis=1)
    w = sys_img.shape[1]
    staff_line_rows = np.where(row_sum > w * 0.25)[0]
    
    if len(staff_line_rows) > 0:
        true_y0 = sy0 + staff_line_rows[0]
        true_y1 = sy0 + staff_line_rows[-1]
        
        # margin
        margin = int(dpi * 0.02)
        true_y0 = max(sy0, true_y0 - margin)
        true_y1 = min(sy1, true_y1 + margin)
    else:
        true_y0 = sy0
        true_y1 = sy1
        
    print(f"System {sys_idx}: Original y0={sy0}, y1={sy1} (h={sy1-sy0})")
    print(f"          Refined  y0={true_y0}, y1={true_y1} (h={true_y1-true_y0})")

