from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QLabel,
    QFileDialog, QTextEdit, QHBoxLayout, QLineEdit
)
from video_processor import VideoProcessor


class VideoToolUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频处理工具")
        self.setGeometry(300, 200, 700, 500)

        self.processor = VideoProcessor()
        self.video_path = ""

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 按钮区
        btn_layout = QHBoxLayout()

        self.load_btn = QPushButton("加载视频")
        self.load_btn.clicked.connect(self.load_video)

        self.info_btn = QPushButton("显示信息")
        self.info_btn.clicked.connect(self.show_info)

        self.extract_btn = QPushButton("拆帧")
        self.extract_btn.clicked.connect(self.extract_frames)

        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.info_btn)
        btn_layout.addWidget(self.extract_btn)

        # 图片转视频
        self.img_input = QLineEdit()
        self.img_input.setPlaceholderText("图片文件夹路径")

        self.img_btn = QPushButton("图片转视频")
        self.img_btn.clicked.connect(self.images_to_video)

        img_layout = QHBoxLayout()
        img_layout.addWidget(self.img_input)
        img_layout.addWidget(self.img_btn)

        # 信息输出
        self.info_label = QLabel("未加载视频")

        # 日志
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        layout.addLayout(btn_layout)
        layout.addWidget(self.info_label)
        layout.addLayout(img_layout)
        layout.addWidget(self.log)

        self.setLayout(layout)

    def log_msg(self, msg):
        self.log.append(msg)

    def load_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择视频")
        if path:
            self.video_path = path
            self.processor.load_video(path)
            self.log_msg(f"加载视频：{path}")

    def show_info(self):
        info = self.processor.get_info()
        if not info:
            self.log_msg("未加载视频")
            return

        text = (
            f"FPS: {info['fps']}\n"
            f"帧数: {info['frame_count']}\n"
            f"分辨率: {info['resolution']}\n"
            f"时长: {info['duration']:.2f}s"
        )

        self.info_label.setText(text)
        self.log_msg("已获取视频信息")

    def extract_frames(self):
        if not self.video_path:
            self.log_msg("请先加载视频")
            return

        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            result = self.processor.extract_frames(dir_path)
            self.log_msg(result)

    def images_to_video(self):
        img_dir = self.img_input.text().strip()
        if not img_dir:
            self.log_msg("请输入图片路径")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "保存视频", filter="MP4 (*.mp4)")
        if save_path:
            result = self.processor.images_to_video(img_dir, save_path, fps=30)
            self.log_msg(result)