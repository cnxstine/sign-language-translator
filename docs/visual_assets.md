# Visual Assets and Media Reference

This document serves as a repository reference for all visual assets, schematics, and screenshots required for publication readiness. It defines the naming conventions, storage paths, and capturing guidelines for each asset.

All media assets should be stored under the `assets/` directory in the repository.

---

## Required Visual Assets

### 1. System Architecture Diagram
- **File Name**: `system_architecture.png`
- **Path**: `assets/diagrams/system_architecture.png`
- **Purpose**: Illustrates the end-to-end signal flow from the wearable glove sensors, through the wireless Bluetooth link, to the host system and output display.
- **Guideline**: Export the Mermaid system overview diagram from the README as a PNG or compile it using standard vector design tools.

### 2. Hardware Block Diagram
- **File Name**: `hardware_block_diagram.png`
- **Path**: `assets/diagrams/hardware_block_diagram.png`
- **Purpose**: Displays the internal component relationships on the wearable glove node (ESP32, MPU6050, 5x Flex Sensor voltage dividers, and TP4056 charging subsystem).
- **Guideline**: Generate using drawing software to show power rails (3.3V, GND, VIN) and communications buses (I2C).

### 3. Wiring Schematic Diagram
- **File Name**: `wiring_diagram.png`
- **Path**: `assets/diagrams/wiring_diagram.png`
- **Purpose**: Comprehensive schematic showing exact electrical pin-to-pin connections for the ESP32 pins, sensor connections, pull-down resistors, switches, and battery module.
- **Guideline**: Export from standard electronic design automation (EDA) software like Fritzing or KiCad.

### 4. Smart Glove Photograph
- **File Name**: `smart_glove_photo.jpg`
- **Path**: `assets/images/smart_glove_photo.jpg`
- **Purpose**: High-resolution photograph of the physically assembled smart glove.
- **Guideline**: Photograph the glove laid flat on a neutral background under good lighting. Show the mounting of the ESP32 on the wrist, sensor routing along the fingers, and battery placement.

### 5. OLED Output Photograph
- **File Name**: `oled_output_photo.jpg`
- **Path**: `assets/images/oled_output_photo.jpg`
- **Purpose**: Close-up photograph of the SSD1306 OLED screen rendering a predicted gesture character.
- **Guideline**: Capture a clear image displaying a stable prediction letter and its confidence bar during live inference. Ensure no screen glare or blur.

### 6. Dataset Collection Screenshot
- **File Name**: `dataset_collection_screenshot.png`
- **Path**: `assets/screenshots/dataset_collection_screenshot.png`
- **Purpose**: Displays the terminal output during interactive dataset acquisition.
- **Guideline**: Run `collect_data.py`, record a few frames, and capture the terminal showing the prompt, countdown, and progress bar during active recording.

### 7. Model Training Screenshot
- **File Name**: `model_training_screenshot.png`
- **Path**: `assets/screenshots/model_training_screenshot.png`
- **Purpose**: Captures the model training and evaluation terminal metrics.
- **Guideline**: Take a screenshot of the terminal after running `train_model.py`. The image should display the classification report, the confusion matrix, and the feature importances table.

### 8. Real-Time Inference Screenshot
- **File Name**: `inference_screenshot.png`
- **Path**: `assets/screenshots/inference_screenshot.png`
- **Purpose**: Captures terminal feedback during live inference.
- **Guideline**: Run `inference.py` while receiving active data and screenshot the terminal showing prediction outputs, timestamps, confidence scores, and FPS calculations.

---

## File Structure for Assets

Ensure the following subfolders exist under the `assets/` directory to host the media files:

- `assets/diagrams/` - For schematics and blocks
- `assets/images/` - For hardware and device photographs
- `assets/screenshots/` - For script execution captures
