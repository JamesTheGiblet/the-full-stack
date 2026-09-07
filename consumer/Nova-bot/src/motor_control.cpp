#include <Arduino.h>
#include <ArduinoJson.h> // For parsing JSON semantic capsule
#include <FS.h>          // For file system access (e.g., SPIFFS)
#include <SPIFFS.h>      // Specific for SPIFFS

// Global variables for motor driver pins, to be loaded from semantic capsule
// These are placeholder values. The Nova_bot roadmap specifies
// "Implement runtime loading of pin configurations from the semantic capsule."
// This dynamic loading would replace these hardcoded values in a future iteration.

// Motor A (e.g., Left Motor)
int MOTOR_A_IN1;
int MOTOR_A_IN2;
int MOTOR_A_EN;

// Motor B (e.g., Right Motor)
int MOTOR_B_IN1;
int MOTOR_B_IN2;
int MOTOR_B_EN;

// PWM settings for ESP32
const int freq = 30000; // PWM frequency
const int motor_a_channel = 0; // PWM channel for Motor A
const int motor_b_channel = 1; // PWM channel for Motor B
const int resolution = 8; // 8-bit resolution (0-255)

void load_pin_configurations() {
  Serial.println("Attempting to load pin configurations...");

  if (!SPIFFS.begin(true)) {
    Serial.println("SPIFFS Mount Failed! Using default hardcoded pins.");
    // Fallback to hardcoded values if SPIFFS fails
    MOTOR_A_IN1 = 27;
    MOTOR_A_IN2 = 26;
    MOTOR_A_EN = 14;
    MOTOR_B_IN1 = 33;
    MOTOR_B_IN2 = 32;
    MOTOR_B_EN = 15;
    return;
  }

  File file = SPIFFS.open("/nova_bot/pin-configuration-v1.sc.json", "r");
  if (!file) {
    Serial.println("Failed to open pin-configuration-v1.sc.json! Using default hardcoded pins.");
    // Fallback to hardcoded values if file not found
    MOTOR_A_IN1 = 27;
    MOTOR_A_IN2 = 26;
    MOTOR_A_EN = 14;
    MOTOR_B_IN1 = 33;
    MOTOR_B_IN2 = 32;
    MOTOR_B_EN = 15;
    return;
  }

  StaticJsonDocument<1024> doc; // Adjust size as needed based on your JSON capsule size
  DeserializationError error = deserializeJson(doc, file);
  if (error) {
    Serial.print("Failed to parse pin-configuration-v1.sc.json: ");
    Serial.println(error.c_str());
    Serial.println("Using default hardcoded pins.");
    // Fallback to hardcoded values if JSON parsing fails
    MOTOR_A_IN1 = 27;
    MOTOR_A_IN2 = 26;
    MOTOR_A_EN = 14;
    MOTOR_B_IN1 = 33;
    MOTOR_B_IN2 = 32;
    MOTOR_B_EN = 15;
    file.close();
    return;
  }

  file.close();

  // Extract pin values, using default hardcoded values as fallbacks if not found in JSON
  MOTOR_A_IN1 = doc["declaration"]["parameters"]["pinout"]["motor_a_left"]["in1"] | 27;
  MOTOR_A_IN2 = doc["declaration"]["parameters"]["pinout"]["motor_a_left"]["in2"] | 26;
  MOTOR_A_EN = doc["declaration"]["parameters"]["pinout"]["motor_a_left"]["ena"] | 14;

  MOTOR_B_IN1 = doc["declaration"]["parameters"]["pinout"]["motor_b_right"]["in3"] | 33; // Note: in3/in4 for motor B in the capsule
  MOTOR_B_IN2 = doc["declaration"]["parameters"]["pinout"]["motor_b_right"]["in4"] | 32;
  MOTOR_B_EN = doc["declaration"]["parameters"]["pinout"]["motor_b_right"]["enb"] | 15;

  Serial.println("Pin configurations loaded successfully from semantic capsule.");
  Serial.print("Motor A IN1: "); Serial.println(MOTOR_A_IN1);
  Serial.print("Motor A IN2: "); Serial.println(MOTOR_A_IN2);
  Serial.print("Motor A EN: "); Serial.println(MOTOR_A_EN);
  Serial.print("Motor B IN1: "); Serial.println(MOTOR_B_IN1);
  Serial.print("Motor B IN2: "); Serial.println(MOTOR_B_IN2);
  Serial.print("Motor B EN: "); Serial.println(MOTOR_B_EN);
}

