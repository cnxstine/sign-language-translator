#!/usr/bin/env python3
"""
inference.py - Real-Time Gesture Inference for Sign Language Translator

[Fidelity Status]: Matches the original project report codebase logic (gesture_oled_autodiag.py).

Loads the trained Random Forest model and scaler, and performs real-time gesture
recognition from ESP32 sensor data received over Bluetooth Serial. Displays
predictions on a 128x64 OLED display and prints results to the terminal.

Original Code Features:
    - 11 features: 5 flex + 3-axis accel + 3-axis gyro
    - Uses StandardScaler to normalize incoming features
    - Extracts class label directly from model.classes_ based on probabilities (no LabelEncoder)
    - Default confidence threshold of 0.55
    - Smoothing buffer of size 5 to prevent rapid prediction flipping
    - Reconnection handling on SerialException
    - Hardware OLED display (128x64 SSD1306, I2C, address 0x3C)

Repository Improvements & Development Conveniences (Clearly Labeled):
    - [Development Convenience]: argparse interface for port, model directory, and confidence threshold.
    - [Development Convenience]: FPS tracking and terminal metrics visualization.
    - [Repository Improvement]: Graceful fallback to terminal-only logging if I2C OLED display is physically absent.
"""

import argparse
import logging
import os
import sys
import time
from collections import deque
from datetime import datetime

import joblib
import numpy as np
import serial

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Sensor configuration
NUM_SENSORS = 11
SENSOR_NAMES = [
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
        description="Real-time sign language gesture recognition."
    )
    parser.add_argument(
        "--port",
        type=str,
        default="/dev/rfcomm0",
        help="Bluetooth serial port (default: /dev/rfcomm0)",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default="models/",
        help="Directory containing model files (default: models/)",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.55,
        help="Minimum confidence to display prediction (default: 0.55, from report)",
    )
    return parser.parse_args()


def load_model_artifacts(model_dir):
    """
    Load the trained model and scaler.
    No label encoder is required as targets are trained as string labels.
    """
    model_path = os.path.join(model_dir, "gesture_model.pkl")
    scaler_path = os.path.join(model_dir, "scaler.pkl")

    for path, name in [(model_path, "Model"), (scaler_path, "Scaler")]:
        if not os.path.isfile(path):
            logger.error("%s not found: %s", name, path)
            sys.exit(1)

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    logger.info("Loaded model artifacts from %s", model_dir)
    logger.info("  Classes: %s", list(model.classes_))
    return model, scaler


def connect_serial(port, baudrate=115200, timeout=0.5):
    """
    Establish serial connection to ESP32 over Bluetooth.
    Matches serial connection configuration from the report.
    """
    logger.info("Opening serial port %s...", port)
    while True:
        try:
            ser = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(1)
            # Perform initial read to verify data flow
            if ser.readline():
                logger.info("Serial connection established and data flow verified.")
                return ser
            ser.close()
            logger.warning("No data received on port %s. Retrying...", port)
            time.sleep(1)
        except serial.SerialException:
            logger.warning("Serial connection error on port %s. Retrying...", port)
            time.sleep(1)


def init_oled():
    """
    [Repository Improvement / Graceful Fallback]
    Initialize the SSD1306 OLED display (128x64, I2C, address 0x3C).
    If initialization fails, runs in terminal-only mode.
    """
    try:
        import board
        import busio
        import adafruit_ssd1306
        from PIL import Image, ImageDraw, ImageFont

        i2c = busio.I2C(board.SCL, board.SDA)
        display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

        # Clear display
        display.fill(0)
        display.show()

        # Create blank image for drawing
        image = Image.new("1", (display.width, display.height))
        draw = ImageDraw.Draw(image)

        # Load default font
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except (IOError, OSError):
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        logger.info("OLED display initialized successfully (address 0x3C).")
        return display, image, draw, (font_large, font_small)

    except Exception as e:
        logger.warning("OLED not available: %s", e)
        logger.warning("Running in terminal-only mode.")
        return None, None, None, None


