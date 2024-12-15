#include <Arduino.h>

#define CLOCK_PIN 2
#define DATA_PIN  3
#define CS_PIN    4
#define LED_PIN   13

// Pin definitions
int clockPin;
int dataPin;
int csPin;
int ledPin;

// Buffers
String payload;
String lastMessage;

// Callback for data received
void (*onDataReceived)(String data);

// Define delay for sending data
#define SENDER_DELAY_US 20  // Delay in microseconds

// Helper function to calculate checksum
uint8_t calculateChecksum(const String &data) {
    uint8_t checksum = 0;
    for (char c : data) {
        checksum += c;
    }
    return checksum % 256;
}

// Function to send a single byte
void send_byte(uint8_t byte) {
    for (int i = 7; i >= 0; i--) {
        digitalWrite(clockPin, LOW);
        digitalWrite(dataPin, (byte >> i) & 1);
        delayMicroseconds(SENDER_DELAY_US);
        digitalWrite(clockPin, HIGH);
        delayMicroseconds(SENDER_DELAY_US);
    }
}

// Function to send a string
void send_string(String data) {

    set_pins_send();

    digitalWrite(ledPin, HIGH); // Indicate sending
    uint8_t checksum = calculateChecksum(data);

    digitalWrite(csPin, HIGH);
    delayMicroseconds(10);

    send_byte(data.length());
    for (char c : data) send_byte(c);
    send_byte(checksum);

    digitalWrite(csPin, LOW);
    digitalWrite(ledPin, LOW); // Indicate completion

    set_pins_recieve();
}

// Function to handle receive errors
void receive_error() {

    Serial.println("Error detected. Sending 'ERROR'.");

    send_string("ERROR");
}

// Function to reset payload
void reset_payload() {
    payload = "";
}

// Function to process the received payload
void processPayload() {
    if (payload.length() < 16) return;

    uint8_t length = strtol(payload.substring(0, 8).c_str(), NULL, 2);
    if (payload.length() >= (8 + length * 8 + 8)) {
        String data = "";
        for (int i = 8; i < 8 + length * 8; i += 8) {
            char byte = strtol(payload.substring(i, i + 8).c_str(), NULL, 2);
            data += byte;
        }

        uint8_t receivedChecksum = strtol(payload.substring(8 + length * 8, 8 + length * 8 + 8).c_str(), NULL, 2);
        if (receivedChecksum == calculateChecksum(data)) {

            if (data == "ERROR") send_string(lastMessage);

            else lastMessage = data, onDataReceived(data);

        } else receive_error();

        reset_payload();
    }
}

// Interrupt handlers
void onClockRisingEdge() {

    if (digitalRead(csPin) == HIGH) payload += digitalRead(dataPin) ? '1' : '0';
}

void onCsChange() {

    if (digitalRead(csPin) == LOW) processPayload();
}

// Set pin modes
void set_pins_recieve() {

    pinMode(clockPin, INPUT); pinMode(dataPin, INPUT); pinMode(csPin, INPUT);

    attachInterrupt(digitalPinToInterrupt(clockPin), onClockRisingEdge, RISING);

    attachInterrupt(digitalPinToInterrupt(csPin), onCsChange, CHANGE);

}

void set_pins_send() {

    detachInterrupt(digitalPinToInterrupt(clockPin));

    detachInterrupt(digitalPinToInterrupt(csPin));

    pinMode(clockPin, OUTPUT); pinMode(dataPin, OUTPUT); pinMode(csPin, OUTPUT);

}

// Initialization function
void initializePins(int clk, int data, int cs, int led, void (*callback)(String)) {

    clockPin = clk; dataPin = data; csPin = cs; ledPin = led; onDataReceived = callback;

    pinMode(ledPin, OUTPUT); digitalWrite(ledPin, LOW);

    set_pins_recieve(); payload = ""; lastMessage = "";

}

// Example callback
void exampleCallback(String data) {

    Serial.print("Received: "); Serial.println(data);

    digitalWrite(ledPin, HIGH);

    delay(10);

    digitalWrite(ledPin, LOW);

}

void setup() {

    Serial.begin(115200);

    initializePins(CLOCK_PIN, DATA_PIN, CS_PIN, LED_PIN, exampleCallback);

}

String working_string;

void loop() {

    // working_string = "Test_message" + millis();

    // send_string(working_string);

    // delay(1000);
}
