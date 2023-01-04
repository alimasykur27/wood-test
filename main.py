# This Python file uses the following encoding: utf-8
import sys
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow # This is the file name of your main window

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print("[Application Error]: " + e)
