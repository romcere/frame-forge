# -*- coding: utf-8 -*-
"""FrameForge GUI —— 基于 PyQt5 的现代化视频帧处理界面"""

import os

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QFont, QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QFileDialog, QProgressBar, QGroupBox, QSpinBox,
    QDoubleSpinBox, QFormLayout, QSplitter, QFrame,
    QComboBox, QApplication, QCheckBox,
)

from video_processor import VideoProcessor


ZOOM_LEVELS = ["75%", "100%", "125%"]


class Worker(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int, int)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(
                *self.args,
                progress_cb=lambda cur, total: self.progress.emit(cur, total),
                **{k: v for k, v in self.kwargs.items() if k != "progress_cb"},
            )
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(f"错误：{e}")


class DropLabel(QLabel):
    file_dropped = pyqtSignal(str)

    def __init__(self, text="拖拽视频到此处\n或点击下方按钮加载"):
        super().__init__(text)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(140)
        self._base_font_size = 18
        self._base_min_height = 140
        self._base_padding = 24
        self._apply_base_style()

    def _apply_base_style(self):
        self.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed #888;
                border-radius: 14px;
                background-color: #f5f5f5;
                color: #666;
                font-size: {self._base_font_size}px;
                padding: {self._base_padding}px;
            }}
        """)

    def scale_ui(self, factor: float):
        self._base_min_height = int(140 * factor)
        self._base_font_size = max(9, int(18 * factor))
        self._base_padding = int(24 * factor)
        self.setMinimumHeight(self._base_min_height)
        self._apply_base_style()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet().replace("#f5f5f5", "#e3f2fd"))

    def dragLeaveEvent(self, _):
        self.setStyleSheet(self.styleSheet().replace("#e3f2fd", "#f5f5f5"))

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(self.styleSheet().replace("#e3f2fd", "#f5f5f5"))
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                self.file_dropped.emit(path)
                return


class VideoToolUI(QWidget):
    ZOOM_PRESETS = [
        ("适应", -1),
        ("50%", 0.5),
        ("75%", 0.75),
        ("100%", 1.0),
        ("150%", 1.5),
        ("200%", 2.0),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎬 FrameForge — 视频帧处理工具")
        self.setGeometry(100, 60, 1050, 720)
        self.setMinimumSize(780, 540)

        self.processor = VideoProcessor()
        self.video_path = ""

        self._original_pixmap = None
        self._zoom_factor = -1
        self._zoom_btns = {}
        self._ui_zoom = 1.0

        self._layouts = []
        self._splitters = []

        self._init_ui()
        self._apply_style()
        self._on_ui_zoom_changed("100%")

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        self._add_layout(main_layout, spacing=14, margins=(16, 16, 16, 16))

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        top_bar.addWidget(QLabel("🔍 UI 缩放："))
        self.ui_zoom_combo = QComboBox()
        self.ui_zoom_combo.addItems(ZOOM_LEVELS)
        self.ui_zoom_combo.setCurrentText("100%")
        self.ui_zoom_combo.setFixedWidth(90)
        self.ui_zoom_combo.currentTextChanged.connect(self._on_ui_zoom_changed)
        top_bar.addWidget(self.ui_zoom_combo)
        main_layout.addLayout(top_bar)

        self.drop_label = DropLabel()
        self.drop_label.file_dropped.connect(self._on_file_dropped)

        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Microsoft YaHei", 11))

        self.tab_info = self._build_info_tab()
        self.tab_extract = self._build_extract_tab()
        self.tab_images = self._build_images_tab()
        self.tab_trim = self._build_trim_tab()

        self.tabs.addTab(self.tab_info, "📊 视频信息")
        self.tabs.addTab(self.tab_extract, "🧩 拆帧导出")
        self.tabs.addTab(self.tab_images, "🎞️ 图片转视频")
        self.tabs.addTab(self.tab_trim, "✂️ 视频裁剪")

        bottom = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(28)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(160)
        self.log.setFont(QFont("Consolas", 11))

        bottom.addWidget(self.progress_bar)
        bottom.addWidget(self.log)

        main_layout.addWidget(self.drop_label)
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(bottom)

    def _add_layout(self, layout, spacing, margins):
        layout._base_spacing = spacing
        layout._base_margins = margins
        self._layouts.append(layout)

    def _add_splitter(self, splitter, sizes):
        splitter._base_sizes = tuple(sizes)
        self._splitters.append(splitter)

    # ── Tab: 视频信息 ────────────────────────────────────

    def _build_info_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self._add_layout(layout, spacing=14, margins=(0, 0, 0, 0))

        btn_row = QHBoxLayout()
        self.btn_load = QPushButton("📂 加载视频")
        self.btn_load.setMinimumHeight(44)
        self.btn_load.setFont(QFont("Microsoft YaHei", 12))
        self.btn_load.clicked.connect(self.load_video)

        self.btn_info = QPushButton("📊 显示信息")
        self.btn_info.setMinimumHeight(44)
        self.btn_info.setFont(QFont("Microsoft YaHei", 12))
        self.btn_info.clicked.connect(self.show_info)
        self.btn_info.setEnabled(False)

        btn_row.addWidget(self.btn_load)
        btn_row.addWidget(self.btn_info)
        layout.addLayout(btn_row)

        split = QSplitter(Qt.Horizontal)
        self._add_splitter(split, (450, 600))

        thumb_widget = QWidget()
        thumb_layout = QVBoxLayout(thumb_widget)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        self._add_layout(thumb_layout, spacing=8, margins=(0, 0, 0, 0))

        self.thumbnail = QLabel("暂无预览")
        self.thumbnail.setAlignment(Qt.AlignCenter)
        self.thumbnail.setMinimumSize(400, 280)
        self.thumbnail.setStyleSheet("background:#eee; border-radius:10px;")
        self.thumbnail.setScaledContents(False)

        zoom_row = QHBoxLayout()
        self._add_layout(zoom_row, spacing=4, margins=(0, 0, 0, 0))

        for label, factor in self.ZOOM_PRESETS:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(factor == -1)
            btn.setMinimumHeight(30)
            btn.setStyleSheet("font-size: 8px; font-weight: bold; padding: 2px 6px; border-radius: 4px;")
            base_w = 56 if label != "适应" else 46
            btn.setFixedWidth(base_w)
            btn._base_fixed_width = base_w
            btn.pressed.connect(lambda f=factor: self._zoom_to(f))
            self._zoom_btns[factor] = btn
            zoom_row.addWidget(btn)

        zoom_row.addStretch()

        thumb_layout.addWidget(self.thumbnail)
        thumb_layout.addLayout(zoom_row)

        self.info_text = QLabel("未加载视频")
        self.info_text.setAlignment(Qt.AlignTop)
        self.info_text.setFont(QFont("Microsoft YaHei", 13))
        self.info_text.setStyleSheet("padding:14px;")

        split.addWidget(thumb_widget)
        split.addWidget(self.info_text)
        split.setSizes([450, 600])

        layout.addWidget(split)
        return w

    # ── Tab: 拆帧（含音频导出）────────────────────────────

    def _build_extract_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self._add_layout(layout, spacing=14, margins=(0, 0, 0, 0))

        group = QGroupBox("拆帧设置")
        group.setFont(QFont("Microsoft YaHei", 12))
        form = QFormLayout(group)
        self._add_layout(form, spacing=12, margins=(0, 0, 0, 0))

        self.extract_step = QSpinBox()
        self.extract_step.setRange(1, 9999)
        self.extract_step.setValue(1)
        self.extract_step.setMinimumHeight(34)
        self.extract_step.setToolTip("每隔 N 帧导出一张，1=逐帧导出")

        self.extract_start = QDoubleSpinBox()
        self.extract_start.setRange(0, 99999)
        self.extract_start.setDecimals(1)
        self.extract_start.setSuffix(" 秒")
        self.extract_start.setMinimumHeight(34)
        self.extract_start.setToolTip("从视频第几秒开始")

        self.extract_end = QDoubleSpinBox()
        self.extract_end.setRange(0, 99999)
        self.extract_end.setDecimals(1)
        self.extract_end.setSpecialValueText("到结尾")
        self.extract_end.setValue(0)
        self.extract_end.setSuffix(" 秒 (0=结尾)")
        self.extract_end.setMinimumHeight(34)

        # 音频导出选项
        self.extract_audio_cb = QCheckBox("同时导出音频 (.mp3)")
        self.extract_audio_cb.setFont(QFont("Microsoft YaHei", 11))

        form.addRow("帧间隔：", self.extract_step)
        form.addRow("起始时间：", self.extract_start)
        form.addRow("结束时间：", self.extract_end)
        form.addRow("", self.extract_audio_cb)
        layout.addWidget(group)

        self.btn_extract = QPushButton("🧩 开始拆帧")
        self.btn_extract.setMinimumHeight(48)
        self.btn_extract.setFont(QFont("Microsoft YaHei", 13))
        self.btn_extract.clicked.connect(self.extract_frames)
        self.btn_extract.setEnabled(False)
        layout.addWidget(self.btn_extract)
        return w

    # ── Tab: 图片转视频（含音频导入）──────────────────────

    def _build_images_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self._add_layout(layout, spacing=14, margins=(0, 0, 0, 0))

        group = QGroupBox("合成设置")
        group.setFont(QFont("Microsoft YaHei", 12))
        form = QFormLayout(group)
        self._add_layout(form, spacing=12, margins=(0, 0, 0, 0))

        row_img = QHBoxLayout()
        self.img_input = QLineEdit()
        self.img_input.setPlaceholderText("选择图片文件夹...")
        self.img_input.setMinimumHeight(34)
        self.btn_img_browse = QPushButton("📁 浏览")
        self.btn_img_browse.setMinimumHeight(34)
        self.btn_img_browse.clicked.connect(self._browse_img_dir)
        row_img.addWidget(self.img_input)
        row_img.addWidget(self.btn_img_browse)

        # 音频导入
        row_audio = QHBoxLayout()
        self.audio_input = QLineEdit()
        self.audio_input.setPlaceholderText("选择音频文件 (可选)...")
        self.audio_input.setMinimumHeight(34)
        self.btn_audio_browse = QPushButton("🎵 浏览")
        self.btn_audio_browse.setMinimumHeight(34)
        self.btn_audio_browse.clicked.connect(self._browse_audio_file)
        row_audio.addWidget(self.audio_input)
        row_audio.addWidget(self.btn_audio_browse)

        self.img_fps = QSpinBox()
        self.img_fps.setRange(1, 120)
        self.img_fps.setValue(30)
        self.img_fps.setSuffix(" FPS")
        self.img_fps.setMinimumHeight(34)

        form.addRow("图片目录：", row_img)
        form.addRow("音频文件：", row_audio)
        form.addRow("帧率：", self.img_fps)
        layout.addWidget(group)

        self.btn_img_to_video = QPushButton("🎞️ 开始合成")
        self.btn_img_to_video.setMinimumHeight(48)
        self.btn_img_to_video.setFont(QFont("Microsoft YaHei", 13))
        self.btn_img_to_video.clicked.connect(self.images_to_video)
        layout.addWidget(self.btn_img_to_video)
        return w

    # ── Tab: 视频裁剪 ────────────────────────────────────

    def _build_trim_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self._add_layout(layout, spacing=14, margins=(0, 0, 0, 0))

        group = QGroupBox("裁剪范围")
        group.setFont(QFont("Microsoft YaHei", 12))
        form = QFormLayout(group)
        self._add_layout(form, spacing=12, margins=(0, 0, 0, 0))

        self.trim_start = QDoubleSpinBox()
        self.trim_start.setRange(0, 99999)
        self.trim_start.setDecimals(1)
        self.trim_start.setSuffix(" 秒")
        self.trim_start.setMinimumHeight(34)

        self.trim_end = QDoubleSpinBox()
        self.trim_end.setRange(0, 99999)
        self.trim_end.setDecimals(1)
        self.trim_end.setValue(10.0)
        self.trim_end.setSuffix(" 秒")
        self.trim_end.setMinimumHeight(34)

        form.addRow("起始时间：", self.trim_start)
        form.addRow("结束时间：", self.trim_end)
        layout.addWidget(group)

        self.btn_trim = QPushButton("✂️ 裁剪并导出")
        self.btn_trim.setMinimumHeight(48)
        self.btn_trim.setFont(QFont("Microsoft YaHei", 13))
        self.btn_trim.clicked.connect(self.trim_video)
        self.btn_trim.setEnabled(False)
        layout.addWidget(self.btn_trim)
        return w

    # ── 样式 ────────────────────────────────────────────

    def _apply_style(self, factor: float = 1.0):
        fs = factor
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 10px;
                margin-top: {int(16*fs)}px;
                padding-top: {int(20*fs)}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {int(14*fs)}px;
                padding: 0 {int(8*fs)}px;
            }}
            QPushButton {{
                padding: {int(10*fs)}px {int(20*fs)}px;
                border-radius: {int(8*fs)}px;
                font-weight: bold;
            }}
            QPushButton:disabled {{
                background-color: #ccc;
                color: #888;
            }}
            QPushButton:checked {{
                background-color: #1565c0;
                color: white;
            }}
            QTabWidget::pane {{
                border: 1px solid #ccc;
                border-radius: {int(8*fs)}px;
                padding: {int(14*fs)}px;
            }}
            QTabBar::tab {{
                font-size: {int(14*fs)}px;
            }}
            QProgressBar {{
                border: 1px solid #bbb;
                border-radius: {int(8*fs)}px;
                text-align: center;
                height: {int(28*fs)}px;
                font-size: {int(13*fs)}px;
            }}
            QProgressBar::chunk {{
                background-color: #4caf50;
                border-radius: {int(6*fs)}px;
            }}
            QTextEdit {{
                border: 1px solid #ccc;
                border-radius: {int(8*fs)}px;
                font-size: {int(13*fs)}px;
                padding: {int(8*fs)}px;
            }}
            QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox {{
                padding: {int(6*fs)}px {int(8*fs)}px;
                font-size: {int(14*fs)}px;
                border: 1px solid #bbb;
                border-radius: {int(5*fs)}px;
            }}
            QCheckBox {{
                font-size: {int(13*fs)}px;
            }}
        """)

    # ── UI 全局缩放 ─────────────────────────────────────

    def _on_ui_zoom_changed(self, text: str):
        factor = int(text.replace("%", "")) / 100.0
        self._ui_zoom = factor
        self._apply_global_zoom(factor)

    def _apply_global_zoom(self, factor: float):
        fs = factor
        self.setGeometry(
            int(100 * fs), int(60 * fs),
            int(1050 * fs), int(720 * fs),
        )
        self.setMinimumSize(int(780 * fs), int(540 * fs))

        for layout in self._layouts:
            bs = getattr(layout, "_base_spacing", 6)
            bm = getattr(layout, "_base_margins", (0, 0, 0, 0))
            layout.setSpacing(max(1, int(bs * fs)))
            layout.setContentsMargins(
                int(bm[0] * fs), int(bm[1] * fs),
                int(bm[2] * fs), int(bm[3] * fs),
            )

        for sp in self._splitters:
            bs = getattr(sp, "_base_sizes", (400, 400))
            sp.setSizes([int(s * fs) for s in bs])

        self.drop_label.scale_ui(factor)
        self.tabs.setFont(QFont("Microsoft YaHei", max(8, int(11 * fs))))

        self.btn_load.setMinimumHeight(int(44 * fs))
        self.btn_load.setFont(QFont("Microsoft YaHei", max(8, int(12 * fs))))
        self.btn_info.setMinimumHeight(int(44 * fs))
        self.btn_info.setFont(QFont("Microsoft YaHei", max(8, int(12 * fs))))
        self.thumbnail.setMinimumSize(int(400 * fs), int(280 * fs))
        self.info_text.setFont(QFont("Microsoft YaHei", max(8, int(13 * fs))))

        btn_fs = max(6, int(8 * fs))
        for btn in self._zoom_btns.values():
            btn.setMinimumHeight(int(30 * fs))
            btn.setStyleSheet(
                f"font-size: {btn_fs}px; font-weight: bold; "
                f"padding: 2px 6px; border-radius: 4px;"
            )
            if hasattr(btn, "_base_fixed_width"):
                btn.setFixedWidth(max(32, int(btn._base_fixed_width * fs)))

        self._scale_group_fonts(fs)
        self.extract_step.setMinimumHeight(int(34 * fs))
        self.extract_start.setMinimumHeight(int(34 * fs))
        self.extract_end.setMinimumHeight(int(34 * fs))
        self.extract_audio_cb.setFont(QFont("Microsoft YaHei", max(8, int(11 * fs))))
        self.btn_extract.setMinimumHeight(int(48 * fs))
        self.btn_extract.setFont(QFont("Microsoft YaHei", max(8, int(13 * fs))))

        self.img_input.setMinimumHeight(int(34 * fs))
        self.audio_input.setMinimumHeight(int(34 * fs))
        self.btn_img_browse.setMinimumHeight(int(34 * fs))
        self.btn_audio_browse.setMinimumHeight(int(34 * fs))
        self.img_fps.setMinimumHeight(int(34 * fs))
        self.btn_img_to_video.setMinimumHeight(int(48 * fs))
        self.btn_img_to_video.setFont(QFont("Microsoft YaHei", max(8, int(13 * fs))))

        self.trim_start.setMinimumHeight(int(34 * fs))
        self.trim_end.setMinimumHeight(int(34 * fs))
        self.btn_trim.setMinimumHeight(int(48 * fs))
        self.btn_trim.setFont(QFont("Microsoft YaHei", max(8, int(13 * fs))))

        self.progress_bar.setMinimumHeight(int(28 * fs))
        self.log.setMaximumHeight(int(160 * fs))
        self.log.setFont(QFont("Consolas", max(7, int(11 * fs))))
        self.ui_zoom_combo.setFixedWidth(max(60, int(90 * fs)))

        self._apply_style(factor)

    def _scale_group_fonts(self, factor: float):
        for tab in [self.tab_info, self.tab_extract, self.tab_images, self.tab_trim]:
            for child in tab.findChildren(QGroupBox):
                child.setFont(QFont("Microsoft YaHei", max(8, int(12 * factor))))

    # ── 日志 / 进度 ─────────────────────────────────────

    def _log(self, msg: str):
        self.log.append(msg)

    def _set_busy(self, busy: bool):
        self.progress_bar.setVisible(busy)
        self.progress_bar.setValue(0)
        for btn in [self.btn_load, self.btn_info, self.btn_extract,
                     self.btn_img_to_video, self.btn_trim]:
            btn.setEnabled(not busy)

    # ── 拖拽 / 加载 ──────────────────────────────────────

    def _on_file_dropped(self, path: str):
        self.video_path = path
        self.processor.load_video(path)
        self._log(f"📥 拖入视频：{path}")
        self._on_video_loaded()

    def load_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频",
            filter="视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv);;所有文件 (*.*)",
        )
        if path:
            self.video_path = path
            self.processor.load_video(path)
            self._log(f"📂 加载视频：{path}")
            self._on_video_loaded()

    def _on_video_loaded(self):
        self.btn_info.setEnabled(True)
        self.btn_extract.setEnabled(True)
        self.btn_trim.setEnabled(True)
        self._update_thumbnail()
        self.show_info()

    # ── 缩略图 & 缩放 ────────────────────────────────────

    def _update_thumbnail(self):
        frame = self.processor.get_thumbnail()
        if frame is None:
            return
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self._original_pixmap = QPixmap.fromImage(qimg)
        self._apply_zoom()

    def _zoom_to(self, factor: float):
        self._zoom_factor = factor
        for f, btn in self._zoom_btns.items():
            btn.setChecked(f == factor)
        self._apply_zoom()

    def _apply_zoom(self):
        if self._original_pixmap is None:
            return
        if self._zoom_factor == -1:
            size = self.thumbnail.size()
            if size.width() <= 0 or size.height() <= 0:
                size = self.thumbnail.minimumSize()
            pixmap = self._original_pixmap.scaled(
                size, Qt.KeepAspectRatio, Qt.SmoothTransformation,
            )
        else:
            orig_w = self._original_pixmap.width()
            orig_h = self._original_pixmap.height()
            pixmap = self._original_pixmap.scaled(
                int(orig_w * self._zoom_factor),
                int(orig_h * self._zoom_factor),
                Qt.KeepAspectRatio, Qt.SmoothTransformation,
            )
        self.thumbnail.setPixmap(pixmap)

    def show_info(self):
        info = self.processor.get_info()
        if not info:
            self._log("⚠️ 未加载视频")
            return
        text = (
            f"<b>FPS：</b>{info['fps']:.2f}<br>"
            f"<b>总帧数：</b>{info['frame_count']}<br>"
            f"<b>分辨率：</b>{info['resolution']}<br>"
            f"<b>时长：</b>{info['duration']:.2f} 秒<br>"
            f"<b>路径：</b>{self.video_path}"
        )
        self.info_text.setText(text)
        self._log("✅ 已获取视频信息")

    # ── 拆帧（含音频）────────────────────────────────────

    def extract_frames(self):
        if not self.video_path:
            self._log("⚠️ 请先加载视频")
            return

        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if not dir_path:
            return

        step = self.extract_step.value()
        start = self.extract_start.value()
        end = self.extract_end.value() if self.extract_end.value() > 0 else None
        export_audio = self.extract_audio_cb.isChecked()

        if export_audio:
            # 先提取音频
            audio_path = os.path.join(dir_path, "audio.mp3")
            audio_result = self.processor.extract_audio(audio_path)
            self._log(audio_result)

        self._set_busy(True)
        self._log(f"🧩 开始拆帧 (间隔={step}, 起始={start}s)...")

        self.worker = Worker(
            self.processor.extract_frames, dir_path, step, start, end,
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_extract_done)
        self.worker.start()

    def _on_extract_done(self, msg: str):
        self._set_busy(False)
        self._log(msg)

    # ── 图片转视频（含音频）───────────────────────────────

    def _browse_img_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择图片目录")
        if path:
            self.img_input.setText(path)

    def _browse_audio_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件",
            filter="音频文件 (*.mp3 *.wav *.aac *.m4a *.ogg *.flac);;所有文件 (*.*)",
        )
        if path:
            self.audio_input.setText(path)

    def images_to_video(self):
        img_dir = self.img_input.text().strip()
        if not img_dir:
            self._log("⚠️ 请输入图片目录")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存视频", filter="MP4 (*.mp4)",
        )
        if not save_path:
            return

        audio_path = self.audio_input.text().strip() or None

        self._set_busy(True)
        fps = self.img_fps.value()
        msg = f"🎞️ 正在合成视频 (FPS={fps})"
        if audio_path:
            msg += f" + 音频"
        self._log(f"{msg}...")

        self.worker = Worker(
            self.processor.images_to_video,
            img_dir, save_path, fps, audio_path,
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_images_done)
        self.worker.start()

    def _on_images_done(self, msg: str):
        self._set_busy(False)
        self._log(msg)

    # ── 视频裁剪 ────────────────────────────────────────

    def trim_video(self):
        if not self.video_path:
            self._log("⚠️ 请先加载视频")
            return
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存裁剪视频", filter="MP4 (*.mp4)",
        )
        if not save_path:
            return
        start = self.trim_start.value()
        end = self.trim_end.value()
        if end <= start:
            self._log("⚠️ 结束时间必须大于起始时间")
            return
        self._set_busy(True)
        self._log(f"✂️ 正在裁剪 ({start}s → {end}s)...")
        self.worker = Worker(
            self.processor.trim_video, save_path, start, end,
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_trim_done)
        self.worker.start()

    def _on_trim_done(self, msg: str):
        self._set_busy(False)
        self._log(msg)

    def _on_progress(self, current: int, total: int):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
