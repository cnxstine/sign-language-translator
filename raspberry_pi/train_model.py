#!/usr/bin/env python3
"""
train_model.py - Model Training for Sign Language Translator

[Fidelity Status]: Matches the original project report codebase logic (train_model1.py).

Trains a Random Forest classifier on the cleaned gesture sensor dataset.
Applies StandardScaler for feature normalization. Evaluates with accuracy,
precision, recall, F1-score, and confusion matrix.

Original Code Features:
    - 11 features: 5 flex + 3-axis accel + 3-axis gyro
    - Fits StandardScaler on the features
    - Fits RandomForestClassifier directly on target string labels (no LabelEncoder)
    - Saves model and scaler using joblib serialization

Saves:
    - models/gesture_model.pkl   (Random Forest model)
    - models/scaler.pkl          (StandardScaler)

Development Conveniences (Clearly Labeled):
    - [Development Convenience]: argparse interface for dataset path and output model directory.
    - [Development Convenience]: Outputs a formatted confusion matrix and feature importances visualization.
"""

import argparse
import logging
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Feature columns (Original dataset structure)
FEATURE_COLUMNS = [
    "flex1", "flex2", "flex3", "flex4", "flex5",
    "ax", "ay", "az",
    "gx", "gy", "gz",
]


def parse_args():
    """
    [Development Convenience]
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Train a Random Forest gesture classifier on sensor data."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="dataset/gesture_data_clean.csv",
        help="Path to cleaned dataset CSV (default: dataset/gesture_data_clean.csv)",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default="models/",
        help="Directory to save trained model files (default: models/)",
    )
    return parser.parse_args()


def load_dataset(filepath):
    """Load and validate the cleaned dataset."""
    if not os.path.isfile(filepath):
        logger.error("Dataset not found: %s", filepath)
        sys.exit(1)

    df = pd.read_csv(filepath)

    # Validate columns match the standard dataset format
    expected = FEATURE_COLUMNS + ["label"]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        logger.error("Missing columns: %s", missing)
        sys.exit(1)

    logger.info("Loaded dataset: %d samples, %d features", len(df), len(FEATURE_COLUMNS))
    return df


def print_confusion_matrix(cm, labels):
    """[Development Convenience] Print a formatted confusion matrix."""
    header = "       " + "  ".join(f"{l:>4}" for l in labels)
    print(header)
    print("       " + "-" * (len(labels) * 6))

    for i, label in enumerate(labels):
        row = "  ".join(f"{cm[i, j]:>4}" for j in range(len(labels)))
        print(f"  {label:>3} | {row}")


def main():
    """Main training pipeline."""
    args = parse_args()

    print("=" * 60)
    print("  Gesture Recognition Model Training")
    print("=" * 60)

    # Load dataset
    df = load_dataset(args.dataset)

    # Unique labels in the dataset
    class_names = sorted(df['label'].unique())

    print(f"\n  Dataset:    {args.dataset}")
    print(f"  Samples:    {len(df)}")
    print(f"  Features:   {len(FEATURE_COLUMNS)}")
    print(f"  Labels:     {class_names}")
    print(f"  Model dir:  {args.model_dir}")

    # Separate features and target (target labels are kept as string values)
    X = df[FEATURE_COLUMNS].values
    y = df["label"].values

    # Train-test split (80/20, stratified by string labels)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info("Train set: %d samples, Test set: %d samples", len(X_train), len(X_test))

    # Feature scaling (StandardScaler fit on train set)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    logger.info("Applied StandardScaler (fit on train set).")

    # Train Random Forest (Matches report: n_estimators=200, random_state=42)
    print("\n--- Training Random Forest Classifier ---")
    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train_scaled, y_train)
    logger.info("Model training complete.")

    # Evaluate on test set
    y_pred = model.predict(X_test_scaled)

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average="weighted")
    recall = recall_score(y_test, y_pred, average="weighted")
    f1 = f1_score(y_test, y_pred, average="weighted")

    print("\n--- Evaluation Results ---")
    print(f"  Accuracy:  {accuracy:.4f} ({accuracy * 100:.2f}%)")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1-Score:  {f1:.4f}")

    # Classification report
    print("\n--- Classification Report ---")
    report = classification_report(y_test, y_pred, target_names=class_names)
    print(report)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=class_names)
    print("--- Confusion Matrix ---")
    print_confusion_matrix(cm, class_names)
    print()

    # Feature importances
    importances = model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    print("--- Feature Importances ---")
    for i in sorted_idx:
        bar = "#" * int(importances[i] * 50)
        print(f"  {FEATURE_COLUMNS[i]:<8} {importances[i]:.4f}  {bar}")
    print()

    # Save model artifacts (Outputting model and scaler only, matching original report)
    os.makedirs(args.model_dir, exist_ok=True)

    model_path = os.path.join(args.model_dir, "gesture_model.pkl")
    scaler_path = os.path.join(args.model_dir, "scaler.pkl")

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    print("--- Saved Model Artifacts ---")
    for name, path in [("Model", model_path), ("Scaler", scaler_path)]:
        size = os.path.getsize(path)
        size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.2f} MB"
        print(f"  {name:<10} {path:<35} ({size_str})")

    print("\nTraining complete.")


if __name__ == "__main__":
    main()
