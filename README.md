# Sign Language Translator Using a Smart Glove

This repository contains the design, implementation, and documentation for a wearable sign language translation system. The system captures hand gestures using a smart glove equipped with flex sensors and an inertial measurement unit (IMU), transmits the sensor readings wirelessly via Bluetooth, and performs real-time gesture classification using a machine learning model on a single-board computer.

## Project Overview

The Smart Glove Sign Language Translator is an assistive technology prototype designed to bridge the communication gap between sign language users and individuals unfamiliar with sign language. By leveraging wearable sensors and edge computing, the system translates physical gestures into digital text in real time.

The glove-based sensor node collects finger flexion and hand orientation data. An ESP32 microcontroller processes these signals and streams them over a Bluetooth connection to a Raspberry Pi 4. The Raspberry Pi runs a pre-trained Random Forest classifier to predict the performed gesture and outputs the result to an I2C-connected SSD1306 OLED display.

---

## System Architecture

The following block diagram illustrates the hardware and data flow of the system.

```mermaid
graph LR
    subgraph GloveNode [Smart Glove Sensor Node]
        Flex [5x Flex Sensors] --> ESP [ESP32 Microcontroller]
        IMU [MPU6050 IMU] --> ESP
        Power [TP4056 + 3.7V Battery] -.->|Power| ESP
    end

    ESP -->|Bluetooth Serial| BT((Bluetooth Link))

    subgraph HostNode [Raspberry Pi Host]
        BT --> RPI [Raspberry Pi 4]
        RPI --> ML [Random Forest Inference]
        ML --> OLED [SSD1306 OLED Display]
    end
```

### Data Flow Sequence

1. **Sensor Acquisition**: The ESP32 reads analog values from five flex sensors representing finger bend levels and digital values from the MPU6050 IMU representing hand acceleration and angular velocity.
2. **Data Transmission**: The ESP32 packages the 11 sensor values into a comma-separated ASCII string and transmits it over Classic Bluetooth Serial (SPP) at 115200 baud.
3. **Data Reception & Preprocessing**: The Raspberry Pi reads the incoming stream, parses the CSV string, and normalizes the features using a pre-fit StandardScaler.
4. **Machine Learning Inference**: The preprocessed vector is fed to a Random Forest classifier.
5. **Output**: The predicted gesture string is rendered on the OLED display.

---

## Hardware Components

The system requires the following hardware components:

| Component | Specification | Quantity | Purpose |
|-----------|---------------|:--------:|---------|
| ESP32 DevKit V1 | Dual-core, Wi-Fi + Classic Bluetooth | 1 | Microcontroller for glove data acquisition and transmission |
| MPU6050 | 3-axis accelerometer + 3-axis gyroscope | 1 | Captures hand orientation and motion dynamics |
| Flex Sensors | 2.2-inch resistive bend sensors | 5 | Measures flexion of individual fingers |
| Resistors | 10k Ohm, 1/4W | 5 | Fixed resistors for flex sensor voltage dividers |
| TP4056 | 1A Lithium battery charging module | 1 | Manages charging and protection for the battery |
| Battery | 3.7V Lithium-Ion (1000 mAh minimum) | 1 | Provides portable power for the glove node |
| Slide Switch | SPST | 1 | Power toggle for the glove electronics |
| Raspberry Pi 4 | Model B, 4GB RAM recommended | 1 | Processes incoming data and executes model inference |
| SSD1306 OLED | 128x64 pixels, I2C interface | 1 | Displays the predicted sign language gesture |
| Glove | Elastic fabric base | 1 | Structural mount for the sensors and wiring |

---

## Software Stack

### Firmware (ESP32)
- **Framework**: Arduino C++
- **Libraries**:
  - `Wire` (Built-in I2C driver)
  - `MPU6050` (Jeff Rowberg library for register access)
  - `BluetoothSerial` (Classic Bluetooth driver)

### Host Application (Raspberry Pi)
- **Language**: Python 3.8+
- **Core Libraries**:
  - `scikit-learn`: Random Forest classification and StandardScaler
  - `joblib`: Model and scaler serialization
  - `pyserial`: Serial communication over RFCOMM
  - `numpy` & `pandas`: Data preprocessing and array manipulation
  - `adafruit-circuitpython-ssd1306` & `Pillow`: OLED display output

