import sys
from PyQt5.QtWidgets import QApplication
from ui import VideoToolUI


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = VideoToolUI()

    # 简单美化
    window.setStyleSheet("""
        QWidget {
            font-size: 14px;
        }
        QPushButton {
            padding: 6px;
            background-color: #2d89ef;
            color: white;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #1b5fbd;
        }
        QTextEdit {
            background-color: #111;
            color: #0f0;
        }
    """)

    window.show()
    sys.exit(app.exec_())