void setup_motor_control() {
  load_pin_configurations(); // Load pins at setup

  // Set all the motor control pins to OUTPUT
  pinMode(MOTOR_A_IN1, OUTPUT);
  pinMode(MOTOR_A_IN2, OUTPUT);
  pinMode(MOTOR_B_IN1, OUTPUT);
  pinMode(MOTOR_B_IN2, OUTPUT);

  // Configure PWM channels
  ledcSetup(motor_a_channel, freq, resolution);
  ledcAttachPin(MOTOR_A_EN, motor_a_channel);
  ledcSetup(motor_b_channel, freq, resolution);
  ledcAttachPin(MOTOR_B_EN, motor_b_channel);

  Serial.begin(115200);
  Serial.println("Motor control initialized.");
}

// Function to set motor speed and direction
void set_motor_speed(int motor_channel, int in1_pin, int in2_pin, int speed) {
  if (speed > 0) { // Forward
    digitalWrite(in1_pin, HIGH);
    digitalWrite(in2_pin, LOW);
    ledcWrite(motor_channel, speed);
  } else if (speed < 0) { // Backward
    digitalWrite(in1_pin, LOW);
    digitalWrite(in2_pin, HIGH);
    ledcWrite(motor_channel, abs(speed));
  } else { // Stop
    digitalWrite(in1_pin, LOW);
    digitalWrite(in2_pin, LOW);
    ledcWrite(motor_channel, 0);
  }
}

// Basic mobility functions
void move_forward(int speed_val) {
  Serial.print("Moving Forward at speed: ");
  Serial.println(speed_val);
  set_motor_speed(motor_a_channel, MOTOR_A_IN1, MOTOR_A_IN2, speed_val);
  set_motor_speed(motor_b_channel, MOTOR_B_IN1, MOTOR_B_IN2, speed_val);
}

void move_backward(int speed_val) {
  Serial.print("Moving Backward at speed: ");
  Serial.println(speed_val);
  set_motor_speed(motor_a_channel, MOTOR_A_IN1, MOTOR_A_IN2, -speed_val);
  set_motor_speed(motor_b_channel, MOTOR_B_IN1, MOTOR_B_IN2, -speed_val);
}

void turn_left(int speed_val) {
  Serial.print("Turning Left at speed: ");
  Serial.println(speed_val);
  set_motor_speed(motor_a_channel, MOTOR_A_IN1, MOTOR_A_IN2, 0); // Stop left motor or move backward
  set_motor_speed(motor_b_channel, MOTOR_B_IN1, MOTOR_B_IN2, speed_val); // Move right motor forward
}

void turn_right(int speed_val) {
  Serial.print("Turning Right at speed: ");
  Serial.println(speed_val);
  set_motor_speed(motor_a_channel, MOTOR_A_IN1, MOTOR_A_IN2, speed_val); // Move left motor forward
  set_motor_speed(motor_b_channel, MOTOR_B_IN1, MOTOR_B_IN2, 0); // Stop right motor or move backward
}

void stop_motors() {
  Serial.println("Stopping Motors.");
  set_motor_speed(motor_a_channel, MOTOR_A_IN1, MOTOR_A_IN2, 0);
  set_motor_speed(motor_b_channel, MOTOR_B_IN1, MOTOR_B_IN2, 0);
}

// Example usage in Arduino loop (for testing)
/*
void loop() {
  move_forward(200);
  delay(2000);
  stop_motors();
  delay(1000);
  move_backward(150);
  delay(2000);
  stop_motors();
  delay(1000);
  turn_left(180);
  delay(1500);
  stop_motors();
  delay(1000);
  turn_right(180);
  delay(1500);
  stop_motors();
  delay(1000);
}
*/