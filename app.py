import streamlit as st

from analysis import (
    SAMPLE_DATA_PATH,
    flag_measurements,
    load_metrics,
    summarize_by_site,
)

from time import monotonic

from camera_panel import render_camera_panel, stop_camera

def change_site(direction: int, sites: list[str]) -> None:
    if not sites:
        return

    current_site = st.session_state.get("selected_site")

    if current_site not in sites:
        st.session_state["selected_site"] = sites[0]
        return

    current_index = sites.index(current_site)
    next_index = (current_index + direction) % len(sites)

    st.session_state["selected_site"] = sites[next_index]


st.set_page_config(
    page_title="Network Metrics Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Network Metrics Dashboard")
st.info(
    "Demo application with user-defined thresholds. "
    "The built-in dataset is simulated. "
    "Threshold flags do not identify the cause of a performance issue."
)

st.sidebar.header("Data source")

uploaded_file = st.sidebar.file_uploader(
    "Upload a measurements CSV",
    type=["csv"],
    help=(
        "Use a UTF-8, comma-separated CSV with columns: "
        "timestamp, site_id, latency_ms, download_mbps, packet_loss_pct."
    ),
)

if uploaded_file is None:
    source_label = "Built-in simulated dataset"
else:
    source_label = f"Uploaded CSV: {uploaded_file.name}"

st.sidebar.caption(source_label)

st.sidebar.header("Demo thresholds")
st.sidebar.caption("Applied to all measurement sites.")

latency_threshold = st.sidebar.number_input(
    "Latency upper threshold (ms)",
    min_value=0.0,
    value=100.0,
    step=10.0,
    help="Flag measurements with latency strictly above this value.",
)

download_threshold = st.sidebar.number_input(
    "Download lower threshold (Mbps)",
    min_value=0.0,
    value=30.0,
    step=5.0,
    help="Flag measurements with download speed strictly below this value.",
)

packet_loss_threshold = st.sidebar.number_input(
    "Packet loss upper threshold (%)",
    min_value=0.0,
    max_value=100.0,
    value=2.0,
    step=0.5,
    help="Flag measurements with packet loss strictly above this value.",
)

render_camera_panel()

try:
    if uploaded_file is None:
        metrics = load_metrics(SAMPLE_DATA_PATH)
    else:
        uploaded_file.seek(0)
        metrics = load_metrics(uploaded_file)

    flagged_metrics = flag_measurements(
        metrics,
        latency_threshold=latency_threshold,
        download_threshold=download_threshold,
        packet_loss_threshold=packet_loss_threshold,
    )

except (ValueError, OSError) as exc:
    stop_camera()
    st.error(f"Unable to analyze the dataset: {exc}")
    st.stop()

site_summary = summarize_by_site(flagged_metrics)

st.sidebar.header("Controls")

site_options = sorted(flagged_metrics["site_id"].unique().tolist())

if st.session_state.get("selected_site") not in site_options:
    st.session_state["selected_site"] = site_options[0]

pending_gesture = st.session_state.pop("pending_gesture", None)

if pending_gesture is not None:
    gesture, detected_at = pending_gesture

    if monotonic() - detected_at <= 2.0 and len(site_options) > 1:
        direction = 1 if gesture == "right" else -1
        change_site(direction, site_options)

        st.toast(
            f"Swipe {gesture}: {st.session_state['selected_site']}"
        )

selected_site = st.sidebar.selectbox(
    "Measurement site",
    options=site_options,
    key="selected_site",
)

previous_col, next_col = st.sidebar.columns(2)

with previous_col:
    st.button(
        "Previous site",
        on_click=change_site,
        args=(-1, site_options),
        disabled=len(site_options) < 2,
    )

with next_col:
    st.button(
        "Next site",
        on_click=change_site,
        args=(1, site_options),
        disabled=len(site_options) < 2,
    )

selected_metrics = flagged_metrics[
    flagged_metrics["site_id"] == selected_site
].copy()

issues = selected_metrics[selected_metrics["is_flagged"]]

st.subheader(f"Overview — {selected_site}")
st.caption(f"Selected measurement site · {source_label}")

latency_col, download_col, loss_col, flagged_col = st.columns(4)

latency_col.metric(
    "Average latency",
    f"{selected_metrics['latency_ms'].mean():.1f} ms",
)
download_col.metric(
    "Average download speed",
    f"{selected_metrics['download_mbps'].mean():.1f} Mbps",
)
loss_col.metric(
    "Average packet loss",
    f"{selected_metrics['packet_loss_pct'].mean():.2f}%",
)
flagged_col.metric(
    "Flagged measurements",
    f"{len(issues)} / {len(selected_metrics)}",
)

st.subheader(f"Measurements over time — {selected_site}")

chart_data = selected_metrics.sort_values("timestamp")

latency_chart, download_chart, loss_chart = st.columns(3)

with latency_chart:
    st.markdown("**Latency**")
    st.line_chart(
        chart_data,
        x="timestamp",
        y="latency_ms",
        x_label="Time",
        y_label="Latency (ms)",
        color="#2563EB",
        height=260,
    )

with download_chart:
    st.markdown("**Download speed**")
    st.line_chart(
        chart_data,
        x="timestamp",
        y="download_mbps",
        x_label="Time",
        y_label="Download speed (Mbps)",
        color="#16A34A",
        height=260,
    )

with loss_chart:
    st.markdown("**Packet loss**")
    st.line_chart(
        chart_data,
        x="timestamp",
        y="packet_loss_pct",
        x_label="Time",
        y_label="Packet loss (%)",
        color="#EA580C",
        height=260,
    )

st.subheader("Summary by site — all sites")
st.dataframe(
    site_summary.round(2),
    hide_index=True,
    width="stretch",
)

st.subheader(f"Flagged measurements — {selected_site}")
st.caption(
    f"Demo thresholds: latency > {latency_threshold:g} ms · "
    f"download speed < {download_threshold:g} Mbps · "
    f"packet loss > {packet_loss_threshold:g}%"
)

if issues.empty:
    st.success("No measurements exceed the configured demo thresholds.")
else:
    st.dataframe(
        issues,
        hide_index=True,
        width="stretch",
    )

st.subheader("Download reports")
st.caption(
    "Reports include all sites and use the current demo thresholds. "
    "The measurement site selection does not limit the exports."
)

summary_report = site_summary.copy()

flagged_report = flagged_metrics[
    flagged_metrics["is_flagged"]
].copy()

flagged_report = flagged_report.sort_values(
    ["site_id", "timestamp"]
)

for report in (summary_report, flagged_report):
    report["latency_threshold_ms"] = latency_threshold
    report["download_threshold_mbps"] = download_threshold
    report["packet_loss_threshold_pct"] = packet_loss_threshold
    report["data_source"] = source_label

summary_csv = summary_report.to_csv(
    index=False,
    float_format="%.2f",
).encode("utf-8-sig")

flagged_csv = flagged_report.to_csv(
    index=False,
    date_format="%Y-%m-%dT%H:%M:%S",
).encode("utf-8-sig")

summary_download, flagged_download = st.columns(2)

with summary_download:
    st.download_button(
        label="Download site summary CSV",
        data=summary_csv,
        file_name="site_summary.csv",
        mime="text/csv",
        on_click="ignore",
    )

with flagged_download:
    st.download_button(
        label="Download flagged measurements CSV",
        data=flagged_csv,
        file_name="flagged_measurements.csv",
        mime="text/csv",
        on_click="ignore",
    )