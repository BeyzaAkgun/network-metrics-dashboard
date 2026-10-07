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


def main() -> None:
    if not MODEL_PATH.is_file():
        print(f"Model file not found: {MODEL_PATH}")
        return

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

    with vision.HandLandmarker.create_from_options(options) as landmarker:
        camera = cv2.VideoCapture(0)

        try:
            if not camera.isOpened():
                print("Unable to open the camera.")
                return

            print("Hand tracking started. Press Q in the camera window to quit.")
            last_timestamp_ms = -1
            swipe_detector = SwipeDetector()
            gesture_message = ""
            gesture_visible_until = 0.0

            while True:
                success, frame = camera.read()

                if not success:
                    print("Unable to read a frame from the camera.")
                    break

                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb_frame,
                )

                timestamp_ms = max(
                    monotonic_ns() // 1_000_000,
                    last_timestamp_ms + 1,
                )
                last_timestamp_ms = timestamp_ms

                result = landmarker.detect_for_video(
                    mp_image,
                    timestamp_ms,
                )

                now = monotonic()

                if result.hand_landmarks:
                    landmarks = result.hand_landmarks[0]
                    palm_indices = (0, 5, 9, 13, 17)

                    palm_x = sum(
                        landmarks[i].x for i in palm_indices
                    ) / len(palm_indices)

                    palm_y = sum(
                        landmarks[i].y for i in palm_indices
                    ) / len(palm_indices)

                    gesture = swipe_detector.update(palm_x, palm_y, now)

                    cv2.putText(
                        frame,
                        f"Palm x: {palm_x:.2f} | Samples: {len(swipe_detector.positions)}",
                        (20, 105),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2,
                    )

                    if gesture is not None:
                        gesture_message = f"Swipe {gesture}"
                        gesture_visible_until = now + 0.8
                        print(gesture_message)
                else:
                    swipe_detector.reset()

                height, width = frame.shape[:2]

                for hand_landmarks in result.hand_landmarks:
                    for landmark in hand_landmarks:
                        x = int(landmark.x * width)
                        y = int(landmark.y * height)

                        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

                status = (
                    "Hand detected"
                    if result.hand_landmarks
                    else "No hand detected"
                )

                cv2.putText(
                    frame,
                    status,
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )

                if now < gesture_visible_until:
                    cv2.putText(
                        frame,
                        gesture_message,
                        (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 255),
                        2,
                    )

                cv2.imshow("Hand Tracking - Press Q to quit", frame)

                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q")):
                    break

        finally:
            camera.release()
            cv2.destroyAllWindows()
            print("Camera released.")


if __name__ == "__main__":
    main()