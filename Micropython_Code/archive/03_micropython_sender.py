from machine import Pin
import time
from neopixel import NeoPixel

# Define pins
cs_port = Pin(20, Pin.OUT)
clock = Pin(19, Pin.OUT)
data_port = Pin(18, Pin.OUT)

led_pin = Pin(23, Pin.OUT)
pixel = NeoPixel(led_pin, 1)

# Configuration
BIT_DELAY = 0.001  # Increased delay for more stability

def send_data(data):
    """
    Sends data via clock, data, and CS pins.
    The data format includes length (1 byte), payload, and checksum.
    """
    # Calculate length and checksum
    length = len(data)
    checksum = sum(bytearray(data, 'ascii')) % 256

    # Prepare payload bits
    payload = encode_payload(length, data, checksum)

    # Begin transmission
    cs_port.on()  # Activate CS
    # pixel.fill([0, 0, 120])  # Indicate sending
    # pixel.write()
    time.sleep(BIT_DELAY)  # Short delay to stabilize

    # Send each bit
    for bit in payload:
        data_port.value(bit)  # Set data line
        clock.on()  # Clock rising edge
        time.sleep(BIT_DELAY)
        clock.off()  # Clock falling edge
        time.sleep(BIT_DELAY)

    cs_port.off()  # Deactivate CS
    # pixel.fill([0, 0, 0])  # Turn off sending indicator
    # pixel.write()
    time.sleep(BIT_DELAY)

    print("Data sent:", data)

def encode_payload(length, data, checksum):
    """
    Encodes the payload as a list of bits.
    Includes the length (8 bits), data (8 bits per character), and checksum (8 bits).
    """
    bits = []
    # Add length (8 bits)
    bits.extend(int_to_bits(length, 8))
    # Add data (8 bits per character)
    for char in data:
        bits.extend(int_to_bits(ord(char), 8))
    # Add checksum (8 bits)
    bits.extend(int_to_bits(checksum, 8))
    return bits

def int_to_bits(value, bit_count):
    """
    Converts an integer to a list of bits.
    """
    return [(value >> i) & 1 for i in range(bit_count - 1, -1, -1)]

# Example usage

import random

while True:
    message = "Hi " + str(random.randrange(11, 99))  # Simplified
    send_data(message)
    time.sleep(0.2)  # Wait before sending the next message
