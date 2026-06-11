# Dataset Documentation

This document describes the structure, data format, acquisition protocol, and preprocessing steps for the dataset used by the Sign Language Translator system.

---

## Dataset Description

The dataset consists of comma-separated value (CSV) logs capturing hand gestures. Each recorded instance represents a vector of 11 sensor values and a string label indicating the gesture class.

Data is streamed over Bluetooth Serial in real time. The model is trained to map these 11-dimensional feature vectors to their corresponding target label.

### Documented Assumptions and Placeholder Gestures

The original project report does not explicitly document the specific sign language gestures trained in the original dataset. To facilitate automated pipeline testing and system validation, a reference set of 10 static ASL (American Sign Language) letters (A, B, C, D, F, I, L, V, W, Y) has been configured as placeholder gesture profiles. 

All scripts (collection, cleaning, training, and inference) are completely gesture-agnostic and will function with any alphabetical labels inputted during data collection.

---

## Feature Descriptions

Each sample in the dataset contains 12 columns (11 features and 1 target label).

| # | Feature Name | Data Type | Range | Unit | Description |
|---|--------------|-----------|-------|------|-------------|
| 1 | `flex1` | Integer | 0 to 4095 | ADC counts | Thumb flex sensor — measures thumb flexion |
| 2 | `flex2` | Integer | 0 to 4095 | ADC counts | Index flex sensor — measures index finger flexion |
| 3 | `flex3` | Integer | 0 to 4095 | ADC counts | Middle flex sensor — measures middle finger flexion |
| 4 | `flex4` | Integer | 0 to 4095 | ADC counts | Ring flex sensor — measures ring finger flexion |
| 5 | `flex5` | Integer | 0 to 4095 | ADC counts | Pinky flex sensor — measures pinky finger flexion |
| 6 | `ax` | Float | -2.0 to 2.0 | g | Accelerometer X-axis linear acceleration |
| 7 | `ay` | Float | -2.0 to 2.0 | g | Accelerometer Y-axis linear acceleration |
| 8 | `az` | Float | -2.0 to 2.0 | g | Accelerometer Z-axis linear acceleration |
| 9 | `gx` | Float | -250.0 to 250.0 | deg/s | Gyroscope X-axis rotational velocity |
| 10 | `gy` | Float | -250.0 to 250.0 | deg/s | Gyroscope Y-axis rotational velocity |
| 11 | `gz` | Float | -250.0 to 250.0 | deg/s | Gyroscope Z-axis rotational velocity |
| 12 | `label` | String | Alphabetical | — | Target gesture class name |

---

## Data Collection Protocol

### Equipment Preparation
1. Mount the Smart Glove sensor node on the hand.
2. Power on the system using the slide switch.
3. Establish a Bluetooth connection from the host Raspberry Pi to the glove node (`ESP32_GLOVE`).
4. Ensure the serial port `/dev/rfcomm0` is open and receiving values at ~20 Hz.

### Data Acquisition
Data collection is performed using the interactive script [collect_data.py](../raspberry_pi/collect_data.py):
1. Execute the script: `python3 collect_data.py --port /dev/rfcomm0 --output dataset/raw/gesture_data.csv`
2. Enter the target gesture label at the prompt (e.g. `A`).
3. Maintain the target hand gesture steadily during the countdown and recording sequence. The system will record a batch of samples (default is 120 frames per gesture).
4. Repeat this process for multiple sessions and different hand configurations.
5. Enter `EXIT` at the prompt to end the data collection loop.

---

## Data Cleaning and Preprocessing

Raw CSV datasets are cleaned using the script [clean_dataset.py](../raspberry_pi/clean_dataset.py). The pipeline applies the following filters sequentially:

1. **Null Values**: Rows containing missing or null values are dropped.
2. **Duplicates**: Duplicate rows are removed to prevent overfitting and data leakage.
3. **Range Constraints**: Flex sensor readings are constrained to the valid ADC range [0, 4095]. Out-of-bounds inputs are discarded.
4. **Outlier Filtering**: Outliers are removed using the Interquartile Range (IQR) method:
   - For each feature column, values outside the range $[Q1 - 1.5 \times IQR, Q3 + 1.5 \times IQR]$ are flagged.
   - Outliers are computed per-class to preserve distinct sensor variations unique to specific gestures.
5. **Label Normalization**: Target labels are converted to uppercase and stripped of any leading or trailing whitespace.

---

## Dataset Format

### File Schema
The CSV format uses a standard header row:
```csv
flex1,flex2,flex3,flex4,flex5,ax,ay,az,gx,gy,gz,label
```

### Reference Row Examples
```csv
1850,2240,1920,2050,1640,0.124,-0.982,0.053,1.25,-0.42,0.18,B
3820,1150,1120,1080,3640,-0.045,-0.992,0.082,-0.15,0.08,-0.05,L
```
