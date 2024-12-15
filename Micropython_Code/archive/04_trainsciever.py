from machine import Pin
import time
from neopixel import NeoPixel

global cs_pin_number
global clock_pin_number
global data_pin_number

# Define pins
cs_pin_number = 20
clock_pin_number = 19
data_pin_number = 18

global cs_pin
global clock_pin
global data_pin

global pixel

led_pin = Pin(23, Pin.OUT)
pixel = NeoPixel(led_pin,1)

# Configuration
BIT_DELAY_US = 1000  # Delay for sending bits in microseconds
MAX_PAYLOAD_SIZE = 256  # Maximum payload size in bits

# Buffers and state variables
payload = []  # Received payload buffer
last_message = ""  # Last valid message

# Helper Functions

def calculate_checksum(data):
    """
    Calculate the checksum of a string.
    """
    return sum(bytearray(data, 'ascii')) % 256

def int_to_bits(value, bit_count):
    """
    Convert an integer to a list of bits.
    """
    return [(value >> i) & 1 for i in range(bit_count - 1, -1, -1)]

def encode_payload(length, data, checksum):
    """
    Encode length, data, and checksum into a payload.
    """
    bits = int_to_bits(length, 8)  # Length as 8 bits
    for char in data:
        bits.extend(int_to_bits(ord(char), 8))  # Each char as 8 bits
    bits.extend(int_to_bits(checksum, 8))  # Checksum as 8 bits
    return bits

def send_data(data):
    """
    Send data via clock, data, and CS pins.
    """
    global cs_pin, clock_pin, data_pin,  pixel

    set_pins_recieve()

    # Wait until CS pin is LOW
    while cs_pin.value() == 1:
        print(cs_pin.value())
        time.sleep_us(10)

    set_pins_send()

    # Turn on the LED to indicate sending
    pixel.fill([0,0,120])
    pixel.write()

    # Calculate length and checksum
    length = len(data)
    checksum = calculate_checksum(data)
    payload = encode_payload(length, data, checksum)

    # Activate CS pin
    cs_pin.on()
    time.sleep_us(10)

    # Send payload
    for bit in payload:
        data_pin.init(Pin.OUT)
        data_pin.value(bit)
        clock_pin.init(Pin.OUT)
        clock_pin.on()
        time.sleep_us(BIT_DELAY_US)
        clock_pin.off()
        time.sleep_us(BIT_DELAY_US)

    # Deactivate CS pin
    cs_pin.off()

    # Turn off the LED
    pixel.fill([0,0,0])
    pixel.write()

    print(f"Data sent: {data}")

def reset_payload():
    """
    Clear the payload buffer.
    """
    global payload
    payload = []

def process_payload():
    """
    Process the received payload.
    """
    global payload, last_message

    if len(payload) < 16:
        return

    # Decode length
    length_bits = payload[:8]
    length = int("".join(map(str, length_bits)), 2)

    if len(payload) >= (8 + length * 8 + 8):
        # Decode data
        data_bits = payload[8:8 + length * 8]
        data = "".join(
            chr(int("".join(map(str, data_bits[i:i + 8])), 2)) for i in range(0, len(data_bits), 8))

        # Decode checksum
        checksum_bits = payload[8 + length * 8:8 + length * 8 + 8]
        received_checksum = int("".join(map(str, checksum_bits)), 2)

        # Validate checksum
        if received_checksum == calculate_checksum(data):
            if data == "ERROR":
                send_data(last_message)  # Resend the last message
            else:
                last_message = data  # Update the last valid message
                print(f"Received: {data}")
        else:
            receive_error()
        reset_payload()

def receive_error():
    """
    Handle receive errors.
    """
    print("Error detected. Sending 'ERROR'.")
    print("Received data (raw):", "".join(map(str, payload)))
    send_data("ERROR")

def clock_change(pin):
    """
    Handle clock rising edge to read a bit.
    """
    global payload

    if cs_pin.value() == 1:  # Only read when CS is active (LOW)
        if len(payload) < MAX_PAYLOAD_SIZE:
            payload.append(data_pin.value())

def cs_change(pin):
    """
    Handle CS pin changes to start or stop reception.
    """
    if cs_pin.value() == 1:  # CS HIGH: End of transmission
        reset_payload()
    else:  # CS LOW: Start of transmission
        process_payload()

def set_pins_recieve():

    global cs_pin
    global clock_pin
    global data_pin

    global cs_pin_number
    global clock_pin_number
    global data_pin_number

    cs_pin = Pin(cs_pin_number, Pin.IN)
    clock_pin = Pin(clock_pin_number, Pin.IN)
    data_pin = Pin(data_pin_number, Pin.IN)

    cs_pin.irq(trigger=cs_pin.IRQ_RISING, handler=cs_change)
    cs_pin.irq(trigger=cs_pin.IRQ_FALLING, handler=cs_change)

    clock_pin.irq(trigger=clock_pin.IRQ_RISING, handler=clock_change)

def set_pins_send():

    global cs_pin
    global clock_pin
    global data_pin

    global cs_pin_number
    global clock_pin_number
    global data_pin_number

    cs_pin = Pin(cs_pin_number, Pin.OUT)
    clock_pin = Pin(clock_pin_number, Pin.OUT)
    data_pin = Pin(data_pin_number, Pin.OUT)

    cs_pin.value(0)
    clock_pin.value(0)
    data_pin.value(0)

set_pins_recieve()

while True:
    
    pass

    # Example: Send data periodically
    # message = f"Hi{int(time.ticks_ms() / 1000)}"
    # send_data(message)
    # time.sleep(1)