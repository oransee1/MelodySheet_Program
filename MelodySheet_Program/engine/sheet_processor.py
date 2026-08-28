import os
import sys

if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
    for p in sys.path:
        for qt_dir in ["PyQt5/Qt5/bin", "PyQt6/Qt6/bin"]:
            full_qt_path = os.path.join(p, *qt_dir.split("/"))
            if os.path.isdir(full_qt_path):
                try:
                    os.add_dll_directory(full_qt_path)
                except Exception:
                    pass

import pymupdf  # PyMuPDF
from PIL import Image
import io

def convert_pdf_to_image(pdf_path: str, page_num: int = 0, dpi: int = 300) -> Image.Image:
    """PDF 악보의 특정 페이지를 지정한 DPI의 PIL Image로 변환합니다."""
    doc = pymupdf.open(pdf_path)
    if page_num >= len(doc):
        page_num = 0
    page = doc.load_page(page_num)
    zoom = dpi / 72
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_data = pix.tobytes("png")
    doc.close()
    return Image.open(io.BytesIO(img_data)).convert("RGB")

def convert_pdf_to_multi_page_image(pdf_path: str, dpi: int = 200):
    """
    PDF 악보 전체 페이지(1~N페이지)를 렌더링하여
    하나의 긴 세로 악보 캔버스 이미지(Continuous Sheet Canvas)로 합치고 각 페이지 Y 위치를 반환합니다.
    """
    doc = pymupdf.open(pdf_path)
    images = []
    total_height = 0
    max_width = 0
    
    zoom = dpi / 72
    mat = pymupdf.Matrix(zoom, zoom)
    
    for page in doc:
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        images.append(img)
        total_height += img.height
        if img.width > max_width:
            max_width = img.width
            
    doc.close()
    
    # 세로로 긴 캔버스 생성 및 이미지 붙이기
    combined_img = Image.new("RGB", (max_width, total_height), (255, 255, 255))
    current_y = 0
    page_y_positions = [0]
    for img in images:
        combined_img.paste(img, (0, current_y))
        current_y += img.height
        page_y_positions.append(current_y)
        
    return combined_img, page_y_positions
