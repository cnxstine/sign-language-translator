#!/usr/bin/env python3
"""
clean_dataset.py - Dataset Cleaning for Sign Language Translator

Cleans the raw sensor dataset by removing missing values, duplicates,
and statistical outliers using the IQR method.

Usage:
    python clean_dataset.py
    python clean_dataset.py --input dataset/gesture_data.csv --output dataset/gesture_data_clean.csv
"""

import argparse
import logging
import os
import sys

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Sensor feature columns (exclude 'label')
FEATURE_COLUMNS = [
    "flex1", "flex2", "flex3", "flex4", "flex5",
    "ax", "ay", "az",
    "gx", "gy", "gz",
]


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Clean the gesture sensor dataset by removing NaN, duplicates, and outliers."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="dataset/gesture_data.csv",
        help="Input raw dataset CSV (default: dataset/gesture_data.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="dataset/gesture_data_clean.csv",
        help="Output cleaned dataset CSV (default: dataset/gesture_data_clean.csv)",
    )
    return parser.parse_args()


def load_dataset(filepath):
    """
    Load the raw CSV dataset.

    Args:
        filepath: Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded dataset.

    Raises:
        SystemExit: If the file cannot be loaded.
    """
    if not os.path.isfile(filepath):
        logger.error("Dataset file not found: %s", filepath)
        sys.exit(1)

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        logger.error("Failed to read dataset: %s", e)
        sys.exit(1)

    # Validate expected columns
    expected = FEATURE_COLUMNS + ["label"]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        logger.error("Missing columns in dataset: %s", missing)
        sys.exit(1)

    logger.info("Loaded dataset: %s (%d rows, %d columns)", filepath, len(df), len(df.columns))
    return df


def remove_missing_values(df):
    """
    Remove rows with missing or NaN values.

    Args:
        df: Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with missing rows removed.
        int: Number of rows removed.
    """
    initial = len(df)
    df_clean = df.dropna()
    removed = initial - len(df_clean)
    if removed > 0:
        logger.info("Removed %d rows with missing values.", removed)
    else:
        logger.info("No missing values found.")
    return df_clean, removed


def remove_duplicates(df):
    """
    Remove duplicate rows.

    Args:
        df: Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with duplicates removed.
        int: Number of rows removed.
    """
    initial = len(df)
    df_clean = df.drop_duplicates()
    removed = initial - len(df_clean)
    if removed > 0:
        logger.info("Removed %d duplicate rows.", removed)
    else:
        logger.info("No duplicate rows found.")
    return df_clean, removed


def remove_outliers_iqr(df, multiplier=1.5):
    """
    Remove outliers using the Interquartile Range (IQR) method.

    For each numeric feature column, values outside the range
    [Q1 - 1.5*IQR, Q3 + 1.5*IQR] are considered outliers.
    Outlier detection is applied per label group to preserve
    gesture-specific value ranges.

    Args:
        df: Input DataFrame.
        multiplier: IQR multiplier for outlier bounds (default: 1.5).

    Returns:
        pd.DataFrame: DataFrame with outlier rows removed.
        int: Number of rows removed.
    """
    initial = len(df)
    mask = pd.Series(True, index=df.index)

    for label in df["label"].unique():
        label_mask = df["label"] == label
        label_data = df.loc[label_mask, FEATURE_COLUMNS]

        Q1 = label_data.quantile(0.25)
        Q3 = label_data.quantile(0.75)
        IQR = Q3 - Q1

        lower = Q1 - multiplier * IQR
        upper = Q3 + multiplier * IQR

        # A row is an outlier if ANY feature is outside bounds
        outlier_mask = ((label_data < lower) | (label_data > upper)).any(axis=1)
        mask.loc[outlier_mask[outlier_mask].index] = False

    df_clean = df.loc[mask].reset_index(drop=True)
    removed = initial - len(df_clean)
    if removed > 0:
        logger.info("Removed %d outlier rows (IQR method, multiplier=%.1f).", removed, multiplier)
    else:
        logger.info("No outliers detected.")
    return df_clean, removed


def print_label_distribution(df, title="Label Distribution"):
    """Print the number of samples per gesture label."""
    print(f"\n  {title}:")
    print(f"  {'Label':<8} {'Count':>6}")
    print(f"  {'-'*14}")
    for label, count in df["label"].value_counts().sort_index().items():
        print(f"  {label:<8} {count:>6}")
    print(f"  {'-'*14}")
    print(f"  {'Total':<8} {len(df):>6}")


def main():
    """Main dataset cleaning pipeline."""
    args = parse_args()

    print("=" * 60)
    print("  Dataset Cleaning Pipeline")
    print("=" * 60)

    # Load dataset
    df = load_dataset(args.input)
    initial_count = len(df)

    print(f"\n  Input file:  {args.input}")
    print(f"  Output file: {args.output}")
    print(f"  Initial rows: {initial_count}")

    print_label_distribution(df, "Before Cleaning")

    # Step 1: Remove missing values
    print("\n--- Step 1: Removing missing values ---")
    df, nan_removed = remove_missing_values(df)

    # Step 2: Remove duplicates
    print("--- Step 2: Removing duplicate rows ---")
    df, dup_removed = remove_duplicates(df)

    # Step 3: Remove outliers
    print("--- Step 3: Removing outliers (IQR method) ---")
    df, outlier_removed = remove_outliers_iqr(df)

    # Summary
    total_removed = nan_removed + dup_removed + outlier_removed
    final_count = len(df)

    print("\n" + "=" * 60)
    print("  Cleaning Summary")
    print("=" * 60)
    print(f"  Initial rows:           {initial_count}")
    print(f"  Rows with NaN removed:  {nan_removed}")
    print(f"  Duplicate rows removed: {dup_removed}")
    print(f"  Outlier rows removed:   {outlier_removed}")
    print(f"  Total rows removed:     {total_removed}")
    print(f"  Final rows:             {final_count}")
    print(f"  Retention rate:         {final_count / initial_count * 100:.1f}%")

    print_label_distribution(df, "After Cleaning")

    # Save cleaned dataset
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    df.to_csv(args.output, index=False)
    file_size = os.path.getsize(args.output)
    logger.info("Saved cleaned dataset to %s (%.1f KB)", args.output, file_size / 1024)

    print(f"\n  Cleaned dataset saved to: {args.output}")
    print()


if __name__ == "__main__":
    main()
