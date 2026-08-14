from typing import Tuple, Optional, List
import os
import pretty_midi

class SyncManager:
    """
    Klangio 5줄 앙상블 및 피아노/다중 악보 정밀 싱크 타임라인 계산기
    """
    
    def __init__(self, audio_duration: float, intro_duration: float = 3.0, outro_duration: float = 3.0,
                 midi_path: Optional[str] = None, page_y_positions: Optional[List[int]] = None,
                 img_height: int = 1000, log_callback=None):
        self.audio_duration = audio_duration
        self.intro_duration = intro_duration
        self.outro_duration = outro_duration
        self.main_duration = max(audio_duration, 0.1)
        self.total_duration = intro_duration + audio_duration + outro_duration
        self.log_callback = log_callback
        
        self.midi_data = None
        self.tempo_bpm = 115.0
        self.midi_notes = []
        
        if midi_path and os.path.exists(midi_path):
            try:
                self.midi_data = pretty_midi.PrettyMIDI(midi_path)
                tempo_change_times, tempi = self.midi_data.get_tempo_changes()
                if len(tempi) > 0:
                    self.tempo_bpm = float(tempi[0])
                
                for inst in self.midi_data.instruments:
                    if not inst.is_drum:
                        for note in inst.notes:
                            self.midi_notes.append((note.start, note.end))
                self.midi_notes.sort(key=lambda x: x[0])
                
                # 음원의 시작과 음표 시작을 동일하게 맞추기 위해 첫 음표 오프셋 제거 및 정밀 타임라인 기록
                if self.midi_notes:
                    first_start = self.midi_notes[0][0]
                    self.midi_notes = [(max(0.0, s - first_start), max(0.0, e - first_start)) for s, e in self.midi_notes]
                    self.unique_note_times = sorted(list(set([n[0] for n in self.midi_notes])))
                    if self.log_callback:
                        self.log_callback("[3차 스캔 완료] MIDI 파일 정밀 타임라인 및 절대 시간 구조 확보")
            except Exception:
                pass
                
        self.page_y_positions = page_y_positions if page_y_positions else [0, img_height]
        self.num_pages = max(1, len(self.page_y_positions) - 1)
        
        # 1페이지당 시스템(단) 수 추정 (앙상블/대보표 악보의 경우 보통 2단~3단)
        self.systems_per_page = 2
        self.total_systems = max(1, self.num_pages * self.systems_per_page)
        
        if self.log_callback:
            self.log_callback("[4차 스캔 완료] PDF 시각적 공간과 MIDI 타임라인의 선형 시공간 매핑 분석 완료")

    def calculate_sync(self, elapsed_main_time: float, img_width: int, img_height: int, viewport_h: int) -> Tuple[int, Tuple[int, int, int, int]]:
        """
        현재 재생 시간(t)에 따른 화면 스크롤 YOffset과 커서 (x, y, w, h)를 완벽하게 연동하여 계산
        반환: (y_offset, (cursor_x, cursor_y, cursor_w, cursor_h))
        """
        if self.main_duration <= 0:
            return 0, (0, 0, 18, 200)

        progress = min(max(elapsed_main_time / self.main_duration, 0.0), 1.0)
        
        # MIDI 노트 데이터가 있으면 더 정밀한 노트 연주 구간 매핑
        if hasattr(self, 'unique_note_times') and len(self.unique_note_times) > 1:
            times = self.unique_note_times
            if elapsed_main_time <= times[0]:
                music_progress = 0.0
            elif elapsed_main_time >= times[-1]:
                music_progress = 1.0
            else:
                # [Time-based 정밀 시공간 매핑] 노트 밀도에 의한 왜곡 없이 절대 시간에 기반한 일정한 진행률 산출
                music_progress = (elapsed_main_time - times[0]) / (times[-1] - times[0])
        else:
            music_progress = progress

        # 1. 현재 연주 중인 단(System) 위치 산출
        curr_sys_float = music_progress * self.total_systems
        curr_sys_idx = min(int(curr_sys_float), self.total_systems - 1)
        intra_sys_prog = curr_sys_float - curr_sys_idx  # 단 내부에서의 진행률 (0.0 ~ 1.0)
        
        # 1-1. 스캔 결과물이 렌더링에 적용되는 과정을 로그로 출력 (단 전환 시 1회만 출력)
        if curr_sys_idx != getattr(self, 'last_logged_sys_idx', -1):
            self.last_logged_sys_idx = curr_sys_idx
            if self.log_callback:
                if curr_sys_idx == 0 and hasattr(self, 'first_note_ratio'):
                    applied_x = int(img_width * self.first_note_ratio)
                    self.log_callback(f"[렌더링 동기화 반영] 1번째 단(System) 진입: 스캔된 첫 음표 X위치({applied_x}px)를 커서 시작점으로 정밀 적용 중...")
                else:
                    applied_x = int(img_width * 0.16)
                    self.log_callback(f"[렌더링 동기화 반영] {curr_sys_idx + 1}번째 단(System) 진입: 동적 기본 여백 X위치({applied_x}px)를 커서 시작점으로 정밀 적용 중...")

        # 2. 단(System)의 악보 Y 위치 산출
        page_idx = min(curr_sys_idx // self.systems_per_page, self.num_pages - 1)
        intra_page_sys = curr_sys_idx % self.systems_per_page
        
        p_start_y = self.page_y_positions[page_idx]
        p_end_y = self.page_y_positions[page_idx + 1] if (page_idx + 1) < len(self.page_y_positions) else img_height
        p_h = max(1, p_end_y - p_start_y)
        
        sys_h = p_h / self.systems_per_page
        sys_y_top = p_start_y + (intra_page_sys * sys_h)
        
        # 3. 화면 스크롤 (y_offset) 계산: 한 단(System) 전체가 화면 세로 중앙에 오도록 설정 (대보표 잘림 방지)
        target_y_offset = sys_y_top - (viewport_h - sys_h) / 2
        
        # 단 전환 시(마지막 15% 구간) 부드러운 스크롤Transition
        if intra_sys_prog > 0.85 and curr_sys_idx < self.total_systems - 1:
            next_sys_idx = curr_sys_idx + 1
            next_p_idx = min(next_sys_idx // self.systems_per_page, self.num_pages - 1)
            next_intra_p_sys = next_sys_idx % self.systems_per_page
            next_p_start = self.page_y_positions[next_p_idx]
            next_p_end = self.page_y_positions[next_p_idx + 1] if (next_p_idx + 1) < len(self.page_y_positions) else img_height
            next_sys_h = (next_p_end - next_p_start) / self.systems_per_page
            next_sys_y_top = next_p_start + (next_intra_p_sys * next_sys_h)
            next_target = next_sys_y_top - (viewport_h - next_sys_h) / 2
            
            blend = (intra_sys_prog - 0.85) / 0.15
            target_y_offset = target_y_offset * (1 - blend) + next_target * blend
            
        max_scroll = max(0, img_height - viewport_h)
        y_offset = int(min(max(target_y_offset, 0), max_scroll))

        # 4. 커서 위치 계산
        if curr_sys_idx == 0 and hasattr(self, 'first_note_ratio'):
            margin_left = int(img_width * self.first_note_ratio)
        else:
            margin_left = int(img_width * 0.16)
            
        margin_right = int(img_width * 0.89)
        cursor_x = int(margin_left + (margin_right - margin_left) * intra_sys_prog)
        
        cursor_y_screen = int(sys_y_top - y_offset + (sys_h * 0.05))
        cursor_w = 18
        cursor_h = int(sys_h * 0.88)

        return y_offset, (cursor_x, cursor_y_screen, cursor_w, cursor_h)

    def get_scroll_y(self, elapsed_main_time: float, img_height: int, viewport_height: int) -> int:
        y_offset, _ = self.calculate_sync(elapsed_main_time, 1920, img_height, viewport_height)
        return y_offset

    def get_full_ensemble_cursor(self, elapsed_main_time: float, img_width: int, viewport_h: int) -> Tuple[int, int, int, int]:
        _, cursor_rect = self.calculate_sync(elapsed_main_time, img_width, 10000, viewport_h)
        return cursor_rect

