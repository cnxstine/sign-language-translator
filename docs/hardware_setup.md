# Hardware Setup Guide

This guide details the hardware specifications, assembly instructions, power configuration, and initial test procedures for the Smart Glove Sign Language Translator.

---

## Project Authenticity Notes

The original project documentation contains an inconsistency between the design schematic and the final working implementation:
- **Design Schematic**: Documents the use of an MCP3008 ADC integrated over SPI to read the five analog flex sensors.
- **Final Implementation Code**: The working firmware reads the five flex sensors directly using the ESP32's built-in analog pins (`GPIO 32` to `36`) and handles ADC internally. This reduces connection complexity, sensor jitter, and latency.

This guide provides assembly instructions for the direct analog connection used in the final working prototype, alongside reference wiring for the legacy MCP3008 ADC design option.

---

## Bill of Materials

The table below lists all components required to build the smart glove node and host system.

| # | Component | Technical Specification | Quantity | Estimated Cost | Purpose |
|---|-----------|-------------------------|:--------:|:--------------:|---------|
| 1 | ESP32 DevKit V1 | 30-pin microcontroller, dual-core, Wi-Fi + Bluetooth | 1 | $6.00 | Data acquisition and wireless transmission |
| 2 | MCP3008 ADC | 10-bit, 8-channel analog-to-digital converter, SPI | 1 | $3.50 | Legacy design option (bypassed in working codebase) |
| 3 | MPU6050 Module | 3-axis accelerometer + 3-axis gyroscope, I2C | 1 | $2.50 | Captures hand orientation and motion dynamics |
| 4 | Flex Sensors | 2.2-inch resistive bend sensors | 5 | $35.00 | Captures flexion of individual fingers |
| 5 | Resistors | 10k Ohm, 1/4W, metal film | 5 | $0.50 | Fixed pull-down resistors for voltage dividers |
| 6 | TP4056 Module | Lithium battery charger with DW01A protection IC | 1 | $1.50 | Battery charging and voltage protection |
| 7 | Li-Ion Battery | 3.7V nominal, 1000 mAh rechargeable pouch cell | 1 | $4.00 | System portable power source |
| 8 | Slide Switch | SPST sub-miniature toggle switch | 1 | $0.30 | Hardware power switch |
| 9 | LED | Blue, 3mm, standard brightness | 1 | $0.10 | Connection and status indicator |
| 10 | Push Button | 6mm tactile momentary switch | 1 | $0.10 | Enters sensor calibration mode (Optional) |
| 11 | Glove | Stretchable fabric glove | 1 | $2.00 | Base mount for components |
| 12 | Perfboard | Single-sided prototype board (5cm x 7cm) | 1 | $2.00 | Circuit assembly board |
| 13 | Jumper Wires | 24 AWG, assorted lengths | 30 | $3.00 | Inter-component wiring |
| 14 | Raspberry Pi 4 | Model B, 4GB RAM recommended | 1 | $55.00 | Host processor and inference engine |
| 15 | SSD1306 OLED | 0.96-inch monochrome display, 128x64 pixels, I2C | 1 | $3.50 | Renders predicted gesture output (on host Pi) |

---

## Assembly Instructions

### Step 1: Prepare the Glove Mount
1. Place the stretchable fabric glove flat on a clean surface.
2. Mark out paths along the back of each finger (knuckle to the middle joint) where the flex sensors will be located.
3. Stitch thin fabric loops or apply velcro strips along the marked finger paths to create channels for the sensors.

### Step 2: Install Flex Sensors
1. Slide each flex sensor into its designated channel on the glove.
2. Apply a drop of adhesive or a small thread stitch at the base of each sensor near the knuckle to prevent slippage.
3. Ensure that the active sensor strip faces upwards and bends smoothly when the fingers curl.
4. Route the sensor solder tabs towards the back of the hand near the wrist.

### Step 3: Circuit Assembly (Direct Analog Pinout)
Assemble the circuit on a perfboard according to the direct ESP32 ADC pin mapping:
1. Connect one pin of each flex sensor to the ESP32 **3.3V** rail.
2. Connect the second pin of each flex sensor to the corresponding ESP32 analog pin and to a 10k Ohm pull-down resistor.
3. Connect the other side of all 10k Ohm pull-down resistors to the **GND** rail.
4. Pin Mapping:
   - Thumb Flex -> **GPIO 32**
   - Index Flex -> **GPIO 33**
   - Middle Flex -> **GPIO 34**
   - Ring Flex -> **GPIO 35**
   - Pinky Flex -> **GPIO 36**

### Step 4: Install the MPU6050 IMU
1. Mount the MPU6050 breakout board securely on the back of the glove (centered near the wrist) using double-sided adhesive tape or velcro.
2. Wire the I2C interface:
   - Connect MPU6050 VCC to ESP32 **3.3V**.
   - Connect MPU6050 GND to ESP32 **GND**.
   - Connect MPU6050 SDA to ESP32 **GPIO 21**.
   - Connect MPU6050 SCL to ESP32 **GPIO 22**.

### Step 5: Power Connections
1. Connect the positive (+) and negative (-) terminals of the 3.7V Li-Ion battery to the B+ and B- pads of the TP4056 charging module.
2. Connect the TP4056 OUT- pad to the ESP32 **GND** pin.
3. Connect the TP4056 OUT+ pad to a slide switch.
4. Connect the remaining terminal of the slide switch to the ESP32 **VIN** pin (input to the on-board 3.3V regulator).

### Step 6: Host Display Connection
On the Raspberry Pi host side, connect the SSD1306 OLED display using the physical I2C pins:
- Connect OLED VCC to Pi Pin 1 (3.3V).
- Connect OLED GND to Pi Pin 6 (GND).
- Connect OLED SDA to Pi Pin 3 (GPIO 2 / SDA1).
- Connect OLED SCL to Pi Pin 5 (GPIO 3 / SCL1).

---

## Power Management

### Battery Specifications
- **Type**: Single-cell Lithium-Ion pouch cell
- **Nominal Voltage**: 3.7V
- **Charging Voltage**: 4.2V (controlled by TP4056 module)
- **Over-Discharge Cutoff**: 2.5V (enforced by DW01A protection IC)
- **Estimated Current Draw**:
  - ESP32 (Bluetooth active): ~130 mA
  - MPU6050: ~3.5 mA
  - Flex sensors (voltage divider load): ~1.0 mA
  - **Total**: ~134.5 mA
- **Operational Duration**: ~7.4 hours on a 1000 mAh charge

---

## Hardware Testing and Troubleshooting

### 1. Power Verification
Turn on the slide switch and measure the voltage rails using a multimeter:
- Verify that the voltage between ESP32 VIN and GND is between 3.5V and 4.2V.
- Verify that the voltage between ESP32 3V3 and GND is 3.3V ± 0.1V.

### 2. Startup Diagnosis (Serial Monitor)
Connect the ESP32 to a computer via USB and open a serial terminal at 115200 baud. Turn on the glove power and verify the following output:
```
=================================
ESP32 HAND GLOVE BOOT
=================================
Flex OK
MPU OK
BT READY: ESP32_GLOVE
```
- If "MPU FAIL" is printed, check the SDA/SCL wire connections and ensure the MPU6050 is getting 3.3V power.

### 3. Sensor Output Check
Observe the CSV stream in the serial monitor:
- Verify that flex values (first 5 columns) change between ~1000 (extended) and ~3500 (fully flexed) when fingers are bent.
- Verify that accelerometer axes change when the glove is tilted, and gyroscope values register non-zero spikes during rotational movement.
