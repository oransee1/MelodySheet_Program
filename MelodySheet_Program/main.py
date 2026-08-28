import sys
import os
import ctypes
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    if os.name == 'nt':
        myappid = 'dicia.melodysheet.videogenerator.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
