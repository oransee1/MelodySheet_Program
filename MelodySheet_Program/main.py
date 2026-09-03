import sys
import os
import ctypes
# Qt 플랫폼 플러그인(qwindows.dll) 경로 자동 설정
if not getattr(sys, 'frozen', False):
    import PyQt5
    pyqt_plugins = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
    if os.path.exists(pyqt_plugins):
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(pyqt_plugins, "platforms")
        from PyQt5.QtCore import QCoreApplication
        QCoreApplication.addLibraryPath(pyqt_plugins)

from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    if os.name == 'nt':
        myappid = 'dicia.melodysheet.videogenerator.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    if os.environ.get("MELODYSHEET_TEST_QUIT"):
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(int(os.environ.get("MELODYSHEET_TEST_QUIT")), app.quit)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