def update_oled(display, image, draw, fonts, gesture, confidence):
    """Update the OLED display with the predicted gesture and confidence."""
    if display is None:
        return

    font_large, font_small = fonts

    # Clear the image
    draw.rectangle((0, 0, display.width, display.height), fill=0)

    # Draw prediction details
    draw.text((10, 5), f"Sign: {gesture}", font=font_large, fill=255)

    # Draw confidence bar
    bar_y = 35
    bar_width = int(100 * confidence)
    draw.text((10, bar_y), f"Conf: {confidence:.0%}", font=font_small, fill=255)
    draw.rectangle((10, bar_y + 16, 110, bar_y + 22), outline=255, fill=0)
    draw.rectangle((10, bar_y + 16, 10 + bar_width, bar_y + 22), fill=255)

    # Push to display
    display.image(image)
    display.show()


def clear_oled(display, image, draw):
    """Clear the OLED display."""
    if display is None:
        return
    draw.rectangle((0, 0, display.width, display.height), fill=0)
    display.image(image)
    display.show()


def parse_sensor_line(line):
    """Parse raw line from ESP32 serial into numeric values."""
    line = line.strip()
    if not line:
        return None

    parts = line.split(",")
    if len(parts) != NUM_SENSORS:
        return None

    try:
        values = [float(p.strip()) for p in parts]
    except ValueError:
        return None

    return np.array(values).reshape(1, -1)


def main():
    """Main real-time prediction and loop."""
    args = parse_args()

    print("=" * 60)
    print("  Sign Language Translator - Real-Time Inference")
    print("=" * 60)

    # Load model and scaler
    model, scaler = load_model_artifacts(args.model_dir)

    # Connect to ESP32
    ser = connect_serial(args.port)

    # Initialize OLED
    display, image, draw, fonts = init_oled()

    print(f"\n  Port:       {args.port}")
    print(f"  Threshold:  {args.confidence_threshold:.0%}")
    print(f"  OLED:       {'Connected' if display else 'Not available'}")
    print(f"\n  Listening for sensor data... (Ctrl+C to stop)\n")

    # [Development Convenience] FPS tracking
    frame_count = 0
    fps_start_time = time.time()
    fps = 0.0

    # Prediction window buffer (size 5, matches report's WINDOW_SIZE)
    buffer = deque(maxlen=5)
    last_prediction = None

    try:
        while True:
            try:
                # Read raw sensor data from serial
                raw = ser.readline().decode("utf-8", errors="replace")
            except serial.SerialException as e:
                logger.error("Serial connection lost: %s", e)
                # Attempt to re-establish serial communication
                buffer.clear()
                last_prediction = None
                clear_oled(display, image, draw)
                ser.close()
                time.sleep(1)
                ser = connect_serial(args.port)
                continue

            # Parse sensor line
            features = parse_sensor_line(raw)
            if features is None:
                continue

            # Preprocess and scale features
            features_scaled = scaler.transform(features)

            # Predict probabilities
            probs = model.predict_proba(features_scaled)[0]
            confidence = float(np.max(probs))

            # Apply confidence threshold
            if confidence < args.confidence_threshold:
                continue

            # Extract predicted string class name directly from model classes
            pred = model.classes_[int(np.argmax(probs))]
            buffer.append(pred)

            # Apply majority vote smoothing
            final_pred = max(set(buffer), key=buffer.count)

            # [Development Convenience] Update FPS
            frame_count += 1
            elapsed = time.time() - fps_start_time
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                frame_count = 0
                fps_start_time = time.time()

            # Update displays if prediction has changed
            if final_pred != last_prediction:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(
                    f"  [{timestamp}]  Gesture: {final_pred:<4}  "
                    f"Confidence: {confidence:.1%}  "
                    f"FPS: {fps:.1f}"
                )

                update_oled(display, image, draw, fonts, final_pred, confidence)
                last_prediction = final_pred

    except KeyboardInterrupt:
        print("\n\n  Inference stopped by user.")
    finally:
        # Cleanup
        clear_oled(display, image, draw)
        ser.close()
        logger.info("Serial connection closed. Goodbye.")


if __name__ == "__main__":
    main()
