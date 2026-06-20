# -*- coding: utf-8 -*-
"""视频处理核心模块 —— 基于 OpenCV + moviepy 的帧级与音频操作"""

import os
import cv2
from typing import Callable, Optional


class VideoProcessor:
    def __init__(self):
        self.video_path: Optional[str] = None
        self.cap: Optional[cv2.VideoCapture] = None

    # ── 基础操作 ─────────────────────────────────────────

    def load_video(self, path: str):
        self.video_path = path
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开视频: {path}")

    def get_info(self) -> Optional[dict]:
        if not self.cap:
            return None
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps else 0
        return {
            "fps": fps,
            "frame_count": frame_count,
            "resolution": f"{width}x{height}",
            "width": width,
            "height": height,
            "duration": duration,
        }

    def get_thumbnail(self) -> Optional[any]:
        if not self.cap:
            return None
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = self.cap.read()
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None

    # ── 拆帧 ─────────────────────────────────────────────

    def extract_frames(
        self,
        output_dir: str,
        step: int = 1,
        start_sec: float = 0,
        end_sec: Optional[float] = None,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        if not self.cap:
            return "错误：未加载视频"
        info = self.get_info()
        fps = info["fps"]
        total_frames = info["frame_count"]
        start_frame = int(start_sec * fps)
        end_frame = total_frames
        if end_sec is not None:
            end_frame = min(int(end_sec * fps), total_frames)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        os.makedirs(output_dir, exist_ok=True)
        idx = 0
        frame_pos = start_frame
        estimated_total = (end_frame - start_frame) // step
        while frame_pos < end_frame:
            ret, frame = self.cap.read()
            if not ret:
                break
            if (frame_pos - start_frame) % step == 0:
                filename = os.path.join(output_dir, f"{idx:06d}.png")
                cv2.imwrite(filename, frame)
                idx += 1
                if progress_cb:
                    progress_cb(idx, estimated_total)
            frame_pos += 1
        return f"完成拆帧：共导出 {idx} 帧 → {output_dir}"

    # ── 音频提取 ─────────────────────────────────────────

    def extract_audio(self, output_path: str) -> str:
        """从已加载的视频中提取音频"""
        if not self.video_path:
            return "错误：未加载视频"
        try:
            from moviepy import VideoFileClip
            clip = VideoFileClip(self.video_path)
            if clip.audio is None:
                clip.close()
                return "警告：视频中没有音频轨道"
            clip.audio.write_audiofile(output_path, logger=None)
            clip.close()
            return f"音频导出完成 → {output_path}"
        except Exception as e:
            return f"音频提取失败：{e}"

    # ── 视频裁剪 ─────────────────────────────────────────

    def trim_video(
        self,
        output_path: str,
        start_sec: float,
        end_sec: float,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        if not self.cap:
            return "错误：未加载视频"
        info = self.get_info()
        fps = info["fps"]
        width, height = info["width"], info["height"]
        start_frame = int(start_sec * fps)
        end_frame = int(end_sec * fps)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        total = end_frame - start_frame
        written = 0
        for i in range(total):
            ret, frame = self.cap.read()
            if not ret:
                break
            out.write(frame)
            written += 1
            if progress_cb and i % 10 == 0:
                progress_cb(written, total)
        out.release()
        return f"视频裁剪完成：{written} 帧 → {output_path}"

    # ── 图片转视频（支持可选音频）─────────────────────────

    def images_to_video(
        self,
        img_dir: str,
        output_path: str,
        fps: int = 30,
        audio_path: Optional[str] = None,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """将图片序列合成为 MP4 视频，可选混入音频"""
        images = sorted([
            f for f in os.listdir(img_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
        ])
        if not images:
            return "错误：目录中没有图片"

        first_img = cv2.imread(os.path.join(img_dir, images[0]))
        if first_img is None:
            return "错误：无法读取图片"
        height, width = first_img.shape[:2]

        # 先用 OpenCV 生成无声视频
        temp_video = output_path
        if audio_path and os.path.isfile(audio_path):
            # 生成为临时文件，后续混音
            temp_video = output_path.replace(".mp4", "_temp.mp4")

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
        total = len(images)
        for i, name in enumerate(images):
            frame = cv2.imread(os.path.join(img_dir, name))
            if frame is not None:
                out.write(frame)
            if progress_cb and i % 5 == 0:
                progress_cb(i + 1, total)
        out.release()

        # 如果有音频，用 moviepy 混音
        if audio_path and os.path.isfile(audio_path):
            try:
                from moviepy import VideoFileClip, AudioFileClip
                video = VideoFileClip(temp_video)
                audio = AudioFileClip(audio_path)
                # 截取音频到视频长度
                if audio.duration > video.duration:
                    audio = audio.subclipped(0, video.duration)
                final = video.with_audio(audio)
                final.write_videofile(output_path, logger=None, codec="libx264")
                video.close()
                audio.close()
                final.close()
                os.remove(temp_video)
                return f"视频+音频合成完成 → {output_path}"
            except Exception as e:
                # 混音失败，保留无声视频
                if os.path.exists(temp_video) and temp_video != output_path:
                    os.rename(temp_video, output_path)
                return f"视频生成完成（音频混入失败：{e}）→ {output_path}"

        return f"视频生成完成：{total} 帧 → {output_path}"

    def __del__(self):
        if self.cap:
            self.cap.release()
