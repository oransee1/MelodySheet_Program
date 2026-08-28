import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QComboBox, QFileDialog, QProgressBar,
                             QTextEdit, QGroupBox, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QTextCursor, QIcon
from engine.video_renderer import VideoRenderer

DARK_STYLE = """
QMainWindow {
    background-color: #121216;
}
QWidget {
    color: #E0E0E6;
    font-family: 'Segoe UI', Malgun Gothic, sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #1A1A22;
    border: 1px solid #2D2D3A;
    border-radius: 8px;
    margin-top: 12px;
    font-weight: bold;
    color: #4C84FF;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
}
QLineEdit, QComboBox {
    background-color: #242430;
    border: 1px solid #363648;
    border-radius: 5px;
    padding: 7px 10px;
    color: #F0F0F5;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #4C84FF;
}
QComboBox QAbstractItemView {
    background-color: #242430;
    color: #F0F0F5;
    selection-background-color: #4C84FF;
    selection-color: #FFFFFF;
}
QPushButton {
    background-color: #2E3244;
    border: 1px solid #40455C;
    border-radius: 5px;
    padding: 8px 16px;
    color: #FFFFFF;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #3B4058;
}
QPushButton#btnRender {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B6CFF, stop:1 #683BFF);
    border: none;
    font-size: 15px;
    padding: 12px;
    border-radius: 6px;
}
QPushButton#btnRender:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4C7BFF, stop:1 #774BFF);
}
QProgressBar {
    border: 1px solid #303040;
    border-radius: 6px;
    background-color: #1E1E26;
    text-align: center;
    color: white;
}
QProgressBar::chunk {
    background-color: #4C84FF;
    border-radius: 5px;
}
QTextEdit {
    background-color: #16161E;
    border: 1px solid #292938;
    border-radius: 6px;
    color: #A0A0B0;
    font-family: 'Consolas', monospace;
}
QMessageBox {
    background-color: #1A1A22;
}
QMessageBox QLabel {
    color: #F0F0F5;
}
"""

class RenderThread(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, pdf_path, audio_path, output_path, title, artist, sync_mode, midi_path=None, musicxml_path=None, fps=120):
        super().__init__()
        self.pdf_path = pdf_path
        self.audio_path = audio_path
        self.output_path = output_path
        self.title = title
        self.artist = artist
        self.sync_mode = sync_mode
        self.midi_path = midi_path
        self.musicxml_path = musicxml_path
        self.fps = fps

    def run(self):
        try:
            self.log_signal.emit("동영상 렌더링 프로세스를 가동합니다...")
            self.progress_signal.emit(10)
            
            renderer = VideoRenderer(
                pdf_path=self.pdf_path,
                audio_path=self.audio_path,
                output_path=self.output_path,
                title=self.title,
                artist=self.artist,
                sync_mode=self.sync_mode,
                midi_path=self.midi_path,
                musicxml_path=self.musicxml_path,
                fps=self.fps,
                progress_callback=lambda p: self.progress_signal.emit(p),
                log_callback=lambda msg: self.log_signal.emit(msg)
            )
            
            try:
                import pymupdf
                with pymupdf.open(self.pdf_path) as doc:
                    page_count = len(doc)
            except Exception:
                page_count = "여러 "
                
            self.log_signal.emit(f"{page_count}페이지 악보 전체 레스터라이징 및 MIDI 정밀 싱크 분석 중...")
            renderer.render()
            
            self.log_signal.emit(f"렌더링 완료! 저장 경로: {self.output_path}")
            self.finished_signal.emit(True, self.output_path)
        except Exception as e:
            self.log_signal.emit(f"오류 발생: {str(e)}")
            self.finished_signal.emit(False, str(e))