---

## Dataset Structure

The dataset consists of comma-separated value (CSV) files containing 11 numeric features and a string label representing the gesture class.

| Column Name | Data Type | Range | Description |
|-------------|-----------|-------|-------------|
| `flex1` | Integer | 0 to 4095 | Thumb flex sensor (12-bit ADC value) |
| `flex2` | Integer | 0 to 4095 | Index finger flex sensor (12-bit ADC value) |
| `flex3` | Integer | 0 to 4095 | Middle finger flex sensor (12-bit ADC value) |
| `flex4` | Integer | 0 to 4095 | Ring finger flex sensor (12-bit ADC value) |
| `flex5` | Integer | 0 to 4095 | Pinky finger flex sensor (12-bit ADC value) |
| `ax` | Float | -2.000 to 2.000 | Accelerometer X-axis acceleration (in g) |
| `ay` | Float | -2.000 to 2.000 | Accelerometer Y-axis acceleration (in g) |
| `az` | Float | -2.000 to 2.000 | Accelerometer Z-axis acceleration (in g) |
| `gx` | Float | -250.00 to 250.00 | Gyroscope X-axis angular velocity (in deg/s) |
| `gy` | Float | -250.00 to 250.00 | Gyroscope Y-axis angular velocity (in deg/s) |
| `gz` | Float | -250.00 to 250.00 | Gyroscope Z-axis angular velocity (in deg/s) |
| `label` | String | Alphabetical | Labeled gesture class name |

---

## Machine Learning Pipeline

The project uses a structured machine learning pipeline:

1. **Data Collection**: Sensor streams are collected interactively using the serial port and saved with ground truth labels.
2. **Data Cleaning**: Outliers are removed per class using the Interquartile Range (IQR) method. Missing values and duplicates are discarded.
3. **Feature Scaling**: Features are standardized by subtracting the mean and dividing by the standard deviation of each feature computed from the training split.
4. **Model Training**: A Random Forest Classifier is trained on the standardized features using 200 estimators.
5. **Serialization**: The fitted `StandardScaler` and `RandomForestClassifier` objects are exported to `.pkl` files using `joblib` for deployment.

---

## Installation Guide

Follow these steps to set up the software environment on the Raspberry Pi:

### 1. System Setup
Ensure Python 3 and basic system tools are installed:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv i2c-tools bluetooth bluez bluez-tools
```

### 2. Configure I2C Interface
Enable I2C via `raspi-config` or by adding `dtparam=i2c_arm=on` to `/boot/config.txt`. Re-add user to I2C group:
```bash
sudo usermod -aG i2c pi
```

### 3. Install Python Dependencies
Clone the repository and install dependencies:
```bash
git clone https://github.com/yourusername/sign-language-translator.git
cd sign-language-translator
pip3 install -r raspberry_pi/requirements.txt
```

---

## Usage Guide

### 1. Flash the ESP32 Firmware
- Open `firmware/smart_glove/smart_glove.ino` in the Arduino IDE.
- Select the "ESP32 Dev Module" board and upload the code to your ESP32 board.
- Power on the ESP32 to start Bluetooth advertising (`ESP32_GLOVE`).

### 2. Establish Bluetooth Connection
Pair the Raspberry Pi with the ESP32 and bind it to a serial device:
```bash
# Pair device using MAC address
bluetoothctl pair XX:XX:XX:XX:XX:XX
bluetoothctl trust XX:XX:XX:XX:XX:XX

# Bind to serial port RFCOMM0
sudo rfcomm bind 0 XX:XX:XX:XX:XX:XX 1
```

### 3. Train the System (Using Synthetic Data for Testing)
To validate the full pipeline without hardware, generate a test dataset and train the model:
```bash
cd raspberry_pi

# 1. Generate test dataset
python3 generate_synthetic_data.py --samples 100 --output ../dataset/raw/gesture_data_raw.csv

# 2. Clean the raw data
python3 clean_dataset.py --input ../dataset/raw/gesture_data_raw.csv --output ../dataset/cleaned/gesture_data_clean.csv

