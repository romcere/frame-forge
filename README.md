<div align="center">

# 🎬 FrameForge

**视频 ↔ 图片 双向帧处理桌面工具**

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green?logo=qt)](https://pypi.org/project/PyQt5/)
[![OpenCV](https://img.shields.io/badge/CV-OpenCV-red?logo=opencv)](https://pypi.org/project/opencv-python/)

</div>

---

## 📖 简介

FrameForge 是一款基于 PyQt5 + OpenCV 的桌面端视频帧处理工具，提供简洁直观的图形界面，帮助你轻松完成视频拆帧、图片合成视频、视频信息查看等常见操作。

## ✨ 功能

- **📂 加载视频** — 选择本地视频文件
- **📊 视频信息** — 查看 FPS、总帧数、分辨率、时长
- **🧩 拆帧导出** — 将视频逐帧导出为 PNG 图片序列
- **🎞️ 图片转视频** — 将 PNG/JPG 图片序列合成为 MP4 视频

## 🖼️ 界面预览

```
┌─────────────────────────────────────────┐
│          视频处理工具                     │
├─────────────────────────────────────────┤
│  [加载视频]  [显示信息]  [拆帧]           │
├─────────────────────────────────────────┤
│  FPS: 30  帧数: 1500  分辨率: 1920x1080  │
│  时长: 50.00s                            │
├─────────────────────────────────────────┤
│  [________________] [图片转视频]          │
├─────────────────────────────────────────┤
│  > 加载视频：C:/video.mp4                │
│  > 已获取视频信息                         │
│  > 完成拆帧，共 1500 帧                   │
└─────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.11
- pip

### 安装

```bash
# 克隆项目
git clone https://github.com/romcere/frame-forge.git
cd frame-forge

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 激活虚拟环境 (macOS/Linux)
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

## 📦 依赖

| 包 | 版本 | 用途 |
|------|---------|------|
| PyQt5 | 5.15.10 | GUI 界面 |
| opencv-python | 4.9.0.80 | 视频读写、帧处理 |
| numpy | 1.26.4 | 图像数据处理 |

## 📁 项目结构

```
viedo_tool/
├── main.py              # 入口，启动 GUI
├── ui.py                # PyQt5 界面逻辑
├── video_processor.py   # OpenCV 视频处理核心
└── requirements.txt     # 依赖清单
```

## 🛠️ 技术栈

- **GUI**: PyQt5
- **视频处理**: OpenCV (cv2)
- **数据处理**: NumPy

## 📝 待办

- [ ] 支持更多视频格式（AVI、MOV、MKV）输出
- [ ] 帧间隔采样（每隔 N 帧导出一张）
- [ ] 视频裁剪 / 缩放
- [ ] 批量处理多个视频
- [ ] 暗色主题切换

## 📄 License

MIT
