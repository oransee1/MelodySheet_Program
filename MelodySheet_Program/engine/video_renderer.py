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
import pretty_midi

def create_text_image(width: int, height: int, title: str, subtitle: str, bg_color=(20, 20, 25), text_color=(255, 255, 255)) -> Image.Image:
    """인트로 / 아웃트로용 텍스트 이미지 생성"""
    mode = "RGBA" if len(bg_color) == 4 else "RGB"
    img = Image.new(mode, (width, height), bg_color)
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
                 sync_mode: str = "klangio", midi_path: str = None, musicxml_path: str = None, progress_callback=None, log_callback=None,
                 fps: int = 120):
        self.pdf_path = pdf_path
        self.audio_path = audio_path
        self.output_path = output_path
        self.title = title
        self.artist = artist
        self.sync_mode = sync_mode
        self.midi_path = midi_path
        self.musicxml_path = musicxml_path
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        
        self.width = 1920
        self.height = 1080
        self.fps = int(fps) if fps and int(fps) > 0 else 120

    def _sidecar(self, base_path, extensions):
        return find_sidecar(base_path, extensions)

    def _detect_audio_offset(self, audio_clip, timeline):
        """음원의 실제 시작점과 MIDI/악보의 첫 음표 시작점 간의 차이를 계산하여 100% 동기화합니다."""
        sr = 11025
        probe = min(4.0, float(audio_clip.duration or 0.0))
        audio_onset = 0.0
        if probe > 0:
            try:
                head = audio_clip.subclipped(0, probe)
                arr = head.to_soundarray(fps=sr)
                if arr is not None and len(arr) > 0:
                    if arr.ndim > 1:
                        arr = arr.mean(axis=1)
                    hop = max(1, int(sr * 0.01))
                    peak = float(np.max(np.abs(arr))) if len(arr) else 0.0
                    thresh = max(0.01, peak * 0.03)
                    for i in range(0, len(arr) - hop, hop):
                        if float(np.sqrt(np.mean(arr[i : i + hop] ** 2))) >= thresh:
                            audio_onset = i / float(sr)
                            break
            except Exception:
                pass
        
        # MIDI의 첫 음 시각(midi_onset) 찾기
        midi_onset = 0.0
        if self.midi_path and os.path.exists(self.midi_path):
            try:
                import pretty_midi
                pm = pretty_midi.PrettyMIDI(self.midi_path)
                first_notes = []
                for inst in pm.instruments:
                    if not inst.is_drum and inst.notes:
                        first_notes.append(min(n.start for n in inst.notes))
                if first_notes:
                    midi_onset = min(first_notes)
            except Exception:
                pass
                
        # 음원보다 MIDI가 늦게 시작한다면, offset은 음수여야 커서가 미리 앞으로 당겨짐
        final_offset = audio_onset - midi_onset
        
        if self.log_callback:
            self.log_callback(f"[음원] 오디오 첫 소리: {audio_onset:.3f}s, MIDI 첫 음표: {midi_onset:.3f}s -> 적용 오프셋: {final_offset:.3f}s")
            
        return final_offset

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

        musicxml_path = self.musicxml_path
        if not musicxml_path or not os.path.isfile(musicxml_path):
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
            total_measures=timeline.n_measures if timeline else 0,
            log_callback=self.log_callback,
        )

        if layout.systems and timeline.n_measures > 0:
            layout.systems[-1].end_measure = max(layout.systems[-1].start_measure, timeline.n_measures)
        attach_measure_anchors(
            timeline,
            layout,
            musicxml_path,
            log_callback=self.log_callback,
            midi_path=midi_path,
            stitched_img=sheet_raw,
            pdf_path=self.pdf_path,
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

        # 가장 큰 단이 화면 안에 들어가고, 좌우 여백(85%)을 확보하도록 스케일
        if layout.systems:
            orig_sys_h = max(s.y1 - s.y0 for s in layout.systems)
            # 첫 번째 단은 위쪽의 제목/작곡가 영역까지 모두 화면에 들어와야 하므로, 해당 높이를 포함시킵니다.
            first_page_top = page_y_positions[layout.systems[0].page_index] if page_y_positions else 0
            first_sys_total_h = layout.systems[0].y1 - first_page_top
            orig_sys_h = max(orig_sys_h, first_sys_total_h)
            orig_sys_w = max(s.x_right - s.x_left for s in layout.systems)
        else:
            orig_page_h = page_y_positions[1] - page_y_positions[0] if len(page_y_positions) > 1 else sheet_img.height
            orig_sys_h = orig_page_h / 2.0
            orig_sys_w = sheet_img.width

        max_sys_h = self.height - 120
        max_sys_w = self.width * 0.85
        scale = min(
            self.width / sheet_img.width,
            max_sys_h / max(orig_sys_h, 1.0),
            max_sys_w / max(orig_sys_w, 1.0)
        )

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

        # 인트로 클립 생성은 메인 프레임 함수 선언 이후(아래)로 이동됨

        # --- Piano Roll Setup ---
        piano_notes = []
        if midi_path and os.path.exists(midi_path):
            try:
                pm = pretty_midi.PrettyMIDI(midi_path)
                possible_pianos = []
                if self.log_callback:
                    self.log_callback("--- [MIDI 피아노 트랙 분석 시작] ---")
                    
                for inst in pm.instruments:
                    if self.log_callback:
                        self.log_callback(f"트랙 확인: '{inst.name}' (Program: {inst.program}, Drum: {inst.is_drum})")
                        
                    if inst.is_drum:
                        if self.log_callback:
                            self.log_callback("  -> 제외 (사유: 드럼 트랙)")
                        continue
                        
                    name_lower = inst.name.lower() if inst.name else ""
                    
                    # 피아노(또는 건반) 트랙임을 암시하는 키워드
                    is_piano_name = any(k in name_lower for k in ["piano", "피아노", "kbd", "clavier", "klavier"])
                    # 왼손, 낮은 음자리표, 하단 단 등 피아노의 두 번째 파트를 암시하는 키워드
                    is_lh_or_bass_clef = any(k in name_lower for k in ["left", "lh", "bass clef", "낮은", "음자리", "lower", "bottom", "staff 2"])
                    
                    # 명시적으로 배제할 다른 악기 키워드 (단, "bass"는 bass clef와 충돌할 수 있으므로 주의)
                    exclude_keywords = ["violin", "cello", "bass", "string", "바이올린", "첼로", "베이스", "스트링", "vocal", "voice", "보컬"]
                    
                    is_piano_prog = inst.program in range(0, 8)
                    
                    has_exclude = any(k in name_lower for k in exclude_keywords)
                    
                    if has_exclude:
                        # "bass clef" 등 왼손 파트를 나타내는 명확한 표현이 있거나, 
                        # "Piano Bass" 처럼 피아노 단어가 있으면 배제하지 않고 살림 (1. 높은 음자리 + 2. 낮은 음자리 완벽 반영)
                        if is_piano_name or is_lh_or_bass_clef:
                            has_exclude = False
                        # 이름이 단순히 "bass" 또는 "베이스"이더라도, 피아노 프로그램(0~7)인 경우 
                        # 피아노 곡의 왼손 파트일 확률이 매우 높으므로 살려둡니다.
                        elif is_piano_prog and name_lower in ["bass", "베이스"]:
                            has_exclude = False
                            
                    if has_exclude:
                        if self.log_callback:
                            self.log_callback("  -> 제외 (사유: 다른 악기 배제 키워드 포함)")
                        continue
                            
                    if is_piano_prog or is_piano_name or is_lh_or_bass_clef:
                        if self.log_callback:
                            part_desc = "왼손/낮은음자리" if is_lh_or_bass_clef else ("피아노" if is_piano_name else "피아노 프로그램")
                            self.log_callback(f"  -> 포함 (인식된 파트: {part_desc})")
                        possible_pianos.append(inst)
                    else:
                        if self.log_callback:
                            self.log_callback("  -> 제외 (사유: 피아노/건반/왼손 트랙으로 인식되지 않음)")
                
                if possible_pianos:
                    # 필터링을 통과한 모든 피아노 트랙(왼손, 오른손)을 병합합니다.
                    for inst in possible_pianos:
                        piano_notes.extend(inst.notes)
            except Exception as e:
                if self.log_callback:
                    self.log_callback(f"[경고] MIDI 로드 실패: {e}")

        # [수정] MIDI 파일에 피아노 낮은 음자리표 등 특정 파트가 누락된 경우를 완벽히 보완하기 위해
        # 원본 악보인 MusicXML에서 직접 1.높은 음자리 2.낮은 음자리 모든 음표를 파싱하여 병합합니다. (100% 적용)
        if musicxml_path and os.path.exists(musicxml_path):
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(musicxml_path)
                root = tree.getroot()
                
                # 네임스페이스 제거
                for elem in root.iter():
                    if '}' in elem.tag:
                        elem.tag = elem.tag.split('}', 1)[1]
                        
                xml_notes = []
                for part in root.findall(".//part"):
                    divs = 1
                    beats = 4
                    beat_type = 4
                    for meas in part.findall("measure"):
                        m_idx_str = meas.get("number")
                        if not m_idx_str or not m_idx_str.isdigit():
                            continue
                        m_idx = int(m_idx_str) - 1 # 0-based
                        if m_idx < 0 or m_idx >= len(timeline.measures):
                            continue
                        
                        m_span = timeline.measures[m_idx]
                        
                        for attrs in meas.findall(".//attributes"):
                            d = attrs.findtext("divisions")
                            if d and d.isdigit(): divs = int(d)
                            b = attrs.findtext("time/beats")
                            if b and b.isdigit(): beats = int(b)
                            bt = attrs.findtext("time/beat-type")
                            if bt and bt.isdigit(): beat_type = int(bt)
                            
                        total_divs = beats * divs * (4 / beat_type)
                        if total_divs <= 0: total_divs = divs * 4
                        
                        cur_div = 0
                        import pretty_midi
                        
                        for el in meas:
                            if el.tag == "forward":
                                d = el.findtext("duration")
                                if d and d.isdigit(): cur_div += int(d)
                            elif el.tag == "backup":
                                d = el.findtext("duration")
                                if d and d.isdigit(): cur_div -= int(d)
                                cur_div = max(0, cur_div)
                            elif el.tag == "note":
                                is_chord = el.find("chord") is not None
                                is_rest = el.find("rest") is not None
                                is_grace = el.find("grace") is not None
                                
                                dur_text = el.findtext("duration")
                                duration_divs = int(dur_text) if (dur_text and dur_text.isdigit()) else 0
                                
                                if is_chord:
                                    start_div = max(0, cur_div - duration_divs)
                                else:
                                    start_div = cur_div
                                    
                                if not is_rest and not is_grace:
                                    step = el.findtext("pitch/step")
                                    octave = el.findtext("pitch/octave")
                                    alter = el.findtext("pitch/alter")
                                    if step and octave:
                                        step_to_semi = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
                                        semi = step_to_semi.get(step.upper(), 0)
                                        oct_val = int(octave)
                                        alt_val = int(alter) if alter else 0
                                        midi_pitch = (oct_val + 1) * 12 + semi + alt_val
                                        
                                        start_frac = min(1.0, start_div / total_divs)
                                        dur_frac = min(1.0, duration_divs / total_divs)
                                        
                                        note_start = m_span.start_sec + m_span.duration_sec * start_frac
                                        note_end = note_start + max(0.1, m_span.duration_sec * dur_frac)
                                        
                                        new_note = pretty_midi.Note(
                                            velocity=80, pitch=midi_pitch, start=note_start, end=note_end
                                        )
                                        # 악보의 staff(단) 번호를 파싱하여 낮은 음자리표(2)인지 명확히 저장합니다.
                                        staff_val = el.findtext("staff")
                                        if staff_val == "2":
                                            new_note.is_bass = True
                                        elif staff_val == "1":
                                            new_note.is_bass = False
                                            
                                        xml_notes.append(new_note)
                                        
                                if not is_chord and not is_grace:
                                    cur_div += duration_divs
                                    
                if xml_notes:
                    piano_notes.extend(xml_notes)
                    if self.log_callback:
                        self.log_callback(f"  -> MusicXML 보완: 피아노 높은/낮은 음자리표 누락 방지를 위해 악보 기반 병합 완료 (총 {len(xml_notes)}개 음표 추가)")
                        
            except Exception as e:
                if self.log_callback:
                    self.log_callback(f"[경고] MusicXML 음표 파싱 병합 실패: {e}")

        if piano_notes:
            # 중복 노트 필터링 (동일 피치, 거의 동일 시작 시간)
            unique_notes = []
            piano_notes.sort(key=lambda x: (x.start, x.pitch))
            for i, n in enumerate(piano_notes):
                if i > 0:
                    prev = unique_notes[-1]
                    if prev.pitch == n.pitch and abs(prev.start - n.start) < 0.05:
                        prev.end = max(prev.end, n.end)
                        continue
                unique_notes.append(n)
            piano_notes = unique_notes
            piano_notes.sort(key=lambda x: x.start)
        

        white_keys = []
        black_keys = []
        for p in range(21, 109):
            is_black = (p % 12) in [1, 3, 6, 8, 10]
            if is_black:
                black_keys.append(p)
            else:
                white_keys.append(p)
                
        white_key_w = self.width / 52.0
        key_rects = {}
        # white keys
        for i, p in enumerate(white_keys):
            x1 = int(i * white_key_w)
            x2 = int((i + 1) * white_key_w)
            key_rects[p] = (x1, x2 - x1, False)
        # black keys
        for p in black_keys:
            num_white_before = sum(1 for wp in white_keys if wp < p)
            x_center = int(num_white_before * white_key_w)
            bw = int(white_key_w * 0.6)
            bx1 = x_center - bw // 2
            key_rects[p] = (bx1, bw, True)

        # 2. 메인 동영상 클립 (Klangio 앙상블 단별 스크롤 및 세로 에메랄드 커서 동기화 + 하단 피아노 롤)
        def make_main_frame(t, is_intro=False):
            if self.progress_callback:
                prog = int(50 + (t / audio_duration) * 45)
                self.progress_callback(prog)
                
            frame = np.full((self.height, self.width, 3), 250, dtype=np.uint8)
            
            # 피아노 건반 높이를 기존 8%에서 13%로 약간 더 높였습니다. 악보 스케일 계산 로직은 변경하지 않아 악보 크기는 그대로 유지됩니다.
            keyboard_h = int(self.height * 0.13) # 1080 * 0.13 = 약 140px
            sheet_viewport_h = self.height - keyboard_h
            kb_y_start = sheet_viewport_h
            
            # 연동된 싱크 계산 (스크롤 YOffset 및 커서 좌표)
            # sync_mgr는 전체 viewport_h 대신 sheet_viewport_h를 사용해야 스크롤이 하단 건반에 가려지지 않습니다.
            y_offset, (cx, cy, box_w, box_h) = sync_mgr.calculate_sync(t, target_w, target_h, sheet_viewport_h)
            
            visible_h = min(sheet_viewport_h, target_h - y_offset)
            if visible_h > 0:
                frame[0:visible_h, x_offset:x_offset + target_w] = sheet_np[y_offset:y_offset + visible_h, 0:target_w]
                
            if self.sync_mode == "klangio":
                cy_start = max(42, cy)
                cy_end = min(sheet_viewport_h, cy + box_h)
                if cy_end > cy_start:
                    overlay = frame.copy()
                    emerald_color = (200, 211, 76)  # 민트 에메랄드 청록색 (BGR)
                    cv2.rectangle(overlay, (x_offset + cx, cy_start), (x_offset + cx + box_w, cy_end), emerald_color, -1)
                    alpha = 0.55
                    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
                    
            # 2. 현재 눌려야 할 피아노 건반(active_keys) 계산
            current_time = max(0.0, t - audio_offset)
            
            # 오디오 시작점과 MIDI 시작점 간의 갭을 보정한 current_time을 사용하여
            # 커서뿐만 아니라 피아노 롤 건반 위치도 완벽하게 동기화합니다.
            midi_time = current_time
            
            active_treble_keys = set()
            active_bass_keys = set()
            for note in piano_notes:
                if note.start > midi_time:
                    break
                # 노트가 너무 짧아 시각적으로 안 보이는 현상을 방지하기 위해 최소 0.2초간 유지합니다.
                visual_end = max(note.end, note.start + 0.2)
                if visual_end >= midi_time:
                    if getattr(note, 'is_bass', note.pitch < 60):
                        active_bass_keys.add(note.pitch)
                    else:
                        active_treble_keys.add(note.pitch)
            
            # [디버그 로그] 3~6초 구간 또는 17.5초 구간의 active_keys 확인
            if self.log_callback and int(t * 10) in [35, 40, 50, 175]:
                self.log_callback(f"[디버그] t={t:.2f}s, midi_time={midi_time:.2f}s, treble={sorted(list(active_treble_keys))}, bass={sorted(list(active_bass_keys))}")
                    
            # [수정] 시작 대기 상태(Intro/Pre-roll)에서 첫 화음을 미리 칠해두던 기존 로직을 제거했습니다.
            # 음악이 실제로 시작(midi_time 도달)되어야만 건반이 눌리게 됩니다.
                    
            # 3. 하단 피아노 건반 그리기 (흰 건반 먼저)
            for p in white_keys:
                kx, kw, is_black = key_rects[p]
                
                if p in active_treble_keys:
                    color = (255, 128, 0) # 높은 음자리: 주황색 네온 (RGB)
                elif p in active_bass_keys:
                    color = (128, 255, 0) # 낮은 음자리: 연두색 네온 (RGB)
                else:
                    color = (240, 240, 240)
                    
                cv2.rectangle(frame, (kx, kb_y_start), (kx + kw, self.height), color, -1)
                cv2.rectangle(frame, (kx, kb_y_start), (kx + kw, self.height), (50, 50, 50), 1)
                
            # 검은 건반 그리기
            for p in black_keys:
                kx, kw, is_black = key_rects[p]
                
                if p in active_treble_keys:
                    color = (255, 100, 0) # 높은 음자리 검은 건반: 약간 더 진한 주황색 네온
                elif p in active_bass_keys:
                    color = (100, 220, 0) # 낮은 음자리 검은 건반: 약간 더 진한 연두색 네온
                else:
                    color = (30, 30, 30)
                    
                cv2.rectangle(frame, (kx, kb_y_start), (kx + kw, kb_y_start + int(keyboard_h * 0.65)), color, -1)
                cv2.rectangle(frame, (kx, kb_y_start), (kx + kw, kb_y_start + int(keyboard_h * 0.65)), (10, 10, 10), 1)
                
            # 상단 헤더 브랜딩 바
            cv2.rectangle(frame, (0, 0), (self.width, 42), (30, 30, 38), -1)
            cv2.putText(frame, f"{self.title} - {self.artist}", (20, 29),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (245, 245, 255), 2)
            
            return frame

        main_clip = VideoClip(make_main_frame, duration=audio_duration)
        main_clip = main_clip.with_audio(audio_clip)

        # 1. 인트로 클립 (미리 시작음을 계산해서 악보 커서 및 건반 위치를 배경으로 깔고 진행)
        intro_bg_frame = make_main_frame(0.0, is_intro=True)
        intro_img = create_text_image(self.width, self.height, self.title, f"Composed & Arranged by {self.artist}", bg_color=(20, 20, 25, 180))
        intro_np = np.array(intro_img)
        
        if intro_np.shape[2] == 4:
            alpha_layer = intro_np[:, :, 3:4] / 255.0
            text_rgb = intro_np[:, :, :3]
        else:
            alpha_layer = np.ones((self.height, self.width, 1))
            text_rgb = intro_np
            
        def make_intro_frame(t):
            alpha = 1.0
            if t < 0.8:
                alpha = t / 0.8
            elif t > intro_duration - 0.8:
                alpha = max(0.0, (intro_duration - t) / 0.8)
            
            frame = intro_bg_frame.copy()
            current_alpha = alpha_layer * alpha
            frame = (frame * (1.0 - current_alpha) + text_rgb * current_alpha).astype(np.uint8)
            return frame

        intro_clip = VideoClip(make_intro_frame, duration=intro_duration)

        # 3. 아웃트로 클립
        outro_img = create_text_image(self.width, self.height, "Thank You for Watching", "Subscribe & Like for More Music Videos!")
        outro_np = np.array(outro_img)
        
        def make_outro_frame(t):
            alpha = 1.0
            if t > outro_duration - 1.0:
                alpha = max(0.0, (outro_duration - t) / 1.0)
            return (outro_np * alpha).astype(np.uint8)

        outro_clip = VideoClip(make_outro_frame, duration=outro_duration)

        # 2.5 시작 전 대기(Pre-roll) 클립 추가
        # 음악이 바로 시작되어 급한 느낌을 주지 않도록, 1.5초간 악보와 건반이 준비된 첫 프레임을 무음으로 띄워줍니다.
        preroll_duration = 1.5
        preroll_clip = VideoClip(lambda t: intro_bg_frame, duration=preroll_duration)

        # 4. 전체 비디오 클립 합성
        final_clip = concatenate_videoclips([intro_clip, preroll_clip, main_clip, outro_clip])
        
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
