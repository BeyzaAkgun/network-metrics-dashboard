import cv2


def main() -> None:
    camera = cv2.VideoCapture(0)

    try:
        if not camera.isOpened():
            print("Unable to open the camera.")
            return

        print("Camera started. Focus the camera window and press Q to quit.")

        while True:
            success, frame = camera.read()

            if not success:
                print("Unable to read a frame from the camera.")
                break

            frame = cv2.flip(frame, 1)

            cv2.imshow("Camera Test - Press Q to quit", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == ord("Q"):
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Camera released.")


if __name__ == "__main__":
    main()