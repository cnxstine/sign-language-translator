#!/usr/bin/env python3
"""
generate_synthetic_data.py - Synthetic Dataset Generator for Sign Language Translator

[Fidelity Status]: [Development Convenience / Testing Utility]
This script was NOT part of the original project. It is provided strictly for
pipeline validation, automated testing, and development convenience so that the
end-to-end data pipeline can be verified without a physical smart glove.

WARNING:
This synthetic generator does NOT represent the actual training dataset used
for the original project. The gestures generated here are simplified mathematical
templates (placeholders) based on physical estimations of joint angles and hand
orientations. They should not be presented as the original data.
"""

import argparse
import csv
import logging
import os
import sys

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Column names
COLUMNS = [
    "flex1", "flex2", "flex3", "flex4", "flex5",
    "ax", "ay", "az",
    "gx", "gy", "gz",
    "label",
]

# [Development Convenience] Template Gesture Profiles:
# These profiles represent base sensor values for 10 mock gestures.
# They are placeholder profiles for pipeline verification only.
GESTURE_PROFILES = {
    "A": {
        "flex":  [820, 850, 830, 810, 650],
        "accel": [2000, -8000, 12000],
        "gyro":  [10, -5, 8],
    },
    "B": {
        "flex":  [150, 130, 140, 160, 580],
        "accel": [1500, -9000, 11000],
        "gyro":  [-5, 10, -3],
    },
    "C": {
        "flex":  [450, 480, 470, 440, 400],
        "accel": [3000, -7500, 11500],
        "gyro":  [8, -8, 5],
    },
    "D": {
        "flex":  [160, 780, 800, 790, 620],
        "accel": [1800, -8500, 12500],
        "gyro":  [-3, 6, -7],
    },
    "F": {
        "flex":  [420, 150, 140, 130, 380],
        "accel": [2200, -8200, 11800],
        "gyro":  [5, -10, 4],
    },
    "I": {
        "flex":  [810, 830, 820, 170, 700],
        "accel": [2500, -7800, 12200],
        "gyro":  [-8, 3, -6],
    },
    "L": {
        "flex":  [170, 820, 810, 800, 200],
        "accel": [1600, -9200, 11200],
        "gyro":  [7, -4, 9],
    },
    "V": {
        "flex":  [160, 150, 790, 810, 680],
        "accel": [1900, -8800, 12000],
        "gyro":  [-6, 8, -4],
    },
    "W": {
        "flex":  [150, 140, 160, 780, 660],
        "accel": [2100, -8600, 11600],
        "gyro":  [4, -7, 6],
    },
    "Y": {
        "flex":  [800, 820, 810, 180, 190],
        "accel": [2800, -7600, 12400],
        "gyro":  [-4, 5, -8],
    },
}

# Standard deviations for Gaussian noise (per sensor type)
NOISE_STD = {
    "flex":  40.0,    # Flex sensor noise (ADC units)
    "accel": 800.0,   # Accelerometer noise (raw units)
    "gyro":  30.0,    # Gyroscope noise (raw units)
}


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic sensor data for ASL gesture recognition."
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=200,
        help="Number of samples to generate per gesture (default: 200)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="dataset/synthetic_data.csv",
        help="Output CSV file path (default: dataset/synthetic_data.csv)",
    )
    parser.add_argument(
        "--noise-level",
        type=float,
        default=1.0,
        help="Noise multiplier, higher = more noisy data (default: 1.0)",
    )
    return parser.parse_args()


def generate_gesture_samples(gesture, profile, num_samples, noise_level, rng):
    """
    Generate synthetic sensor samples for a single gesture.
    """
    flex_base = np.array(profile["flex"], dtype=float)
    accel_base = np.array(profile["accel"], dtype=float)
    gyro_base = np.array(profile["gyro"], dtype=float)

    # Generate noisy samples
    flex_noise = rng.normal(0, NOISE_STD["flex"] * noise_level, size=(num_samples, 5))
    accel_noise = rng.normal(0, NOISE_STD["accel"] * noise_level, size=(num_samples, 3))
    gyro_noise = rng.normal(0, NOISE_STD["gyro"] * noise_level, size=(num_samples, 3))

    flex_samples = flex_base + flex_noise
    accel_samples = accel_base + accel_noise
    gyro_samples = gyro_base + gyro_noise

    # Clamp sensor values to valid physically possible ranges
    # ESP32 ADC: 12-bit range (0-4095).
    # Since our template flex values are designed around 0-1023 range, clamp to [0, 4095].
    flex_samples = np.clip(flex_samples, 0, 4095)

    # Clamp accelerometer and gyroscope
    accel_samples = np.clip(accel_samples, -32768, 32767)
    gyro_samples = np.clip(gyro_samples, -32768, 32767)

    # Round to integers to simulate raw ADC/IMU digits
    flex_samples = np.round(flex_samples).astype(int)
    accel_samples = np.round(accel_samples).astype(int)
    gyro_samples = np.round(gyro_samples).astype(int)

    # Combine all sensor values
    samples = np.hstack([flex_samples, accel_samples, gyro_samples])

    return samples


def main():
    """Main synthetic data generation pipeline."""
    args = parse_args()

    print("=" * 60)
    print("  [DEVELOPMENT UTILITY] Synthetic Data Generator")
    print("=" * 60)
    print("  WARNING: This script generates placeholder data for pipeline")
    print("  validation and testing only. It is NOT the original dataset.")
    print("=" * 60)
    print(f"  Samples per gesture: {args.samples}")
    print(f"  Total samples:       {args.samples * len(GESTURE_PROFILES)}")
    print(f"  Noise level:         {args.noise_level:.1f}x")
    print(f"  Output file:         {args.output}")
    print(f"  Mock Gestures:       {', '.join(sorted(GESTURE_PROFILES.keys()))}")
    print("=" * 60)

    rng = np.random.default_rng(seed=42)

    all_rows = []
    for gesture in sorted(GESTURE_PROFILES.keys()):
        profile = GESTURE_PROFILES[gesture]
        samples = generate_gesture_samples(
            gesture, profile, args.samples, args.noise_level, rng
        )

        for sample in samples:
            # Format raw sensor values:
            # We divide raw accelerometer by 16384.0 and gyroscope by 131.0
            # to match the units sent by the ESP32 firmware:
            flex_vals = sample[:5]
            ax, ay, az = sample[5:8] / 16384.0
            gx, gy, gz = sample[8:11] / 131.0
            
            row = (
                list(flex_vals) +
                [round(ax, 3), round(ay, 3), round(az, 3)] +
                [round(gx, 3), round(gy, 3), round(gz, 3)] +
                [gesture]
            )
            all_rows.append(row)

        logger.info(
            "Generated %d mock samples for gesture '%s'",
            args.samples,
            gesture,
        )

    # Shuffle the dataset
    rng.shuffle(all_rows)

    # Save to CSV
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(args.output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(all_rows)

    file_size = os.path.getsize(args.output)
    logger.info("Saved synthetic dataset to: %s (%.1f KB)", args.output, file_size / 1024)
    print()


if __name__ == "__main__":
    main()
