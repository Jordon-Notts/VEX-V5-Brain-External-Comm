#ifndef COMMHANDLER_H
#define COMMHANDLER_H

#include <Arduino.h>

#define SENDER_DELAY_US 1000  // Delay for sending data in microseconds

class CommHandler {
private:
    // Pin definitions
    int clockPin;
    int dataPin;
    int csPin;
    int ledPin;

    // Buffers
    String payload;
    String lastMessage;

    // Callback for received data
    void (*onDataReceived)(String data);

    // Static pointer to the active instance
    static CommHandler* activeInstance;

    // Helper functions
    uint8_t calculateChecksum(const String &data);
    void send_byte(uint8_t byte);
    void reset_payload();

public:
    // Constructor
    CommHandler(int clk, int data, int cs, int led, void (*callback)(String));

    // Methods
    void send_string(String data);
    void processPayload();
    void receive_error();

    // Pin mode setters
    void set_pins_recieve();
    void set_pins_send();

    // Interrupt handlers
    static void onClockRisingEdge();
    static void onCsChange();
};

#endif
