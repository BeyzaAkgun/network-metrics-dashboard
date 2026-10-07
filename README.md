# Network Metrics Dashboard

A Python dashboard for validating network measurement CSV files,
analyzing performance against adjustable thresholds, and exporting reports.

The application includes optional hand-gesture navigation between
measurement sites using OpenCV and MediaPipe.

## Features

- Load the built-in simulated dataset or upload a CSV file.
- Validate required columns, missing values, numeric ranges, and timestamps.
- Calculate measurement counts and average metrics for each site.
- Flag high latency, low download speed, and high packet loss.
- Explore per-site time-series charts.
- Export summaries and flagged measurements as CSV files.
- Navigate between sites using a dropdown, buttons, or hand gestures.
- Enable or disable camera control from the sidebar.

## Technology

- Python
- Pandas
- Streamlit
- OpenCV
- MediaPipe Hand Landmarker

The application uses a pretrained MediaPipe model.
Custom code handles swipe detection, cooldowns, dashboard navigation,
data validation, analysis, and reporting.

## Data format

Use a UTF-8, comma-separated CSV with these required columns:

```csv
timestamp,site_id,latency_ms,download_mbps,packet_loss_pct
2026-10-05T10:00:00,SITE_A,35,85,0.2
2026-10-05T10:01:00,SITE_A,120,18,3.5
```

Validation rules:

- All required fields must be present and non-empty.
- Measurement values must be finite numbers.
- Latency and download speed must be zero or greater.
- Packet loss must be between 0 and 100, inclusive.
- Timestamps must follow `YYYY-MM-DDTHH:MM:SS`.
- Timestamps are assumed to use the same time zone.
- Leading and trailing whitespace is removed from site identifiers.

## Setup on Windows PowerShell

Developed locally using Python 3.12.

Open a terminal in the project directory.

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

### Optional camera model

To use gesture control, download the pretrained
[MediaPipe Hand Landmarker model](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task).

Create a `models` directory and save the file as:

```text
models/hand_landmarker.task
```

The model file is excluded from Git.
CSV analysis and mouse navigation can be used with the camera disabled.

## Run

```powershell
python -m streamlit run app.py
```

Open the Local URL printed in the terminal.

## Usage

1. Use the built-in simulated dataset or upload a CSV.
2. Adjust the demo thresholds in the sidebar.
3. Select a measurement site.
4. Review the metric cards, charts, and flagged measurements.
5. Download the reports.

Default flagging rules:

| Metric | Condition |
|---|---|
| Latency | Greater than 100 ms |
| Download speed | Less than 30 Mbps |
| Packet loss | Greater than 2% |

Values equal to a threshold are not flagged by that rule.
A measurement is flagged if at least one condition is met.

These are configurable demo thresholds, not telecom standards.
Flags indicate threshold violations, not the cause of an issue.

## Reports

Both reports include all sites, the current thresholds, and the data source.
The selected site does not restrict the exports.

- `site_summary.csv`: measurement counts, averages, flagged counts,
  and flagged percentages per site.
- `flagged_measurements.csv`: measurements that violate at least one
  threshold, with separate Boolean flags for each condition.

Summary floating-point values are exported to two decimal places.
Flagged measurement values are not explicitly rounded during export.

## Gesture control

Enable the camera from the sidebar and show one hand.

- Swipe right in the mirrored preview to select the next site.
- Swipe left to select the previous site.
- Navigation wraps between the first and last sites.
- Pause briefly between gestures.

The detector uses recent palm positions, a minimum horizontal
displacement, a vertical-motion check, and a cooldown.
Its settings are defined in `gesture_control.py`.

Turn the camera off before closing the browser tab.
Mouse controls remain available when the camera is disabled.

### Local camera limitation

OpenCV accesses the camera of the computer running the Python process.
This version is intended for a local, single-user demo.

Deploying the app to a remote server does not provide access to the
visitor's webcam. Browser-based camera capture would require a
different integration.

The application does not implement video recording or camera uploads.

## Project structure

```text
network-metrics-dashboard/
├── app.py
├── analysis.py
├── camera_controller.py
├── camera_panel.py
├── gesture_control.py
├── camera_test.py
├── hand_tracking.py
├── controller_test.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   └── sample_metrics.csv
└── models/
    └── hand_landmarker.task
```

The camera test scripts are manual prototypes, not an automated test suite.

## Manual checks

- Valid CSV loads and produces the expected summaries.
- Missing columns, empty values, invalid numbers, and invalid dates
  are rejected.
- Invalid threshold values are rejected.
- Uploaded files can be removed to return to the built-in dataset.
- Changing thresholds updates flags without changing measurement averages.
- Site selection updates cards, charts, and the issue table.
- CSV exports contain all sites and the configured thresholds.
- Left and right swipes change the selected site.
- Disabling the camera preserves mouse navigation.

With the built-in dataset and default thresholds, the expected result is
15 measurements across 3 sites, with 5 flagged measurements.

## Limitations

- The built-in measurements are simulated.
- The application does not diagnose network root causes.
- Duplicate measurements are not automatically removed.
- Gesture reliability depends on lighting, framing, camera speed,
  and movement.
- Camera cleanup on an unexpected browser disconnect is not implemented.