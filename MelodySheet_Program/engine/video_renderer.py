import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
from moviepy import VideoClip, AudioFileClip, concatenate_videoclips
from engine.sheet_processor import convert_pdf_to_multi_page_image
from engine.sync_manager import SyncManager
from engine.score_layout import analyze_score_layout
from engine.score_timeline import build_score_timeline, find_sidecar
from engine.score_notes import attach_measure_anchors
from engine.beat_audit import run_beat_audit, write_audit_file
from engine.piano_chords import extract_piano_chords, write_chord_report
from engine.violin_audit import audit_violin, write_violin_report
from engine.cello_audit import audit_cello, write_cello_report
from engine.bass_audit import audit_bass, write_bass_report

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
                 sync_mode: str = "klangio", midi_path: str = None, progress_callback=None, log_callback=None,
                 fps: int = 120):
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
        self.fps = int(fps) if fps and int(fps) > 0 else 120

    def _sidecar(self, base_path, extensions):
        return find_sidecar(base_path, extensions)

    def _detect_audio_offset(self, audio_clip, timeline):
        """음원 앞 무음만 보정한다. 다성 onset 상관은 평탄한 점수가 나와 쓰지 않는다."""
        sr = 11025
        probe = min(4.0, float(audio_clip.duration or 0.0))
        if probe <= 0:
            return 0.0
        try:
            head = audio_clip.subclipped(0, probe)
            arr = head.to_soundarray(fps=sr)
        except Exception:
            return 0.0
        if arr is None or len(arr) == 0:
            return 0.0
        if arr.ndim > 1:
            arr = arr.mean(axis=1)
        hop = max(1, int(sr * 0.01))
        peak = float(np.max(np.abs(arr))) if len(arr) else 0.0
        thresh = max(0.01, peak * 0.03)
        onset = 0.0
        for i in range(0, len(arr) - hop, hop):
            if float(np.sqrt(np.mean(arr[i : i + hop] ** 2))) >= thresh:
                onset = i / float(sr)
                break
        if onset < 0.18:
            onset = 0.0
        if self.log_callback:
            extra = None
            if timeline and timeline.music_end:
                extra = audio_clip.duration - timeline.music_end
            self.log_callback(
                f"[음원] 시작 오프셋 {onset:.3f}s"
                + (f", 악보 대비 길이차 {extra:+.3f}s" if extra is not None else "")
            )
        return onset

    def render(self):
        """동영상 생성 프로세스 실행"""
        audio_clip = AudioFileClip(self.audio_path)
        audio_duration = audio_clip.duration
        
        intro_duration = 3.0
        outro_duration = 3.0
        sheet_dpi = 200
        # 전체 페이지를 하나의 세로 캔버스로 합친 뒤, 같은 해상도에서 단/마디를 읽는다.
        sheet_img, page_y_positions = convert_pdf_to_multi_page_image(self.pdf_path, dpi=sheet_dpi)
        sheet_raw = np.array(sheet_img)

        musicxml_path = self._sidecar(self.midi_path, (".musicxml", ".xml")) or self._sidecar(
            self.pdf_path, (".musicxml", ".xml")
        )
        lilypond_path = self._sidecar(self.pdf_path, (".ly",))
        midi_path = self.midi_path if self.midi_path and os.path.isfile(self.midi_path) else None
        if midi_path and os.path.splitext(midi_path)[1].lower() not in (".mid", ".midi"):
            midi_path = self._sidecar(self.pdf_path, (".mid", ".midi"))

        timeline = build_score_timeline(
            musicxml_path=musicxml_path,
            lilypond_path=lilypond_path,
            midi_path=midi_path,
            log_callback=self.log_callback,
        )
        layout = analyze_score_layout(
            pdf_path=self.pdf_path,
            stitched_img=sheet_raw,
            page_y_positions=page_y_positions,
            dpi=sheet_dpi,
            total_measures=timeline.n_measures,
            log_callback=self.log_callback,
        )
        attach_measure_anchors(
            timeline,
            layout,
            musicxml_path,
            log_callback=self.log_callback,
            midi_path=None,
            stitched_img=sheet_raw,
        )

        if self.log_callback:
            self.log_callback("[1차 스캔 완료] PDF 단 · 마디 세로줄 · 음표 앵커 분석 완료")

        chord_report = extract_piano_chords(timeline, midi_path, musicxml_path)
        chord_path = write_chord_report(self.output_path, chord_report)
        if self.log_callback:
            for line in chord_report.summary_lines():
                self.log_callback(line)
            self.log_callback(f"[피아노 화음] 상세: {chord_path}")

        violin_report = audit_violin(timeline, midi_path, musicxml_path)
        violin_path = write_violin_report(self.output_path, violin_report)
        if self.log_callback:
            for line in violin_report.summary_lines():
                self.log_callback(line)
            self.log_callback(f"[바이올린] 상세: {violin_path}")

        cello_report = audit_cello(timeline, midi_path, musicxml_path)
        cello_path = write_cello_report(self.output_path, cello_report)
        if self.log_callback:
            for line in cello_report.summary_lines():
                self.log_callback(line)
            self.log_callback(f"[첼로] 상세: {cello_path}")

        bass_report = audit_bass(timeline, midi_path, musicxml_path)
        bass_path = write_bass_report(self.output_path, bass_report)
        if self.log_callback:
            for line in bass_report.summary_lines():
                self.log_callback(line)
            self.log_callback(f"[베이스] 상세: {bass_path}")

        # 가장 큰 단이 화면 안에 들어가도록 스케일
        if layout.systems:
            orig_sys_h = max(s.y1 - s.y0 for s in layout.systems)
        else:
            orig_page_h = page_y_positions[1] - page_y_positions[0] if len(page_y_positions) > 1 else sheet_img.height
            orig_sys_h = orig_page_h / 2.0

        max_sys_h = self.height - 120
        scale = min(self.width / sheet_img.width, max_sys_h / max(orig_sys_h, 1.0))

        target_w = int(sheet_img.width * scale)
        target_h = int(sheet_img.height * scale)
        scaled_page_y = [int(py * scale) for py in page_y_positions]
        layout = layout.scaled(scale)

        sheet_resized = sheet_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        sheet_np = np.array(sheet_resized)

        x_offset = (self.width - target_w) // 2
        audio_offset = self._detect_audio_offset(audio_clip, timeline)

        sync_mgr = SyncManager(
            audio_duration=audio_duration,
            intro_duration=intro_duration,
            outro_duration=outro_duration,
            midi_path=midi_path,
            page_y_positions=scaled_page_y,
            img_height=target_h,
            log_callback=self.log_callback,
            layout=layout,
            timeline=timeline,
            audio_offset=audio_offset,
        )

        audit = run_beat_audit(
            timeline=timeline,
            layout=layout,
            sync_mgr=sync_mgr,
            audio_path=self.audio_path,
            midi_path=midi_path,
            musicxml_path=musicxml_path,
            lilypond_path=lilypond_path,
            img_width=target_w,
            img_height=target_h,
            viewport_h=self.height,
        )
        audit_path = write_audit_file(self.output_path, audit)
        if self.log_callback:
            for line in audit.summary_lines:
                self.log_callback(line)
            self.log_callback(f"[교차검증] 상세: {audit_path}")
            if audit.verdict == "FAIL":
                self.log_callback("[교차검증] FAIL — 영상은 만들지만 박자 구조가 어긋난 항목이 있습니다.")

        if self.log_callback:
            self.log_callback(
                f"--- [최종 분석 데이터 기반 렌더링 시작] {self.fps}fps "
                f"(빠른 커서 구간 프레임 간격 {1000.0 / self.fps:.1f}ms) ---"
            )

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
