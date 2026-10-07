from pathlib import Path
from time import monotonic, monotonic_ns

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from gesture_control import SwipeDetector


MODEL_PATH = (
    Path(__file__).resolve().parent
    / "models"
    / "hand_landmarker.task"
)


class CameraController:
    def __init__(self) -> None:
        self.camera = None
        self.landmarker = None
        self.swipe_detector = SwipeDetector()
        self.last_timestamp_ms = -1

    def start(self) -> None:
        if self.camera is not None:
            return

        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(
                model_asset_path=str(MODEL_PATH)
            ),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        try:
            self.landmarker = (
                vision.HandLandmarker.create_from_options(options)
            )

            self.camera = cv2.VideoCapture(0)

            if not self.camera.isOpened():
                raise RuntimeError("Unable to open the camera.")

            self.swipe_detector = SwipeDetector()
            self.last_timestamp_ms = -1

        except Exception:
            self.stop()
            raise

    def read(self):
        if self.camera is None or self.landmarker is None:
            raise RuntimeError("The camera controller is not started.")

        success, frame = self.camera.read()

        if not success:
            raise RuntimeError("Unable to read a frame from the camera.")

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame,
        )

        timestamp_ms = max(
            monotonic_ns() // 1_000_000,
            self.last_timestamp_ms + 1,
        )
        self.last_timestamp_ms = timestamp_ms

        result = self.landmarker.detect_for_video(
            mp_image,
            timestamp_ms,
        )

        gesture = None
        hand_detected = bool(result.hand_landmarks)

        if hand_detected:
            landmarks = result.hand_landmarks[0]
            palm_indices = (0, 5, 9, 13, 17)

            palm_x = sum(
                landmarks[i].x for i in palm_indices
            ) / len(palm_indices)

            palm_y = sum(
                landmarks[i].y for i in palm_indices
            ) / len(palm_indices)

            gesture = self.swipe_detector.update(
                palm_x,
                palm_y,
                monotonic(),
            )

            height, width = frame.shape[:2]

            for landmark in landmarks:
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
        else:
            self.swipe_detector.reset()

        return frame, gesture, hand_detected

    def stop(self) -> None:
        try:
            if self.camera is not None:
                self.camera.release()
        finally:
            self.camera = None

            try:
                if self.landmarker is not None:
                    self.landmarker.close()
            finally:
                self.landmarker = None
                self.swipe_detector.reset()