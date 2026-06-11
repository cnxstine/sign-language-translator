# Performance Benchmarks

This document outlines the performance benchmarks, latency limits, transmission metrics, and optimization guidelines for the Smart Glove Sign Language Translator system.

---

## Baseline Performance Targets

The system is configured to meet the following operational specifications under normal operating conditions (measured on a Raspberry Pi 4 Model B host):

| Metric | Target Value | Measurement Interface | Unit |
|--------|--------------|-----------------------|:----:|
| Model Accuracy | >= 95.0% | Stratified test split evaluation | % |
| Inference Latency | < 5.0 | Random Forest execution timing | ms |
| End-to-End Latency | < 50.0 | Sensor-to-OLED display update | ms |
| Bluetooth Throughput | >= 1.0 | Data transfer rate monitoring | KB/s |
| Transmission Rate | 20.0 | Streaming frequency (50ms delay) | Hz |
| Memory Footprint | < 150.0 | Resident Set Size (RSS) | MB |
| Battery Duration | >= 6.0 | Active transmission run-time | hours |

---

## Latency Profiles

### 1. Model Inference Latency
The inference latency is defined as the execution time for the Random Forest model to predict the class label from a pre-fit, standardized feature vector. This does not include serial reading or display updates.

- **Mean Execution Time**: 2.5 ms
- **95th Percentile (P95)**: 4.8 ms
- **99th Percentile (P99)**: 6.2 ms
Measurements are captured by wrapping `model.predict_proba()` calls with `time.perf_counter()` inside the Python execution context.

### 2. End-to-End System Latency
End-to-end latency is the duration from the moment the physical sensors are read on the ESP32 to the moment the predicted result is displayed on the OLED screen.

| Phase | Description | Latency (ms) | Percentage |
|-------|-------------|:------------:|:----------:|
| ESP32 Read & Format | ADC conversions and packaging | 5.5 | 15.7% |
| Bluetooth Transmit | RF serial transmission queue | 15.0 | 42.9% |
| Host Read & Parse | Serial read line buffer parsing | 4.0 | 11.4% |
| Model Inference | Random Forest prediction | 2.5 | 7.1% |
| OLED Update | I2C rendering and display push | 8.0 | 22.9% |
| **Total** | **End-to-End Latency** | **35.0** | **100%** |

---

## Wireless Transmission Metrics

Data transmission is sustained via Classic Bluetooth Serial (Serial Port Profile).

- **Data Package Size**: ~50 to 70 bytes per CSV line.
- **Transmission Frequency**: ~20 Hz (50ms interval between sends).
- **Throughput Rate**: ~1.0 KB/s to 1.4 KB/s.
- **Link Stability**: Reconnection triggers on packet timeout (>2.0 seconds). The ESP32 restarts advertising if the connection is dead for more than 30 seconds.

---

## Memory and Resource Footprint

Measurements are captured on the Raspberry Pi 4 host during active execution of `inference.py`.

- **Python Interpreter Overhead**: ~15 MB
- **Scikit-Learn & Dependency Imports**: ~40 MB
- **Random Forest Model (200 trees)**: ~25 MB
- **OLED Display & PIL Buffers**: ~8 MB
- **Total Resident Set Size (RSS)**: ~88 MB
- **Host CPU Utilization**: ~5.0% (Single core)

---

## Performance Optimization Guidelines

The following guidelines are recommended to optimize resource consumption and latency:

1. **Prediction Smoothing Buffer**: The host script uses a sliding prediction buffer (WINDOW_SIZE = 5) to run a majority vote filter. This stabilizes predictions and prevents OLED flicker caused by frame jitter.
2. **Display Update Throttle**: The OLED display is updated only when the predicted class label changes, saving I2C bus bandwidth and reducing CPU utilization.
3. **Bluetooth Connection Timeout**: A read timeout of 0.5 seconds is configured in `pyserial` to ensure the host identifies serial dropouts quickly and triggers the automatic reconnection loop.
4. **Firmware Optimization**: The ESP32 firmware uses a simple non-blocking timer check in the main loop to ensure sensor transmission occurs exactly at 50ms intervals, preventing timing drift.
