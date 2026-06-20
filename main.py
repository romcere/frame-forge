# -*- coding: utf-8 -*-
"""FrameForge 入口 —— 视频帧处理桌面工具"""

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from qt_material import apply_stylesheet
from ui import VideoToolUI


if __name__ == "__main__":
    # 高 DPI 适配（2560x1600 等高分屏）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # Material Design 主题 + 高分屏密度缩放
    apply_stylesheet(app, theme="light_blue.xml", extra={"density_scale": 2})

    window = VideoToolUI()
    window.show()
    sys.exit(app.exec_())
