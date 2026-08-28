from typing import Optional, Tuple

from engine.score_layout import ScoreLayout
from engine.score_timeline import ScoreTimeline


class SyncManager:
    """악보 단·마디 레이아웃과 연주 시간축을 커서/스크롤에 묶는다."""

    def __init__(
        self,
        audio_duration: float,
        intro_duration: float = 3.0,
        outro_duration: float = 3.0,
        midi_path: Optional[str] = None,
        page_y_positions=None,
        img_height: int = 1000,
        log_callback=None,
        layout: Optional[ScoreLayout] = None,
        timeline: Optional[ScoreTimeline] = None,
        audio_offset: float = 0.0,
    ):
        self.audio_duration = audio_duration
        self.intro_duration = intro_duration
        self.outro_duration = outro_duration
        self.main_duration = max(audio_duration, 0.1)
        self.total_duration = intro_duration + audio_duration + outro_duration
        self.log_callback = log_callback
        self.midi_path = midi_path
        self.layout = layout
        self.timeline = timeline
        self.audio_offset = audio_offset
        self.page_y_positions = page_y_positions if page_y_positions else [0, img_height]
        self.last_logged_sys_idx = -1

        if self.log_callback:
            if layout and layout.systems and timeline and timeline.n_measures:
                self.log_callback(
                    f"[동기화] 마디 {timeline.n_measures}개 · 단 {len(layout.systems)}개 · "
                    f"연주 {timeline.music_end:.2f}s / 음원 {audio_duration:.2f}s "
                    f"(오프셋 {audio_offset:.3f}s)"
                )
            else:
                self.log_callback("[동기화] 레이아웃/타임라인 없음 — 선형 스크롤로 대체")

    def _music_time(self, elapsed_main_time: float) -> float:
        return max(0.0, elapsed_main_time - self.audio_offset)

    def calculate_sync(
        self, elapsed_main_time: float, img_width: int, img_height: int, viewport_h: int
    ) -> Tuple[int, Tuple[int, int, int, int]]:
        """현재 음원 시각 → (스크롤 y_offset, 커서 x,y,w,h). 커서 좌표는 화면 기준."""
        if self.layout and self.layout.systems and self.timeline and self.timeline.n_measures:
            return self._sync_from_score(elapsed_main_time, img_width, img_height, viewport_h)
        return self._sync_linear(elapsed_main_time, img_width, img_height, viewport_h)

    def _sync_from_score(
        self, elapsed_main_time: float, img_width: int, img_height: int, viewport_h: int
    ) -> Tuple[int, Tuple[int, int, int, int]]:
        t = self._music_time(elapsed_main_time)
        meas_idx, intra = self.timeline.measure_at(t)
        meas = self.timeline.measures[meas_idx]
        sys = self.layout.system_for_measure(meas.number)
        if sys is None:
            return self._sync_linear(elapsed_main_time, img_width, img_height, viewport_h)

        left, right = sys.measure_x_range(meas.number)
        x_frac = meas.x_frac_at(t) if hasattr(meas, "x_frac_at") else intra
        cursor_x = int(left + (right - left) * x_frac)

        sys_h = max(1, sys.y1 - sys.y0)
        target_y_offset = self._scroll_offset(t, sys, viewport_h)

        max_scroll = max(0, img_height - viewport_h)
        y_offset = int(min(max(target_y_offset, 0), max_scroll))

        cursor_y_screen = int(sys.y0 - y_offset)
        cursor_h = int(sys_h)
        cursor_w = 16
        if cursor_y_screen < 42:
            cursor_h = max(1, cursor_h - (42 - cursor_y_screen))
            cursor_y_screen = 42
        if cursor_y_screen + cursor_h > viewport_h:
            cursor_h = max(1, viewport_h - cursor_y_screen)

        if sys.index != self.last_logged_sys_idx:
            self.last_logged_sys_idx = sys.index
            if self.log_callback:
                self.log_callback(
                    f"[렌더링 동기화] 단 {sys.index + 1}/{len(self.layout.systems)} "
                    f"마디 {sys.start_measure}-{sys.end_measure} 진입 "
                    f"(t={t:.2f}s, x={cursor_x})"
                )

        return y_offset, (cursor_x, cursor_y_screen, cursor_w, cursor_h)

    def _system_y_offset(self, sys, viewport_h: int) -> float:
        sys_h = max(1, sys.y1 - sys.y0)
        if sys.index == 0:
            # 첫 번째 단은 제목과 작곡가를 보여주기 위해 가급적 화면 맨 위(페이지 y=0)부터 보여줍니다.
            # 단, 시스템 하단이 잘리지 않도록 최소한의 스크롤만 허용합니다.
            return max(0.0, float(sys.y1 - viewport_h + 40))
        return sys.y0 - (viewport_h - sys_h) / 2.0

    def _scroll_offset(self, t: float, sys, viewport_h: int) -> float:
        """현재 단을 화면에 유지하고, 음이 끝난 뒤에만 다음 단/페이지로 옮긴다.

        예전에는 단 시간의 85%부터 미리 섞어서 다음 페이지가
        마지막 마디를 듣기도 전에 올라왔다.
        """
        hold = self._system_y_offset(sys, viewport_h)
        if sys.index + 1 >= len(self.layout.systems):
            return hold
        if sys.end_measure < 1 or sys.end_measure > len(self.timeline.measures):
            return hold

        nxt = self.layout.systems[sys.index + 1]
        nxt_off = self._system_y_offset(nxt, viewport_h)
        last = self.timeline.measures[sys.end_measure - 1]
        last_start, last_end = last.start_sec, last.end_sec
        last_dur = max(last.duration_sec, 1e-6)
        same_page = nxt.page_index == sys.page_index

        if same_page:
            # 같은 페이지 아랫단: 마지막 마디에 들어온 뒤, 그 마디의 후반에만 내린다.
            if t < last_start + last_dur * 0.70:
                return hold
            blend = (t - (last_start + last_dur * 0.70)) / (last_dur * 0.30)
        else:
            # 다음 페이지: 마지막 마디가 거의 끝날 때만 넘긴다 (최대 0.4초).
            tail = min(0.40, last_dur * 0.12)
            turn_at = last_end - tail
            if t < turn_at:
                return hold
            blend = (t - turn_at) / max(tail, 1e-6)

        blend = min(max(blend, 0.0), 1.0)
        return hold * (1.0 - blend) + nxt_off * blend

    def _sync_linear(
        self, elapsed_main_time: float, img_width: int, img_height: int, viewport_h: int
    ) -> Tuple[int, Tuple[int, int, int, int]]:
        """레이아웃을 못 읽었을 때의 최후 선형 대체."""
        if self.main_duration <= 0:
            return 0, (0, 0, 18, 200)
        progress = min(max(elapsed_main_time / self.main_duration, 0.0), 1.0)
        max_scroll = max(0, img_height - viewport_h)
        y_offset = int(progress * max_scroll)
        margin_left = int(img_width * 0.16)
        margin_right = int(img_width * 0.89)
        # 한 화면을 한 주기로 좌→우
        cycle = progress * max(1, int(round(img_height / max(viewport_h, 1))))
        intra = cycle - int(cycle)
        cursor_x = int(margin_left + (margin_right - margin_left) * intra)
        return y_offset, (cursor_x, 80, 18, viewport_h - 160)

    def get_scroll_y(self, elapsed_main_time: float, img_height: int, viewport_height: int) -> int:
        y_offset, _ = self.calculate_sync(elapsed_main_time, 1920, img_height, viewport_height)
        return y_offset

    def get_full_ensemble_cursor(
        self, elapsed_main_time: float, img_width: int, viewport_h: int
    ) -> Tuple[int, int, int, int]:
        _, cursor_rect = self.calculate_sync(elapsed_main_time, img_width, 10000, viewport_h)
        return cursor_rect
