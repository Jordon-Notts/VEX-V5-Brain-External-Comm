#include "CommHandler.h"

// Initialize static member
CommHandler* CommHandler::activeInstance = nullptr;

// Constructor
CommHandler::CommHandler(int cs ,int clk, int data, int led, void (*callback)(String)) {

    csPin = cs;
    clockPin = clk;
    dataPin = data;

    ledPin = led;
    onDataReceived = callback;

    // Initialize pins
    pinMode(ledPin, OUTPUT);
    digitalWrite(ledPin, LOW);

    // Set active instance for static interrupt handlers
    activeInstance = this;

    // Initialize in receive mode
    set_pins_recieve();

    // Initialize buffers
    payload = "";
    lastMessage = "";
}

// Helper function to calculate checksum
uint8_t CommHandler::calculateChecksum(const String &data) {
    uint8_t checksum = 0;
    for (char c : data) {
        checksum += c;
    }
    return checksum % 256;
}

// Function to send a single byte
void CommHandler::send_byte(uint8_t byte) {
    for (int i = 7; i >= 0; i--) {
        digitalWrite(clockPin, LOW);
        digitalWrite(dataPin, (byte >> i) & 1);
        delayMicroseconds(SENDER_DELAY_US);
        digitalWrite(clockPin, HIGH);
        delayMicroseconds(SENDER_DELAY_US);
    }
}

void CommHandler::send_string(String data) {

    // Wait until CS pin is low

    while (digitalRead(csPin) == HIGH) {
        // Optionally add a small delay to avoid busy waiting
        delayMicroseconds(1000);
    }

    set_pins_send();

    // Turn on the LED to indicate sending
    digitalWrite(ledPin, HIGH);

    uint8_t checksum = calculateChecksum(data);

    digitalWrite(csPin, HIGH);  // Activate CS
    delayMicroseconds(10);      // Small stabilization delay

    // Send length
    send_byte(data.length());

    // Send data
    for (char c : data) {
        send_byte(c);
    }

    // Send checksum
    send_byte(checksum);

    digitalWrite(csPin, LOW);  // Deactivate CS
    digitalWrite(ledPin, LOW); // Turn off sending indicator

    set_pins_recieve();
}

void CommHandler::receive_error() {
    Serial.println("Error detected. Sending 'ERROR'.");
    Serial.print("Received data (raw): ");

    // Display raw payload bits
    for (char bit : payload) {
        Serial.print(bit);
    }
    Serial.println();

    // Decode and display the length field
    if (payload.length() >= 8) {
        uint8_t length = strtol(payload.substring(0, 8).c_str(), NULL, 2);
        Serial.print("Decoded length: ");
        Serial.println(length);
    } else {
        Serial.println("Insufficient data for length decoding.");
    }

    // Decode and display the checksum
    if (payload.length() >= 16) {
        uint8_t checksumStart = payload.length() - 8;
        uint8_t receivedChecksum = strtol(payload.substring(checksumStart, checksumStart + 8).c_str(), NULL, 2);
        Serial.print("Received checksum (binary): ");
        Serial.print(payload.substring(checksumStart, checksumStart + 8));
        Serial.print(" (decimal): ");
        Serial.println(receivedChecksum);
    } else {
        Serial.println("Insufficient data for checksum decoding.");
    }

    // Decode and display data (if sufficient bits)
    if (payload.length() > 16) {
        Serial.print("Decoded data (ASCII): ");
        for (int i = 8; i < payload.length() - 8; i += 8) {
            char byte = strtol(payload.substring(i, i + 8).c_str(), NULL, 2);
            Serial.print(byte);
        }
        Serial.println();
    }

    // Uncomment to send "ERROR" if needed
    send_string("ERROR");
}

// Function to reset payload
void CommHandler::reset_payload() {
    payload = "";
}

// Function to process the received payload
void CommHandler::processPayload() {
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

// Static interrupt handlers
void CommHandler::onClockRisingEdge() {

    if (activeInstance) activeInstance->payload += digitalRead(activeInstance->dataPin) ? '1' : '0';

}

void CommHandler::onCsChange() {
    // Check if the instance is active
    if (activeInstance) {
        if (digitalRead(activeInstance->csPin) == LOW) {
            // Process the payload when CS goes low
            activeInstance->processPayload();
        } else if (digitalRead(activeInstance->csPin) == HIGH) {
            // Clear the payload when CS goes high
            activeInstance->reset_payload();
            // Serial.println("CS pin HIGH: Payload cleared.");
        }
    }
}


// Set pin modes
void CommHandler::set_pins_recieve() {

    pinMode(clockPin, INPUT);

    pinMode(dataPin, INPUT);

    pinMode(csPin, INPUT);

    attachInterrupt(digitalPinToInterrupt(clockPin), onClockRisingEdge, RISING);

    attachInterrupt(digitalPinToInterrupt(csPin), onCsChange, CHANGE);
}

void CommHandler::set_pins_send() {

    detachInterrupt(digitalPinToInterrupt(clockPin));

    detachInterrupt(digitalPinToInterrupt(csPin));

    pinMode(clockPin, OUTPUT);

    pinMode(dataPin, OUTPUT);

    pinMode(csPin, OUTPUT);

}
