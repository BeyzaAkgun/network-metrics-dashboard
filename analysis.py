from math import isfinite
from pathlib import Path

import pandas as pd

from io import BytesIO

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DATA_PATH = BASE_DIR / "data" / "sample_metrics.csv"

REQUIRED_COLUMNS = {
    "timestamp",
    "site_id",
    "latency_ms",
    "download_mbps",
    "packet_loss_pct",
}

NUMERIC_COLUMNS = (
    "latency_ms",
    "download_mbps",
    "packet_loss_pct",
)

def validate_columns(df: pd.DataFrame) -> None:
    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        missing_names = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing_names}")

def validate_missing_values(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValueError("The CSV file contains no measurements.")

    required_data = df[sorted(REQUIRED_COLUMNS)]
    normalized_data = required_data.replace(r"^\s*$", pd.NA, regex=True)

    missing_counts = normalized_data.isna().sum()
    columns_with_missing = missing_counts[missing_counts > 0]

    if not columns_with_missing.empty:
        details = ", ".join(
            f"{column}: {count}"
            for column, count in columns_with_missing.items()
        )
        raise ValueError(f"Missing values in required columns: {details}")

def validate_numeric_values(df: pd.DataFrame) -> pd.DataFrame:
    validated_df = df.copy()

    for column in NUMERIC_COLUMNS:
        values = pd.to_numeric(validated_df[column], errors="coerce")

        invalid_values = values.isna() | values.isin(
            [float("inf"), float("-inf")]
        )

        if invalid_values.any():
            raise ValueError(
                f"Column '{column}' must contain only finite numbers. "
                f"Invalid values: {int(invalid_values.sum())}."
            )

        if (values < 0).any():
            raise ValueError(
                f"Column '{column}' must not contain negative values."
            )

        validated_df[column] = values

    if (validated_df["packet_loss_pct"] > 100).any():
        raise ValueError(
            "Column 'packet_loss_pct' must not contain values greater than 100."
        )

    return validated_df

def validate_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    validated_df = df.copy()

    timestamps = pd.to_datetime(
        validated_df["timestamp"],
        format="%Y-%m-%dT%H:%M:%S",
        errors="coerce",
    )

    invalid_timestamps = timestamps.isna()

    if invalid_timestamps.any():
        raise ValueError(
            "Column 'timestamp' contains invalid dates or unsupported formats. "
            "Expected format: YYYY-MM-DDTHH:MM:SS "
            "(example: 2026-10-05T10:00:00). "
            f"Invalid values: {int(invalid_timestamps.sum())}."
        )

    validated_df["timestamp"] = timestamps

    return validated_df

def load_metrics(file_path: str | Path | BytesIO) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError as exc:
        raise ValueError("The CSV file is empty.") from exc

    validate_columns(df)
    validate_missing_values(df)
    df = validate_numeric_values(df)
    df = validate_timestamps(df)

    df["site_id"] = df["site_id"].astype("string").str.strip()

    return df

def summarize_by_site(df: pd.DataFrame) -> pd.DataFrame:
    summary = df.groupby("site_id", as_index=False).agg(
        measurement_count=("timestamp", "size"),
        avg_latency_ms=("latency_ms", "mean"),
        avg_download_mbps=("download_mbps", "mean"),
        avg_packet_loss_pct=("packet_loss_pct", "mean"),
        flagged_count=("is_flagged", "sum"),
    )

    summary["flagged_pct"] = (
        summary["flagged_count"] / summary["measurement_count"] * 100
    )

    return summary

def validate_thresholds(
    *,
    latency_threshold: float,
    download_threshold: float,
    packet_loss_threshold: float,
) -> None:
    thresholds = {
        "latency_threshold": latency_threshold,
        "download_threshold": download_threshold,
        "packet_loss_threshold": packet_loss_threshold,
    }

    for name, value in thresholds.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"'{name}' must be a number.")

        if not isfinite(value):
            raise ValueError(f"'{name}' must be finite.")

        if value < 0:
            raise ValueError(f"'{name}' must be zero or greater.")

    if packet_loss_threshold > 100:
        raise ValueError(
            "'packet_loss_threshold' must not be greater than 100."
        )

def flag_measurements(
    df: pd.DataFrame,
    *,
    latency_threshold: float,
    download_threshold: float,
    packet_loss_threshold: float,
) -> pd.DataFrame:
    validate_thresholds(
        latency_threshold=latency_threshold,
        download_threshold=download_threshold,
        packet_loss_threshold=packet_loss_threshold,
    )

    flagged_df = df.copy()

    flagged_df["high_latency"] = (
        flagged_df["latency_ms"] > latency_threshold
    )
    flagged_df["low_download"] = (
        flagged_df["download_mbps"] < download_threshold
    )
    flagged_df["high_packet_loss"] = (
        flagged_df["packet_loss_pct"] > packet_loss_threshold
    )

    flagged_df["is_flagged"] = (
        flagged_df["high_latency"]
        | flagged_df["low_download"]
        | flagged_df["high_packet_loss"]
    )

    return flagged_df

if __name__ == "__main__":
    metrics = load_metrics(SAMPLE_DATA_PATH)

    flagged_metrics = flag_measurements(
        metrics,
        latency_threshold=100,
        download_threshold=30,
        packet_loss_threshold=2,
    )

    site_summary = summarize_by_site(flagged_metrics)
    issues = flagged_metrics[flagged_metrics["is_flagged"]]

    print("Summary by site:")
    print(site_summary.round(2).to_string(index=False))

    print("\nFlagged measurements:")
    print(issues.to_string(index=False))

    print(f"\nTotal measurements: {len(flagged_metrics)}")
    print(f"Flagged measurements: {len(issues)}")