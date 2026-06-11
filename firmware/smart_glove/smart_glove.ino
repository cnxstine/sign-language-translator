/*
 * Smart Glove Sign Language Translator - ESP32 Firmware
 * 
 * [Fidelity Status]: Matches the original project report codebase exactly.
 * 
 * Captures finger bending from 5 flex sensors connected to ESP32 analog pins (32-36)
 * and hand orientation from MPU6050 IMU connected via I2C. Transmits data wirelessly
 * over Classic Bluetooth Serial (advertised as "ESP32_GLOVE") to a Raspberry Pi.
 * 
 * Hardware Layout (Original Report):
 *   - ESP32 Pin 32 (ADC1_CH4) -> Flex Sensor 1 (Thumb)
 *   - ESP32 Pin 33 (ADC1_CH5) -> Flex Sensor 2 (Index)
 *   - ESP32 Pin 34 (ADC1_CH6) -> Flex Sensor 3 (Middle)
 *   - ESP32 Pin 35 (ADC1_CH7) -> Flex Sensor 4 (Ring)
 *   - ESP32 Pin 36 (ADC1_CH0) -> Flex Sensor 5 (Pinky)
 *   - ESP32 Pin 21 -> MPU6050 SDA
 *   - ESP32 Pin 22 -> MPU6050 SCL
 * 
 * Note on MCP3008 ADC: The report documents an MCP3008 ADC connected to the Raspberry Pi
 * over SPI. However, the actual working code in the report bypasses the MCP3008 and reads 
 * the flex sensors directly through the ESP32's built-in 12-bit analog input pins. This
 * code maintains that original implementation.
 */

#include <Wire.h>
#include <MPU6050.h>
#include "BluetoothSerial.h"

// Bluetooth Serial interface
BluetoothSerial SerialBT;

// IMU sensor instance
MPU6050 mpu;

// Flex Sensor analog input pins (direct ESP32 ADCs)
#define FLEX1 32
#define FLEX2 33
#define FLEX3 34
#define FLEX4 35
#define FLEX5 36

// Timer variables for periodic loops
unsigned long lastSendTime = 0;
unsigned long lastClientTime = 0;

// Configurable Constants (Matched to original report)
const unsigned long SEND_INTERVAL = 50;          // 50ms interval (~20Hz sampling rate)
const unsigned long ADVERTISE_TIMEOUT = 30000;    // Restart Bluetooth advertising after 30s idle

void setup() {
  // Initialize USB serial for debugging
  Serial.begin(115200);
  delay(500);

  Serial.println("=================================");
  Serial.println("ESP32 HAND GLOVE BOOT");
  Serial.println("=================================");

  // Configure analog pins as inputs
  pinMode(FLEX1, INPUT);
  pinMode(FLEX2, INPUT);
  pinMode(FLEX3, INPUT);
  pinMode(FLEX4, INPUT);
  pinMode(FLEX5, INPUT);
  Serial.println("Flex OK");

  // Initialize I2C communication (SDA=21, SCL=22)
  Wire.begin(21, 22);
  mpu.initialize();

  // Test MPU6050 connection
  if (!mpu.testConnection()) {
    Serial.println("MPU FAIL");
    // Block execution if hardware is not found
    while (1) {
      delay(100);
    }
  }
  Serial.println("MPU OK");

  // Initialize Bluetooth Serial
  SerialBT.begin("ESP32_GLOVE");
  Serial.println("BT READY: ESP32_GLOVE");
}

void loop() {
  // Check client connection state and restart advertising if disconnected for too long
  if (SerialBT.hasClient()) {
    lastClientTime = millis();
    Serial.println("BT CLIENT OK");
  } else if (millis() - lastClientTime > ADVERTISE_TIMEOUT) {
    Serial.println("BT RESTART");
    SerialBT.end();
    delay(200);
    SerialBT.begin("ESP32_GLOVE");
    lastClientTime = millis();
  }

  // Periodic sensor read and transmit loop
  if (millis() - lastSendTime >= SEND_INTERVAL) {
    lastSendTime = millis();
    if (SerialBT.hasClient()) {
      sendData();
    }
  }
}

/**
 * Acquires sensor readings, formats them as a CSV string,
 * and transmits the packet over Bluetooth Serial.
 */
void sendData() {
  // Read flex sensors directly from ESP32 ADCs (12-bit range: 0-4095)
  int f1 = analogRead(FLEX1);
  int f2 = analogRead(FLEX2);
  int f3 = analogRead(FLEX3);
  int f4 = analogRead(FLEX4);
  int f5 = analogRead(FLEX5);

  // Read raw acceleration and angular velocity from IMU
  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  /*
   * Format sensor readings:
   *   - Flex: 0-4095 raw ADC values.
   *   - Accelerometer: Raw values / 16384.0 to yield acceleration in g (±2g range sensitivity).
   *   - Gyroscope: Raw values / 131.0 to yield angular velocity in °/s (±250°/s range sensitivity).
   * 
   * Expected CSV line format:
   * flex1,flex2,flex3,flex4,flex5,ax,ay,az,gx,gy,gz
   */
  String data =
    String(f1) + "," + String(f2) + "," +
    String(f3) + "," + String(f4) + "," +
    String(f5) + "," +
    String(ax / 16384.0, 3) + "," +
    String(ay / 16384.0, 3) + "," +
    String(az / 16384.0, 3) + "," +
    String(gx / 131.0, 3) + "," +
    String(gy / 131.0, 3) + "," +
    String(gz / 131.0, 3);

  // Transmit over Bluetooth Serial
  SerialBT.println(data);
}
