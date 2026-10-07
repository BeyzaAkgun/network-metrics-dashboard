from time import monotonic

import streamlit as st

from camera_controller import CameraController


def stop_camera() -> None:
    controller = st.session_state.pop("camera_controller", None)

    if controller is not None:
        controller.stop()

    st.session_state.pop("pending_gesture", None)


@st.fragment(run_every=0.2)
def camera_preview(controller: CameraController) -> None:
    if st.session_state.get("camera_controller") is not controller:
        return

    try:
        frame, gesture, hand_detected = controller.read()
    except Exception as exc:
        stop_camera()
        st.session_state["camera_error"] = str(exc)
        st.rerun()
        return

    st.image(
    frame,
    channels="BGR",
    output_format="JPEG",
    width=280,
)
    st.caption(
        "Hand detected" if hand_detected else "Show one hand to the camera."
    )

    if gesture is not None:
        st.session_state["pending_gesture"] = (gesture, monotonic())
        st.rerun()


def render_camera_panel() -> None:
    st.sidebar.header("Gesture control")

    enabled = st.sidebar.toggle(
        "Enable camera",
        value=False,
        key="camera_enabled",
    )

    if not enabled:
        stop_camera()
        st.session_state.pop("camera_error", None)
        st.sidebar.caption("Camera off. Mouse controls remain available.")
        return

    if "camera_error" in st.session_state:
        st.sidebar.error(st.session_state["camera_error"])
        st.sidebar.caption("Turn the camera off and on to retry.")
        return

    if "camera_controller" not in st.session_state:
        controller = CameraController()

        try:
            controller.start()
        except Exception as exc:
            st.session_state["camera_error"] = str(exc)
            st.sidebar.error(f"Unable to start camera: {exc}")
            st.sidebar.caption("Turn the camera off and on to retry.")
            return

        st.session_state["camera_controller"] = controller

    st.sidebar.caption(
        "Swipe right: next site. Swipe left: previous site. "
        "Pause briefly between gestures."
    )

    with st.sidebar:
        camera_preview(st.session_state["camera_controller"])