# 3. Train and serialize model
python3 train_model.py --dataset ../dataset/cleaned/gesture_data_clean.csv --model-dir ../models
```

### 4. Run Real-Time Inference
Launch the inference loop on the Raspberry Pi:
```bash
python3 inference.py --port /dev/rfcomm0 --model-dir ../models
```

---

## Repository Structure

```
sign-language-translator/
├── README.md                           # General documentation
├── LICENSE                             # MIT License
├── .gitignore                          # Exclude compiled files, models, and datasets
│
├── firmware/                           # ESP32 firmware
│   └── smart_glove/
│       └── smart_glove.ino             # Main C++ firmware code
│
├── raspberry_pi/                       # Python scripts for inference and pipeline
│   ├── collect_data.py                 # Interactive dataset collector
│   ├── clean_dataset.py                # Dataset outlier cleaning
│   ├── train_model.py                  # Model training and metric exporter
│   ├── inference.py                    # Main real-time prediction script
│   ├── generate_synthetic_data.py      # Pipeline validation utility
│   └── requirements.txt               # Pinned pip requirements
│
├── dataset/                            # Dataset folders
│   ├── raw/                            # Directory for raw collected CSV data
│   └── cleaned/                        # Directory for cleaned CSV data
│
├── models/                             # Output model folder
│   ├── gesture_model.pkl               # Serialized Random Forest model
│   └── scaler.pkl                      # Serialized StandardScaler object
│
├── scripts/                            # Helper setup scripts
│   ├── bluetooth_setup.sh              # Automates Bluetooth pairing
│   └── install.sh                      # Automates Raspberry Pi package installs
│
├── systemd/                            # Daemon configuration
│   ├── rfcomm-glove.service            # Binds RFCOMM at boot
│   ├── gesture-glove.service           # Automatically runs inference
│   └── signlanguage.service            # Consolidated translator service
│
├── docs/                               # Engineering documentation
│   ├── architecture.md                 # System overview and diagrams
│   ├── hardware_setup.md               # Bill of materials and assembly guide
│   ├── wiring_guide.md                 # Pin tables and schematics
│   ├── dataset.md                      # Feature descriptions and collection protocol
│   ├── benchmarks.md                   # Speed, latency, and throughput metrics
│   └── original_project_report.docx    # Reassigned original project documentation
│
└── assets/                             # Visual assets and placeholders
```

---

## Results

On testing with cross-validation and independent splits, the Random Forest model achieves the following benchmarks on the reference dataset:

- **Classification Accuracy**: 98.88% across 10 classes
- **Inference Latency**: 2.5 ms (measured on Raspberry Pi 4 CPU)
- **End-to-End Latency**: 35 ms (measured from ESP32 sensor read to OLED display output update)
- **Bluetooth Streaming Jitter**: 2.1 ms (at ~20 Hz transmission rate)

---

## Limitations

- **Predefined Gestures**: The model operates on static hand configurations and does not support dynamic gestures that rely on motion paths.
- **Voice Feedback**: The system is text-only and does not provide audio speech output.
- **Environmental Drift**: Flex sensor voltage dividers may show minor baseline shifts due to stretch wear and temperature changes.

---

## Future Improvements

The following items are designated for future hardware and software revisions:
- **Incremental Calibration**: Implementing a baseline zero-bias offset routine for flex sensors on system boot.
- **Sequence Modeling**: Benchmark recurrent neural models (e.g. LSTM) on time-series inputs to support dynamic spelling sequences.
- **Audio Synthesis**: Integrating text-to-speech modules on the Raspberry Pi host.

---

## Project Authenticity Notes

This repository contains the reconstructed codebase and polished documentation matching the original project report ([original_project_report.docx](docs/original_project_report.docx)). 

The repository preserves the implementation used during validation:
1. **Flex Sensor Connection**: The final working system routes the five flex sensors directly to the ESP32 DevKit internal analog inputs (`GPIO 32` to `36`), which performs internal 12-bit analog-to-digital conversions.
2. **MCP3008 Design Reference**: The report documents an MCP3008 ADC SPI connection. To maintain fidelity to the report's design documents, this schematic is preserved and documented under the wiring guide, though the firmware reads the ESP32 ADCs directly.
3. **Gesture Alphabets**: The specific gesture characters trained in the original database were not explicitly specified in the report text. The repository configures a set of 10 static ASL letter templates as placeholders to allow for automated tests and pipeline validation. The scripts are completely gesture-agnostic.

---

## Repository Recovery Notes

This repository was reconstructed from:

* The final project report
* Recovered firmware
* Recovered Raspberry Pi code
* Recovered training scripts

### Component Status Table

| Component | Status |
| :--- | :--- |
| ESP32 Firmware | Recovered |
| Raspberry Pi Inference | Recovered |
| Dataset | Missing (reconstructed format) |
| Model Files | Missing |
| Documentation | Reconstructed |

### File-Level Integrity Details

* **Original Recovered Files**:
  * `firmware/smart_glove/smart_glove.ino` (Recovered from `val-flex_2_1.ino`)
  * `raspberry_pi/inference.py` (Recovered from `gesture_oled_autodiag.py`)
  * `raspberry_pi/train_model.py` (Recovered from `train_model1.py`)
* **Reconstructed Components**:
  * `raspberry_pi/collect_data.py` (Reconstructed from the data collection chapter specifications)
  * `raspberry_pi/clean_dataset.py` (Reconstructed from the data cleaning chapter specifications)
  * `systemd/rfcomm-glove.service` (Reconstructed from the service configuration files)
  * `systemd/gesture-glove.service` (Reconstructed from the service configuration files)
  * `systemd/signlanguage.service` (Reconstructed from the service configuration files)
  * `dataset/` structure (Reconstructed format matching dataset descriptions)
  * `docs/` (Reconstructed based on project report chapters)

---

## Validation Status

This section details the physical hardware validation status of the system to prevent reviewers from assuming all reconstructed components have been fully retested.

### Verified

Components that were actually tested during project development:
* **Analog Flex Sensor Nodes**: Flex sensor voltage divider readings acquired through the ESP32 internal ADCs.
* **IMU Coordinate System**: Hand orientation and dynamic motion acquisition via the MPU6050 accelerometer and gyroscope.
* **Classic Bluetooth Transmission**: Streaming sensor data packets wirelessly from the ESP32 under the `ESP32_GLOVE` device name.
* **Model Inference Engine**: Random Forest Classifier predictions executed on standardized sensor feature vectors.

### Reconstructed

Components recreated from the report after file loss:
* **Interactive Data Collector**: The script (`collect_data.py`) used to build the gesture dataset via a CLI-guided recording loop.
* **Preprocessing Pipeline**: Outlier detection using the Interquartile Range (IQR) method and StandardScaler integration (`clean_dataset.py`).
* **Daemon Configuration**: Systemd service scripts (`rfcomm-glove.service`, `gesture-glove.service`, `signlanguage.service`) for automatic execution at system startup.

### Not Yet Revalidated

Components that still require hardware testing after reconstruction:
* **Active Serial Binding**: Establishing a stable RFCOMM socket connection over `/dev/rfcomm0` using the reconstructed BlueZ system configurations on a physical Raspberry Pi 4.
* **SSD1306 I2C OLED Output**: Displaying predicted characters on a physical 128x64 display panel over the I2C bus using the Adafruit CircuitPython SSD1306 driver.
* **End-to-End Live Translation**: Validating real-time gesture classification using a physical smart glove hardware assembly transmitting to the reconstructed host environment.

---

## GitHub Publication Readiness Checklists

These checklists represent steps required to prepare this repository for public release. A complete asset checklist is available in the [release_checklist.md](docs/release_checklist.md) file.

### GitHub Release Assets Checklist
- [ ] **README completed**
- [ ] **Architecture diagram added**
- [ ] **Wiring diagram added**
- [ ] **Hardware photos added**
- [ ] **OLED output photo added**
- [ ] **Dataset example added**
- [ ] **Trained model added**
- [ ] **Demo video uploaded**
- [ ] **Release tag created**
- [ ] **License verified**
- [ ] **Installation instructions tested**

### Technical Repository Checklist
- [ ] Ensure `.gitignore` successfully excludes all local `.pkl` files and raw data CSVs from tracking.
- [ ] Check that no relative local filesystem paths are hardcoded in any execution scripts.
- [ ] Verify that all Markdown cross-references link to existing files.
- [ ] Confirm all script headers explain original source and development improvements.

---

## Contributors

- S. Jayant Kumar - Project Development
- Veetesh Sinha - Project Development
- Swayam Das - Project Development
- Anubhab Patra - Project Development
- Smruti Sourav Mishra - Project Development
- Saadiya Farheen - Project Development

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
