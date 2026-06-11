#!/usr/bin/env python3
"""
collect_data.py - Sensor Data Collection for Sign Language Translator

[Fidelity Status]: Matches the original project report codebase logic.

Connects to the ESP32 Smart Glove via Bluetooth Serial and records real-time
sensor data. Labeled samples are appended to a CSV file.

Original Code Features:
    - 11 sensor values: 5 flex sensors + 3-axis accelerometer + 3-axis gyroscope
    - Labeled gesture data collection
    - Gesture-agnostic input (no hardcoded alphabet constraint)
    - Exit on typing "EXIT"

Development Conveniences (Clearly Labeled):
    - [Development Convenience]: argparse interface for port, samples, and output file path.
    - [Development Convenience]: Inline terminal progress bar and countdown timer.
    - [Development Convenience]: Basic data format validation during real-time capture.
"""

import argparse
import csv
import logging
import os
import sys
import time
import serial

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Sensor column names (Standardized dataset structure)
SENSOR_COLUMNS = [
    "flex1", "flex2", "flex3", "flex4", "flex5",
    "ax", "ay", "az",
    "gx", "gy", "gz",
]
NUM_SENSORS = len(SENSOR_COLUMNS)

def parse_args():
    """
    [Development Convenience]
    Parse command-line arguments for port, samples, and output file.
    """
    parser = argparse.ArgumentParser(
        description="Collect sensor data from ESP32 for gesture recognition training."
    )
    parser.add_argument(
        "--port",
        type=str,
        default="/dev/rfcomm0",
        help="Bluetooth serial port (default: /dev/rfcomm0)",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=120,
        help="Number of samples to record per gesture (default: 120)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="dataset/gesture_data.csv",
        help="Output CSV file path (default: dataset/gesture_data.csv)",
    )
    return parser.parse_args()


def connect_serial(port, baudrate=115200, timeout=1):
    """
    Establish serial connection to the ESP32.
    Matches the original serial settings from the report.
    """
    try:
        ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        time.sleep(1)  # Stabilize connection
        ser.reset_input_buffer()
        logger.info("Connected to %s at %d baud.", port, baudrate)
        return ser
    except serial.SerialException as e:
        logger.error("Failed to connect to %s: %s", port, e)
        sys.exit(1)


def validate_sensor_line(line):
    """
    [Development Convenience]
    Validate and parse a line of sensor data from the ESP32.
    Expects 11 comma-separated numeric values.
    """
    line = line.strip()
    if not line:
        return None

    parts = line.split(",")
    if len(parts) != NUM_SENSORS:
        return None

    values = []
    for part in parts:
        try:
            values.append(float(part.strip()))
        except ValueError:
            return None

    return values


def print_progress_bar(current, total, bar_length=40):
    """[Development Convenience] Print an inline progress bar to the terminal."""
    fraction = current / total
    filled = int(bar_length * fraction)
    bar = "█" * filled + "░" * (bar_length - filled)
    percent = fraction * 100
    sys.stdout.write(f"\r  [{bar}] {current}/{total} ({percent:.0f}%)")
    sys.stdout.flush()


def countdown(seconds=3):
    """[Development Convenience] Display a countdown before recording starts."""
    print("  Get ready...")
    for i in range(seconds, 0, -1):
        print(f"  Starting in {i}...", end="\r")
        time.sleep(1)
    print("  Recording NOW!       ")


def record_samples(ser, label, num_samples):
    """
    Record a set of labeled sensor samples from Bluetooth Serial.
    Fidelity is matched to original data acquisition logic.
    """
    samples = []
    invalid_count = 0

    countdown()

    while len(samples) < num_samples:
        try:
            raw = ser.readline().decode("utf-8", errors="replace")
        except serial.SerialException as e:
            logger.warning("Serial read error: %s", e)
            continue

        values = validate_sensor_line(raw)
        if values is None:
            invalid_count += 1
            continue

        samples.append(values + [label])
        print_progress_bar(len(samples), num_samples)

    print()  # newline after progress bar
    if invalid_count > 0:
        logger.info("Skipped %d invalid lines during recording.", invalid_count)

    return samples


def save_to_csv(samples, output_path):
    """
    Save or append samples to the CSV file.
    Creates directories and headers if they do not exist.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    file_exists = os.path.isfile(output_path) and os.path.getsize(output_path) > 0
    mode = "a" if file_exists else "w"

    with open(output_path, mode, newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            # Write header row matching the original dataset structure
            writer.writerow(SENSOR_COLUMNS + ["label"])
        writer.writerows(samples)

    logger.info(
        "Saved %d samples to %s (%s).",
        len(samples),
        output_path,
        "appended" if file_exists else "created",
    )


def main():
    """Main data collection loop."""
    args = parse_args()

    print("=" * 60)
    print("  Sign Language Gesture Data Collector")
    print("=" * 60)
    print(f"  Port:    {args.port}")
    print(f"  Samples: {args.samples} per gesture")
    print(f"  Output:  {args.output}")
    print("  Gestures: Gesture-agnostic (Type any custom label to record)")
    print("=" * 60)

    ser = connect_serial(args.port)

    try:
        while True:
            print()
            # Prompt matching original report: uppercase label, check for EXIT
            label = input("Enter label (or EXIT): ").strip().upper()

            if label == "EXIT":
                print("Exiting data collection.")
                break

            if not label:
                print("  Label cannot be empty.")
                continue

            print(f"  Recording {args.samples} samples for gesture '{label}'...")
            samples = record_samples(ser, label, args.samples)
            save_to_csv(samples, args.output)

            print(f"  Successfully recorded {len(samples)} samples for '{label}'.")

    except KeyboardInterrupt:
        print("\n\nData collection interrupted by user.")
    finally:
        ser.close()
        logger.info("Serial connection closed.")

    # Print summary of dataset
    if os.path.isfile(args.output):
        try:
            import pandas as pd
            df = pd.read_csv(args.output)
            print("\n--- Dataset Summary ---")
            print(f"  Total samples: {len(df)}")
            print("  Samples per label:")
            for label, count in df["label"].value_counts().sort_index().items():
                print(f"    {label}: {count}")
            print()
        except Exception:
            pass


if __name__ == "__main__":
    main()
