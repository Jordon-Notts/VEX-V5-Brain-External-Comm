#include <Arduino.h>
#include "CommHandler.h"

#define CS_PIN    2
#define CLOCK_PIN 3
#define DATA_PIN  4
#define LED_PIN   13

// Example callback function
void exampleCallback(String data) {

  Serial.print("Received: ");

  Serial.println(data);
  
}

// Instantiate CommHandler object
CommHandler comm(CS_PIN, CLOCK_PIN, DATA_PIN, LED_PIN, exampleCallback);

void setup() {

  Serial.begin(115200);
}

void loop() {

  String working_string = "12345";

  comm.send_string(working_string);

  Serial.println(working_string);

  delay(1000);
}
