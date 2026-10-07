from camera_controller import CameraController


controller = CameraController()

try:
    controller.start()
    frame, gesture, hand_detected = controller.read()

    print("Frame shape:", frame.shape)
    print("Hand detected:", hand_detected)
    print("Gesture:", gesture)
finally:
    controller.stop()
    print("Controller stopped.")