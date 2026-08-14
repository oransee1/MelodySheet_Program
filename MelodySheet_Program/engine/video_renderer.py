import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
from moviepy import VideoClip, AudioFileClip, concatenate_videoclips
from engine.sheet_processor import convert_pdf_to_multi_page_image
from engine.sync_manager import SyncManager

def create_text_image(width: int, height: int, title: str, subtitle: str, bg_color=(20, 20, 25), text_color=(255, 255, 255)) -> Image.Image:
    """인트로 / 아웃트로용 텍스트 이미지 생성"""
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 64)
        sub_font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    t_bbox = draw.textbbox((0, 0), title, font=title_font)
    t_w = t_bbox[2] - t_bbox[0]
    t_h = t_bbox[3] - t_bbox[1]
    
    s_bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
    s_w = s_bbox[2] - s_bbox[0]
    s_h = s_bbox[3] - s_bbox[1]
    
    total_h = t_h + s_h + 30
    start_y = (height - total_h) // 2
    
    draw.text(((width - t_w) // 2, start_y), title, fill=text_color, font=title_font)
    draw.text(((width - s_w) // 2, start_y + t_h + 30), subtitle, fill=(180, 180, 200), font=sub_font)
    
    line_y = start_y + t_h + 15
    draw.line([((width - 300) // 2, line_y), ((width + 300) // 2, line_y)], fill=(100, 140, 245), width=3)
    
    return img

class VideoRenderer:
    def __init__(self, pdf_path: str, audio_path: str, output_path: str,
                 title: str = "Sunday Slow Motion", artist: str = "Kim Sanghoon",
                 sync_mode: str = "klangio", midi_path: str = None, progress_callback=None, log_callback=None):
        self.pdf_path = pdf_path
        self.audio_path = audio_path
        self.output_path = output_path
        self.title = title
        self.artist = artist
        self.sync_mode = sync_mode
        self.midi_path = midi_path
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        
        self.width = 1920
        self.height = 1080
        self.fps = 30

    def render(self):
        """동영상 생성 프로세스 실행"""
        audio_clip = AudioFileClip(self.audio_path)
        audio_duration = audio_clip.duration
        
        intro_duration = 3.0
        outro_duration = 3.0
        # 8페이지 악보 전체 세로 캔버스 이미지 및 페이지 Y 위치 생성
        sheet_img, page_y_positions = convert_pdf_to_multi_page_image(self.pdf_path, dpi=200)
        
        if self.log_callback:
            self.log_callback("[1차 스캔 완료] PDF 파일 악보의 전체 단(System) 레이아웃 분할 분석 완료")
            
        # 한 단(System)의 높이가 화면 높이(1080) 안에 모두 들어오도록 스케일 동적 계산 (가로세로 비율 유지)
        systems_per_page = 2
        orig_page_h = page_y_positions[1] - page_y_positions[0] if len(page_y_positions) > 1 else sheet_img.height
        orig_sys_h = orig_page_h / systems_per_page
        
        max_sys_h = self.height - 120  # 상/하단 여백 및 브랜딩 바 고려
        scale = min(self.width / sheet_img.width, max_sys_h / orig_sys_h)
        
        target_w = int(sheet_img.width * scale)
        target_h = int(sheet_img.height * scale)
        scaled_page_y = [int(py * scale) for py in page_y_positions]

        sheet_resized = sheet_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        sheet_np = np.array(sheet_resized)
        
        x_offset = (self.width - target_w) // 2

        # 1. 음표 시작 위치(검은색) 스캔 알고리즘 적용 및 로그 출력
        # 대보표 묶음줄, 음자리표, 조표, 박자표를 건너뛰고 실제 첫 음표를 스캔하기 위해 범위를 24%부터 시작
        scan_x_start = int(target_w * 0.24)
        scan_x_end = int(target_w * 0.45)
        scan_y_start = scaled_page_y[0]
        scan_y_end = scaled_page_y[1] if len(scaled_page_y) > 1 else target_h
        
        first_note_x = int(target_w * 0.24)
        detected_color = None
        
        if self.log_callback:
            self.log_callback("Pdf파일 음표시작의 실제 검은색 은표 색상을 스캔합니다...")
            
        for x in range(scan_x_start, scan_x_end):
            col_pixels = sheet_np[scan_y_start:scan_y_end, x]
            # 어두운 픽셀 (RGB 모두 100 이하) 검출
            dark_pixels = np.all(col_pixels < 100, axis=-1)
            if np.sum(dark_pixels) > 15: # 임계값 (음표)
                first_note_x = x
                dark_idx = np.where(dark_pixels)[0][0]
                detected_color = col_pixels[dark_idx]
                break
                
        if self.log_callback and detected_color is not None:
            self.log_callback(f"[스캔 완료] 실제 음표시작 검은색 색상 감지됨: RGB{tuple(detected_color)} (X위치: {first_note_x}px)")
        elif self.log_callback:
            self.log_callback(f"[스캔 실패] 음표를 찾지 못해 기본 위치를 사용합니다.")

        sync_mgr = SyncManager(
            audio_duration=audio_duration,
            intro_duration=intro_duration,
            outro_duration=outro_duration,
            midi_path=self.midi_path,
            page_y_positions=scaled_page_y,
            img_height=target_h,
            log_callback=self.log_callback
        )
        sync_mgr.first_note_ratio = first_note_x / target_w
        
        if self.log_callback:
            self.log_callback("--- [최종 분석 데이터 기반 렌더링 시작] ---")

        # 1. 인트로 클립
        intro_img = create_text_image(self.width, self.height, self.title, f"Composed & Arranged by {self.artist}")
        intro_np = np.array(intro_img)
        
        def make_intro_frame(t):
            alpha = 1.0
            if t < 0.8:
                alpha = t / 0.8
            elif t > intro_duration - 0.8:
                alpha = max(0.0, (intro_duration - t) / 0.8)
            return (intro_np * alpha).astype(np.uint8)

        intro_clip = VideoClip(make_intro_frame, duration=intro_duration)

        # 2. 메인 동영상 클립 (Klangio 앙상블 단별 스크롤 및 세로 에메랄드 커서 동기화)
        def make_main_frame(t):
            if self.progress_callback:
                prog = int(50 + (t / audio_duration) * 45)
                self.progress_callback(prog)
                
            frame = np.full((self.height, self.width, 3), 250, dtype=np.uint8)
            
            # 연동된 싱크 계산 (스크롤 YOffset 및 커서 좌표)
            y_offset, (cx, cy, box_w, box_h) = sync_mgr.calculate_sync(t, target_w, target_h, self.height)
            
            visible_h = min(self.height, target_h - y_offset)
            if visible_h > 0:
                frame[0:visible_h, x_offset:x_offset + target_w] = sheet_np[y_offset:y_offset + visible_h, 0:target_w]
                
            if self.sync_mode == "klangio":
                cy_start = max(42, cy)
                cy_end = min(self.height, cy + box_h)
                if cy_end > cy_start:
                    overlay = frame.copy()
                    emerald_color = (200, 211, 76)  # 민트 에메랄드 청록색 (BGR)
                    cv2.rectangle(overlay, (x_offset + cx, cy_start), (x_offset + cx + box_w, cy_end), emerald_color, -1)
                    alpha = 0.55
                    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
                
            # 상단 헤더 브랜딩 바
            cv2.rectangle(frame, (0, 0), (self.width, 42), (30, 30, 38), -1)
            cv2.putText(frame, f"{self.title} - {self.artist}", (20, 29),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (245, 245, 255), 2)
            
            return frame

        main_clip = VideoClip(make_main_frame, duration=audio_duration)
        main_clip = main_clip.with_audio(audio_clip)

        # 3. 아웃트로 클립
        outro_img = create_text_image(self.width, self.height, "Thank You for Watching", "Subscribe & Like for More Music Videos!")
        outro_np = np.array(outro_img)
        
        def make_outro_frame(t):
            alpha = 1.0
            if t > outro_duration - 1.0:
                alpha = max(0.0, (outro_duration - t) / 1.0)
            return (outro_np * alpha).astype(np.uint8)

        outro_clip = VideoClip(make_outro_frame, duration=outro_duration)

        # 4. 전체 비디오 클립 합성
        final_clip = concatenate_videoclips([intro_clip, main_clip, outro_clip])
        
        os.makedirs(os.path.dirname(os.path.abspath(self.output_path)), exist_ok=True)
        final_clip.write_videofile(
            self.output_path,
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            logger=None
        )
        
        audio_clip.close()
        final_clip.close()
        
        if self.log_callback:
            self.log_callback("--- [렌더링 프로세스 완료] ---")
            
        if self.progress_callback:
            self.progress_callback(100)
