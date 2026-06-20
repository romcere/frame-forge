import cv2
import os


class VideoProcessor:
    def __init__(self):
        self.video_path = None
        self.cap = None

    def load_video(self, path):
        self.video_path = path
        self.cap = cv2.VideoCapture(path)

    def get_info(self):
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
            "duration": duration
        }

    def extract_frames(self, output_dir):
        if not self.cap:
            return "未加载视频"

        os.makedirs(output_dir, exist_ok=True)

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        idx = 0
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            filename = os.path.join(output_dir, f"{idx:06d}.png")
            cv2.imwrite(filename, frame)
            idx += 1

        return f"完成拆帧，共 {idx} 帧"

    def images_to_video(self, img_dir, output_path, fps=30):
        images = sorted([
            img for img in os.listdir(img_dir)
            if img.endswith((".png", ".jpg", ".jpeg"))
        ])

        if not images:
            return "没有图片"

        first_img = cv2.imread(os.path.join(img_dir, images[0]))
        height, width, _ = first_img.shape

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        for img_name in images:
            img_path = os.path.join(img_dir, img_name)
            frame = cv2.imread(img_path)
            out.write(frame)

        out.release()
        return f"视频生成完成：{output_path}"