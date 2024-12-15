from machine import Pin
import time
from neopixel import NeoPixel

class V5ExternalComm:
    def __init__(self, cs_pin_number, clock_pin_number, data_pin_number, led_pin_number):
        # Initialize pin numbers
        self.cs_pin_number = cs_pin_number
        self.clock_pin_number = clock_pin_number
        self.data_pin_number = data_pin_number

        # State variables
        self.payload = []
        self.last_message = ""

        # LED setup
        self.led_pin = Pin(led_pin_number, Pin.OUT)
        self.pixel = NeoPixel(self.led_pin, 1)

        # Pin configurations
        self.cs_pin = None
        self.clock_pin = None
        self.data_pin = None

        # Configuration constants
        self.BIT_DELAY_US = 1000
        self.MAX_PAYLOAD_SIZE = 256

        self.reciving = False

        # Initial setup
        self.set_pins_receive()

    def calculate_checksum(self, data):
        """Calculate the checksum of a string."""
        return sum(bytearray(data, 'ascii')) % 256

    def int_to_bits(self, value, bit_count):
        """Convert an integer to a list of bits."""
        return [(value >> i) & 1 for i in range(bit_count - 1, -1, -1)]

    def encode_payload(self, length, data, checksum):
        """Encode length, data, and checksum into a payload."""
        bits = self.int_to_bits(length, 8)  # Length as 8 bits
        for char in data:
            bits.extend(self.int_to_bits(ord(char), 8))  # Each char as 8 bits
        bits.extend(self.int_to_bits(checksum, 8))  # Checksum as 8 bits
        return bits

    def send_data(self, data):
        """Send data via clock, data, and CS pins."""

        self.set_pins_receive()

        # Wait until CS pin is LOW
        while self.cs_pin.value() == 1:

            time.sleep_us(10)

        self.set_pins_send()

        # Turn on the LED to indicate sending
        self.pixel.fill([0, 0, 120])
        self.pixel.write()

        # Calculate length and checksum
        length = len(data)
        checksum = self.calculate_checksum(data)
        payload = self.encode_payload(length, data, checksum)

        # Activate CS pin
        self.cs_pin.on()
        time.sleep_us(10)

        # Send payload
        for bit in payload:
            # self.data_pin.init(Pin.OUT)
            self.data_pin.value(bit)
            # self.clock_pin.init(Pin.OUT)
            self.clock_pin.on()
            time.sleep_us(self.BIT_DELAY_US)
            self.clock_pin.off()
            time.sleep_us(self.BIT_DELAY_US)

        # Deactivate CS pin
        self.cs_pin.off()

        # Turn off the LED
        self.pixel.fill([0, 0, 0])
        self.pixel.write()

        print(f"Data sent: {data}")

        self.set_pins_receive()

    def reset_payload(self):
        """Clear the payload buffer."""
        self.payload = []

    def process_payload(self):
        """Process the received payload."""
        if len(self.payload) < 16:
            return

        # Decode length
        length_bits = self.payload[:8]
        length = int("".join(map(str, length_bits)), 2)

        if len(self.payload) >= (8 + length * 8 + 8):
            # Decode data
            data_bits = self.payload[8:8 + length * 8]
            data = "".join(
                chr(int("".join(map(str, data_bits[i:i + 8])), 2)) for i in range(0, len(data_bits), 8))

            # Decode checksum
            checksum_bits = self.payload[8 + length * 8:8 + length * 8 + 8]
            received_checksum = int("".join(map(str, checksum_bits)), 2)

            # Validate checksum
            if received_checksum == self.calculate_checksum(data):
                if data == "ERROR":
                    self.send_data(self.last_message)  # Resend the last message
                else:
                    self.last_message = data  # Update the last valid message
                    print(f"Received: {data}")
            else:
                self.receive_error()
            self.reset_payload()

    def receive_error(self):
        """Handle receive errors."""
        print("Error detected. Sending 'ERROR'.")
        print("Received data (raw):", "".join(map(str, self.payload)))
        self.send_data("ERROR")

    def clock_change(self, pin):
        """Handle clock rising edge to read a bit."""
        if self.reciving == True:
            if self.cs_pin.value() == 1:  # Only read when CS is active (LOW)
                if len(self.payload) < self.MAX_PAYLOAD_SIZE:
                    self.payload.append(self.data_pin.value())

    def cs_change(self, pin):
        """Handle CS pin changes to start or stop reception."""
        if self.reciving == True:
            if self.cs_pin.value() == 1:  # CS HIGH: End of transmission
                self.reset_payload()
                self.pixel.fill([0,0,120])
                self.pixel.write()
            else:  # CS LOW: Start of transmission
                self.process_payload()
                self.pixel.fill([0,0,0])
                self.pixel.write()

    def set_pins_receive(self):
        """Set pins to receive mode."""

        self.cs_pin = Pin(self.cs_pin_number, Pin.IN)
        self.clock_pin = Pin(self.clock_pin_number, Pin.IN)
        self.data_pin = Pin(self.data_pin_number, Pin.IN)

        self.cs_pin.irq(trigger=Pin.IRQ_RISING, handler=self.cs_change)
        self.cs_pin.irq(trigger=Pin.IRQ_FALLING, handler=self.cs_change)

        self.clock_pin.irq(trigger=Pin.IRQ_RISING, handler=self.clock_change)

        self.reciving = True

    def set_pins_send(self):
        """Set pins to send mode."""

        self.reciving = False

        self.cs_pin = Pin(self.cs_pin_number, Pin.OUT)
        self.clock_pin = Pin(self.clock_pin_number, Pin.OUT)
        self.data_pin = Pin(self.data_pin_number, Pin.OUT)

        self.cs_pin.value(0)
        self.clock_pin.value(0)
        self.data_pin.value(0)


# Example Usage
transceiver = V5ExternalComm(cs_pin_number=20, clock_pin_number=19, data_pin_number=18, led_pin_number=23)

while True:
    pass  # Main loop
    transceiver.send_data("Hello")
    time.sleep(0.2)