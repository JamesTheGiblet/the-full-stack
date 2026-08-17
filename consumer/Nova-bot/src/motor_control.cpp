/**
 * @file motor_control.cpp
 * @brief Basic motor control sketch for the Nova-bot ESP32 platform.
 * @version 0.1
 * @date 2026-08-16
 *
 * Implements the first firmware requirement from ROADMAP.md: Basic Motor Control.
 * This sketch provides functions to control two TT motors via a standard
 * L298N H-bridge driver. It uses the ESP32's LEDC peripheral for PWM speed control.
 *
 * Pinout (assumes a standard L298N driver):
 * - These are example pins and may need to be changed based on your wiring.
 * - Connect the motor driver's 5V and GND to the ESP32's 5V and GND.
 * - Connect the motor power supply to the driver's VMS and GND.
 */

#include <Arduino.h>

// --- Pin Configuration ---
// This struct centralizes pin definitions. In a future version, this will be
// populated by parsing a configuration file (e.g., pin-configuration-v1.sc.json)
// from the ESP32's filesystem instead of being hardcoded.
struct MotorPins {
    // Motor A (Left)
    const int ENA = 14; // PWM Speed Control for Left Motor
    const int IN1 = 25; // Direction Control 1 for Left Motor
    const int IN2 = 26; // Direction Control 2 for Left Motor

    // Motor B (Right)
    const int ENB = 12; // PWM Speed Control for Right Motor
    const int IN3 = 27; // Direction Control 1 for Right Motor
    const int IN4 = 13; // Direction Control 2 for Right Motor
};

// Create an instance of the pin configuration.
MotorPins pins;

// --- PWM Configuration ---
const int PWM_FREQ = 5000; // PWM frequency in Hz
const int PWM_RESOLUTION = 8; // 8-bit resolution (0-255)
const int PWM_CHANNEL_A = 0; // LEDC channel 0 for Left Motor
const int PWM_CHANNEL_B = 1; // LEDC channel 1 for Right Motor

// --- Motor Control Functions ---

/**
 * @brief Stops both motors.
 */
void stopMotors() {
    digitalWrite(pins.IN1, LOW);
    digitalWrite(pins.IN2, LOW);
    digitalWrite(pins.IN3, LOW);
    digitalWrite(pins.IN4, LOW);
    ledcWrite(PWM_CHANNEL_A, 0);
    ledcWrite(PWM_CHANNEL_B, 0);
}

/**
 * @brief Moves the robot forward at a given speed.
 * @param speed PWM duty cycle (0-255).
 */
void moveForward(int speed) {
    digitalWrite(pins.IN1, HIGH);
    digitalWrite(pins.IN2, LOW);
    digitalWrite(pins.IN3, HIGH);
    digitalWrite(pins.IN4, LOW);
    ledcWrite(PWM_CHANNEL_A, speed);
    ledcWrite(PWM_CHANNEL_B, speed);
}

/**
 * @brief Moves the robot backward at a given speed.
 * @param speed PWM duty cycle (0-255).
 */
void moveBackward(int speed) {
    digitalWrite(pins.IN1, LOW);
    digitalWrite(pins.IN2, HIGH);
    digitalWrite(pins.IN3, LOW);
    digitalWrite(pins.IN4, HIGH);
    ledcWrite(PWM_CHANNEL_A, speed);
    ledcWrite(PWM_CHANNEL_B, speed);
}

/**
 * @brief Turns the robot right (on the spot) at a given speed.
 * @param speed PWM duty cycle (0-255).
 */
void turnRight(int speed) {
    digitalWrite(pins.IN1, HIGH); // Left motor forward
    digitalWrite(pins.IN2, LOW);
    digitalWrite(pins.IN3, LOW);  // Right motor backward
    digitalWrite(pins.IN4, HIGH);
    ledcWrite(PWM_CHANNEL_A, speed);
    ledcWrite(PWM_CHANNEL_B, speed);
}

/**
 * @brief Turns the robot left (on the spot) at a given speed.
 * @param speed PWM duty cycle (0-255).
 */
void turnLeft(int speed) {
    digitalWrite(pins.IN1, LOW);  // Left motor backward
    digitalWrite(pins.IN2, HIGH);
    digitalWrite(pins.IN3, HIGH); // Right motor forward
    digitalWrite(pins.IN4, LOW);
    ledcWrite(PWM_CHANNEL_A, speed);
    ledcWrite(PWM_CHANNEL_B, speed);
}

// --- Main Program ---

void setup() {
    // Set motor control pins as outputs
    pinMode(pins.IN1, OUTPUT);
    pinMode(pins.IN2, OUTPUT);
    pinMode(pins.IN3, OUTPUT);
    pinMode(pins.IN4, OUTPUT);

    // Configure LEDC PWM channels
    ledcSetup(PWM_CHANNEL_A, PWM_FREQ, PWM_RESOLUTION);
    ledcSetup(PWM_CHANNEL_B, PWM_FREQ, PWM_RESOLUTION);

    // Attach PWM pins to channels
    ledcAttachPin(pins.ENA, PWM_CHANNEL_A);
    ledcAttachPin(pins.ENB, PWM_CHANNEL_B);

    // Start with motors stopped
    stopMotors();
}

void loop() {
    // This is a simple demonstration sequence.
    // In the final robot, this loop will be replaced by the main Sense->Decide->Act logic.

    moveForward(200); // Move forward at 80% speed
    delay(2000);
    stopMotors();
    delay(1000);

    moveBackward(200); // Move backward at 80% speed
    delay(2000);
    stopMotors();
    delay(1000);

    turnRight(180); // Turn right at 70% speed
    delay(1500);
    stopMotors();
    delay(1000);

    turnLeft(180); // Turn left at 70% speed
    delay(1500);
    stopMotors();
    delay(1000);
}