class LogStream(QObject):
    new_text = pyqtSignal(str)

    def write(self, text):
        if text.strip():
            self.new_text.emit(str(text))

    def flush(self):
        pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MelodySheet Video Generator - 악보 시각화 동영상 제작기")
        
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.resize(820, 800)
        self.setStyleSheet(DARK_STYLE)
        
        self.init_ui()
        self.auto_fill_default_paths()
        
        # 시스템 표준 출력(print 등) 및 에러를 로그 창으로 리다이렉트
        self.log_stream = LogStream()
        self.log_stream.new_text.connect(self.log)
        sys.stdout = self.log_stream
        sys.stderr = self.log_stream

    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title Banner
        title_label = QLabel("<span style='color: #9acd32;'>♫</span> MelodySheet Video Generator")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #FFFFFF; margin-bottom: 5px;")
        layout.addWidget(title_label)

        sub_label = QLabel("Suno 음원, PDF 악보 및 MIDI/MusicXML/GP5/LY 옵션 파일 지원 동영상 제작기")
        sub_label.setStyleSheet("color: #9090A0;")
        layout.addWidget(sub_label)

        # 1. 파일 선택 그룹
        grp_files = QGroupBox(" 1. 음원 및 악보 파일 선택 (기본 및 옵션) ")
        layout_files = QVBoxLayout(grp_files)
        
        # Audio File
        row_audio = QHBoxLayout()
        row_audio.addWidget(QLabel("기본 음원 (.mp3/.wav):"))
        self.txt_audio = QLineEdit()
        btn_browse_audio = QPushButton("찾아보기")
        btn_browse_audio.clicked.connect(self.browse_audio)
        row_audio.addWidget(self.txt_audio)
        row_audio.addWidget(btn_browse_audio)
        layout_files.addLayout(row_audio)

        # Sheet File
        row_sheet = QHBoxLayout()
        row_sheet.addWidget(QLabel("기본 악보 (.pdf/.png):"))
        self.txt_sheet = QLineEdit()
        btn_browse_sheet = QPushButton("찾아보기")
        btn_browse_sheet.clicked.connect(self.browse_sheet)
        row_sheet.addWidget(self.txt_sheet)
        row_sheet.addWidget(btn_browse_sheet)
        layout_files.addLayout(row_sheet)

        # Optional MIDI File
        row_midi = QHBoxLayout()
        row_midi.addWidget(QLabel("옵션 MIDI (.mid):"))
        self.txt_midi = QLineEdit()
        btn_browse_midi = QPushButton("찾아보기")
        btn_browse_midi.clicked.connect(self.browse_midi)
        row_midi.addWidget(self.txt_midi)
        row_midi.addWidget(btn_browse_midi)
        layout_files.addLayout(row_midi)

        # Optional MusicXML File
        row_xml = QHBoxLayout()
        row_xml.addWidget(QLabel("옵션 MusicXML (.musicxml):"))
        self.txt_xml = QLineEdit()
        btn_browse_xml = QPushButton("찾아보기")
        btn_browse_xml.clicked.connect(self.browse_xml)
        row_xml.addWidget(self.txt_xml)
        row_xml.addWidget(btn_browse_xml)
        layout_files.addLayout(row_xml)

        # Save Path
        row_out = QHBoxLayout()
        row_out.addWidget(QLabel("저장 폴더:"))
        self.txt_output = QLineEdit()
        btn_browse_out = QPushButton("찾아보기")
        btn_browse_out.clicked.connect(self.browse_output)
        row_out.addWidget(self.txt_output)
        row_out.addWidget(btn_browse_out)
        layout_files.addLayout(row_out)

        layout.addWidget(grp_files)

        # 2. 곡 및 브랜딩 설정 그룹
        grp_meta = QGroupBox(" 2. 브랜딩 및 악보 싱크 옵션 ")
        layout_meta = QVBoxLayout(grp_meta)

        row_meta1 = QHBoxLayout()
        row_meta1.addWidget(QLabel("곡 제목:"))
        self.txt_title = QLineEdit("Sunday Slow Motion")
        row_meta1.addWidget(self.txt_title)
        
        row_meta1.addWidget(QLabel("아티스트:"))
        self.txt_artist = QLineEdit("Kim Sanghoon")
        row_meta1.addWidget(self.txt_artist)
        layout_meta.addLayout(row_meta1)

        row_meta2 = QHBoxLayout()
        row_meta2.addWidget(QLabel("시각화 싱크 방식:"))
        self.combo_sync = QComboBox()
        self.combo_sync.addItems([
            "Klangio Emerald Highlight (Klangio 스타일 반투명 커서)",
            "Smooth Vertical Scroll (수직 자동 스크롤)"
        ])
        row_meta2.addWidget(self.combo_sync)
        layout_meta.addLayout(row_meta2)

        row_meta3 = QHBoxLayout()
        row_meta3.addWidget(QLabel("프레임레이트:"))
        self.combo_fps = QComboBox()
        self.combo_fps.addItems([
            "120 fps (빠른 커서 구간, 권장)",
            "60 fps (중간)",
            "30 fps (가벼움, 예전 기본)",
        ])
        self.combo_fps.setCurrentIndex(0)
        row_meta3.addWidget(self.combo_fps)
        layout_meta.addLayout(row_meta3)

        layout.addWidget(grp_meta)

        # 3. 렌더링 실행 및 진행 상태
        self.btn_render = QPushButton("🎬 동영상 생성 시작")
        self.btn_render.setObjectName("btnRender")
        self.btn_render.clicked.connect(self.start_rendering)
        layout.addWidget(self.btn_render)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setPlaceholderText("동영상 렌더링 처리 로그가 이곳에 표시됩니다...")
        layout.addWidget(self.txt_log)

        self.setCentralWidget(main_widget)

    def _first_existing(self, candidates):
        for path in candidates:
            if path and os.path.isfile(path):
                return path
        return ""

    def auto_fill_default_paths(self):
        downloads_dir = os.path.expanduser("~/Downloads")
        desktop_dir = os.path.expanduser("~/Desktop")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        today_str = datetime.now().strftime("%Y-%m-%d")
        input_today = os.path.join(base_dir, "InputData", today_str)
        input_01 = os.path.join(input_today, "Input01")
        sample_dir = os.path.join(base_dir, "Sample")

        def named(folder, ext):
            return os.path.join(folder, f"Sunday Slow Motion{ext}")

        default_audio = self._first_existing([
            named(input_01, ".mp3"),
            named(input_today, ".mp3"),
            named(sample_dir, ".mp3"),
            named(downloads_dir, ".mp3"),
            named(desktop_dir, ".mp3"),
        ])
        default_sheet = self._first_existing([
            named(input_01, ".pdf"),
            named(input_today, ".pdf"),
            named(sample_dir, ".pdf"),
            named(downloads_dir, ".pdf"),
            named(desktop_dir, ".pdf"),
        ])
        default_midi = self._first_existing([
            named(input_01, ".mid"),
            named(input_today, ".mid"),
            named(downloads_dir, ".mid"),
        ])
        default_xml = self._first_existing([
            named(input_01, ".musicxml"),
            named(input_01, ".xml"),
            named(input_today, ".musicxml"),
            named(input_today, ".xml"),
        ])

        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        output_dir = os.path.join(base_dir, "Output")
        input_data_dir = os.path.join(base_dir, "Input_Data")
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(input_data_dir, exist_ok=True)
        default_output = output_dir

        if default_audio:
            self.txt_audio.setText(default_audio)
            self.txt_title.setText(os.path.splitext(os.path.basename(default_audio))[0])
            self.txt_midi.setText(os.path.splitext(default_audio)[0] + ".mid")
        if default_sheet:
            self.txt_sheet.setText(default_sheet)
            self.extract_artist_from_pdf(default_sheet)
        if default_midi and not default_audio:
            self.txt_midi.setText(default_midi)
        if default_xml:
            self.txt_xml.setText(default_xml)
        elif default_audio:
            self.txt_xml.setText(os.path.splitext(default_audio)[0] + ".musicxml")
        self.txt_output.setText(default_output)

    def browse_audio(self):
        path, _ = QFileDialog.getOpenFileName(self, "음원 파일 선택", "", "Audio Files (*.mp3 *.wav)")
        if path:
            self.txt_audio.setText(path)
            self.txt_title.setText(os.path.splitext(os.path.basename(path))[0])
            self.txt_midi.setText(os.path.splitext(path)[0] + ".mid")
            self.txt_xml.setText(os.path.splitext(path)[0] + ".musicxml")

    def browse_sheet(self):
        path, _ = QFileDialog.getOpenFileName(self, "악보 파일 선택", "", "Sheet Files (*.pdf *.png *.jpg)")
        if path:
            self.txt_sheet.setText(path)
            self.extract_artist_from_pdf(path)

    def extract_artist_from_pdf(self, path):
        if not path.lower().endswith('.pdf'):
            return
        try:
            import pymupdf
            doc = pymupdf.open(path)
            if len(doc) > 0:
                page = doc[0]
                blocks = page.get_text("blocks")
                width = page.rect.width
                height = page.rect.height
                
                candidates = []
                for b in blocks:
                    x0, y0, x1, y1, text, block_no, block_type = b
                    if block_type != 0:
                        continue
                    if y0 < height * 0.3 and x0 > width * 0.5:
                        clean_text = text.strip()
                        if len(clean_text) >= 2 and any(c.isalpha() for c in clean_text):
                            candidates.append((y0, clean_text))
                
                if candidates:
                    candidates.sort(key=lambda x: x[0])
                    self.txt_artist.setText(candidates[0][1])
        except Exception as e:
            print(f"PDF parsing error: {e}")

    def browse_midi(self):
        path, _ = QFileDialog.getOpenFileName(self, "MIDI 파일 선택", "", "MIDI Files (*.mid *.midi *.musicxml *.gp5 *.ly)")
        if path:
            self.txt_midi.setText(path)

    def browse_xml(self):
        path, _ = QFileDialog.getOpenFileName(self, "MusicXML 파일 선택", "", "MusicXML Files (*.musicxml *.xml)")
        if path:
            self.txt_xml.setText(path)

    def browse_output(self):
        current_dir = self.txt_output.text().strip()
        path = QFileDialog.getExistingDirectory(self, "저장 폴더 선택", current_dir)
        if path:
            self.txt_output.setText(path)

    def log(self, text: str):
        self.txt_log.append(text)
        self.txt_log.moveCursor(QTextCursor.End)
        self.txt_log.ensureCursorVisible()

    def start_rendering(self):
        audio_path = self.txt_audio.text().strip()
        sheet_path = self.txt_sheet.text().strip()
        midi_path = self.txt_midi.text().strip()
        musicxml_path = self.txt_xml.text().strip()
        output_path = self.txt_output.text().strip()
        title = self.txt_title.text().strip()
        artist = self.txt_artist.text().strip()
        sync_mode = "klangio" if self.combo_sync.currentIndex() == 0 else "scroll"
        fps = (120, 60, 30)[min(self.combo_fps.currentIndex(), 2)]

        if not os.path.exists(audio_path):
            QMessageBox.warning(self, "오류", "선택한 음원 파일이 존재하지 않습니다.")
            return
        if not os.path.exists(sheet_path):
            QMessageBox.warning(self, "오류", "선택한 악보 파일이 존재하지 않습니다.")
            return

        if os.path.isdir(output_path) or not output_path.lower().endswith('.mp4'):
            safe_title = "".join([c for c in title if c.isalnum() or c in " -_"]).strip().replace(" ", "_")
            if not safe_title:
                safe_title = "Output"
            
            today_str = datetime.now().strftime("%Y-%m-%d")
            base_out_dir = os.path.join(output_path, today_str)
            os.makedirs(base_out_dir, exist_ok=True)
            
            idx = 1
            while True:
                seq_dir = os.path.join(base_out_dir, f"Output{idx:02d}")
                if not os.path.exists(seq_dir):
                    break
                idx += 1
                
            os.makedirs(seq_dir, exist_ok=True)
            output_path = os.path.join(seq_dir, f"{safe_title}_SheetVideo.mp4")

        self.btn_render.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log(f"--- 렌더링 개시: {title} ({artist}) · {fps}fps ---")

        self.render_thread = RenderThread(
            pdf_path=sheet_path,
            audio_path=audio_path,
            output_path=output_path,
            title=title,
            artist=artist,
            sync_mode=sync_mode,
            midi_path=midi_path if os.path.exists(midi_path) else None,
            musicxml_path=musicxml_path if os.path.exists(musicxml_path) else None,
            fps=fps,
        )
        self.render_thread.progress_signal.connect(self.progress_bar.setValue)
        self.render_thread.log_signal.connect(self.log)
        self.render_thread.finished_signal.connect(self.on_render_finished)
        self.render_thread.start()

    def on_render_finished(self, success: bool, message: str):
        self.btn_render.setEnabled(True)
        if success:
            QMessageBox.information(self, "완료", f"동영상 생성이 완료되었습니다!\n경로: {message}")
        else:
            QMessageBox.critical(self, "실패", f"동영상 생성 중 오류가 발생했습니다:\n{message}")
