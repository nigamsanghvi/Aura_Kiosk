import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import KioskGUI

app = QApplication(sys.argv)
window = KioskGUI()
window.show()
sys.exit(app.exec())