# Wiring Reference Guide

This document lists all pin assignments, electrical connections, and circuit configurations for the Smart Glove system. All connections correspond to the pins defined in [smart_glove.ino](../firmware/smart_glove/smart_glove.ino) and the Raspberry Pi host script [inference.py](../raspberry_pi/inference.py).

---

## Connection Block Diagram

The diagram below shows the electrical block layout of the glove node and host display system.

```mermaid
graph TD
    subgraph GloveNode [Smart Glove Sensor Node]
        Flex1 [Flex Sensor 1] --> GPIO32 [ESP32 GPIO 32]
        Flex2 [Flex Sensor 2] --> GPIO33 [ESP32 GPIO 33]
        Flex3 [Flex Sensor 3] --> GPIO34 [ESP32 GPIO 34]
        Flex4 [Flex Sensor 4] --> GPIO35 [ESP32 GPIO 35]
        Flex5 [Flex Sensor 5] --> GPIO36 [ESP32 GPIO 36]
        
        MPU [MPU6050 IMU] -->|SDA| GPIO21 [ESP32 GPIO 21]
        MPU -->|SCL| GPIO22 [ESP32 GPIO 22]
        
        Battery [3.7V Li-Ion] --> Charger [TP4056 Charger]
        Charger -->|OUT+| Switch [Power Switch]
        Switch -->|VIN| ESP [ESP32 DevKit]
    end

    subgraph HostNode [Receiver and Inference Host]
        OLED [SSD1306 OLED] -->|SDA| PiGPIO2 [Pi GPIO 2 / Pin 3]
        OLED -->|SCL| PiGPIO3 [Pi GPIO 3 / Pin 5]
        RPI [Raspberry Pi 4]
    end

    ESP -.->|Bluetooth Classic Serial| RPI
```

---

## 1. ESP32 Pin Assignments (Working Code)

The table below defines the GPIO pin mappings utilized in the firmware sketch.

| ESP32 Pin | Function | Electrical Connection | Description |
|-----------|----------|-----------------------|-------------|
| **GPIO 21** | I2C SDA | MPU6050 SDA | Serial Data Line for I2C communication |
| **GPIO 22** | I2C SCL | MPU6050 SCL | Serial Clock Line for I2C communication |
| **GPIO 32** | Analog In | Thumb Flex divider | Reads analog voltage for Thumb finger flexion |
| **GPIO 33** | Analog In | Index Flex divider | Reads analog voltage for Index finger flexion |
| **GPIO 34** | Analog In | Middle Flex divider | Reads analog voltage for Middle finger flexion |
| **GPIO 35** | Analog In | Ring Flex divider | Reads analog voltage for Ring finger flexion |
| **GPIO 36** | Analog In | Pinky Flex divider | Reads analog voltage for Pinky finger flexion |
| **3V3** | Power Out | Sensor VCC rails | Provides regulated 3.3V to sensors |
| **GND** | Ground | Ground rails | Common electrical ground reference |
| **VIN** | Power In | Power Switch output | Receives 3.7V–4.2V from the battery circuit |

---

## 2. Flex Sensor Voltage Divider Circuit

The five flex sensors require a voltage divider configuration to convert variable resistance into readable analog voltage signals.

### Circuit Schematic Diagram
```
     3.3V Rail
         |
         |
      [ Flex Sensor ] (Variable resistance: R_flex)
         |
         +-----------------> ESP32 Analog input pin (GPIO 32 to 36)
         |
      [ 10k Resistor ] (Fixed resistance: R_fixed)
         |
         |
      GND Rail
```

### Voltage Divider Calculation
The output voltage ($V_{out}$) routed to the ESP32 ADC pin is calculated as:

$$V_{out} = 3.3 \text{ V} \times \frac{R_{fixed}}{R_{flex} + R_{fixed}}$$

Where:
- $R_{fixed} = 10 \text{ k}\Omega$
- $R_{flex}$ varies from approximately $10 \text{ k}\Omega$ (unbent, flat) to $40 \text{ k}\Omega$ (fully bent).

This yields an input voltage range to the ESP32 of approximately **0.66V (fully bent) to 1.65V (flat)**, which matches the linear sampling range of the ESP32 ADCs.

---

## 3. Host OLED Display Connections (I2C)

The SSD1306 OLED display connects directly to the Raspberry Pi 4's physical pinout.

| OLED Pin | Function | Raspberry Pi Pin | RPi GPIO | Description |
|----------|----------|------------------|----------|-------------|
| **VCC** | Power | Pin 1 | 3.3V | Power supply input |
| **GND** | Ground | Pin 6 | GND | Ground reference |
| **SDA** | I2C Data | Pin 3 | GPIO 2 (SDA) | I2C serial data line |
| **SCL** | I2C Clock | Pin 5 | GPIO 3 (SCL) | I2C serial clock line |

No external pull-up resistors are required because the Raspberry Pi I2C pins have internal 1.8k Ohm pull-up resistors to 3.3V.

---

## 4. Power Configuration

The power node uses a TP4056 charging module with a DW01A protection IC to ensure battery safety.

| TP4056 Pad | Connected To | Purpose |
|------------|--------------|---------|
| **B+** | Battery Positive Terminal | Positive cell charging line |
| **B-** | Battery Negative Terminal | Negative cell charging line |
| **OUT+** | Slide Switch input | Regulated positive power line |
| **OUT-** | ESP32 GND and MPU6050 GND | Common system ground |

---

## 5. Legacy MCP3008 SPI Reference Wiring (Design Only)

This table outlines the SPI connection scheme described in the report's design section. Note that this is bypassed in the final codebase in favor of direct analog reads.

| MCP3008 Pin | MCP3008 Pin Name | Connected To | Pin Function |
|-------------|------------------|--------------|--------------|
| Pin 16 | VDD | 3.3V | Analog power supply |
| Pin 15 | VREF | 3.3V | Reference voltage |
| Pin 14 | AGND | GND | Analog ground |
| Pin 13 | CLK | ESP32 GPIO 18 | SPI Clock |
| Pin 12 | DOUT | ESP32 GPIO 19 | SPI MISO |
| Pin 11 | DIN | ESP32 GPIO 23 | SPI MOSI |
| Pin 10 | CS/SHDN | ESP32 GPIO 5 | SPI Chip Select |
| Pin 9 | DGND | GND | Digital ground |
| Pin 1 | CH0 | Thumb Flex Divider | Analog input channel 0 |
| Pin 2 | CH1 | Index Flex Divider | Analog input channel 1 |
| Pin 3 | CH2 | Middle Flex Divider | Analog input channel 2 |
| Pin 4 | CH3 | Ring Flex Divider | Analog input channel 3 |
| Pin 5 | CH4 | Pinky Flex Divider | Analog input channel 4 |
