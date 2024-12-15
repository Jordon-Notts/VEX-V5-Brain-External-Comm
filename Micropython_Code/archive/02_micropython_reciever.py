from machine import Pin
from neopixel import NeoPixel
import time

clock = Pin(19, Pin.IN)
data_port = Pin(18, Pin.IN)
cs_port = Pin(20, Pin.IN)

led_pin = Pin(23, Pin.OUT)

pixel = NeoPixel(led_pin,1)

class V5ExternalComm:
    """
    A class to handle bit reading via clock, data, and chip select (CS) pins.
    """
    LENGTH_FIELD_SIZE = 8  # Fixed size for length field (in bits)
    CHECKSUM_FIELD_SIZE = 8  # Fixed size for checksum field (in bits)

    def __init__(self, clock, data_port, cs_port, on_error=None, on_message=None):
        """
        Initialize the BitReader instance.

        Parameters:
        - clock: DigitalIn
            The clock pin, used to trigger data bit reading on rising edges.
        - data_port: DigitalIn
            The data pin, which carries the bits to be read.
        - cs_port: DigitalIn
            The chip select (CS) pin, used to signal the start and end of data transmission.
        - on_message: Callable (optional)
            A user-defined callback function to process the received payload. It should accept
            length, data, checksum, and validity as arguments.
        """
        # Initialize pins
        self.cs_pin = cs_port  # CS pin
        self.data_pin = data_port  # Data pin
        self.clock_pin = clock  # Clock pin

        # Initialize payload
        self.payload = []

        # User-defined callback
        self.on_message = on_message
        self.on_error = on_error

    def handle_cs_rising_edge(self, pin):
        # Reset payload for the next sequence
        # print("Payload reset")
        self.payload = []

    def handle_clock_rising_edge(self, pin):
        """
        Handle clock rising edge to read a data bit.
        """
        # Check if CS is active (high)
        if self.cs_pin.value() == 1:
            # Read the data pin and append the bit to the payload
            self.payload.append(self.data_pin.value())

    def handle_cs_falling_edge(self, pin):
        """
        Handle CS falling edge to process the payload.
        """

        if self.payload:
            # Decode the payload into its components
            length, data, checksum, valid = self.decode_payload(self.payload)

            if valid:
                # Trigger the on_message callback if defined
                if self.on_message:
                    self.on_message(data)
            else:
                if self.on_error:
                    self.on_error([length, data, checksum, valid])

        self.handle_cs_rising_edge(pin)

    def decode_payload(self, bits):
        index = 0

        # Read length (in bytes)
        if len(bits) < self.LENGTH_FIELD_SIZE:
            return None, None, None, False

        length_in_bytes = int(''.join(map(str, bits[index:index + self.LENGTH_FIELD_SIZE])), 2)
        index += self.LENGTH_FIELD_SIZE

        length_in_bits = length_in_bytes * 8

        # Read data (as bits first)
        if len(bits) < index + length_in_bits:
            return None, None, None, False
        data_bits = bits[index:index + length_in_bits]
        index += length_in_bits

        # Convert data_bits to a string
        data_str = ''
        for i in range(0, len(data_bits), 8):
            byte_bits = data_bits[i:i+8]
            byte_val = int(''.join(map(str, byte_bits)), 2)
            data_str += chr(byte_val)

        # Read checksum
        if len(bits) < index + self.CHECKSUM_FIELD_SIZE:
            return None, None, None, False
        checksum = int(''.join(map(str, bits[index:index + self.CHECKSUM_FIELD_SIZE])), 2)

        # Calculate checksum for validation (using ASCII values)
        calculated_checksum = sum(bytearray(data_str, 'ascii')) % 256
        valid = checksum == calculated_checksum

        return length_in_bytes, data_str, checksum, valid

def data_recieved(data):
    """
    Callback to display the received blocks on the Brain's screen.

    Parameters:
    - length: int
        Length of the data block.
    - data: str
        The data string of the block.
    - checksum: int
        The checksum of the block.
    - valid: bool
        Whether the checksum is valid.
    """
    pixel.fill([0,80,0])
    pixel.write()
    print("Data: '{}'".format(data))
    time.sleep(0.04)
    pixel.fill([0,0,0])
    pixel.write()

def error(message):
    pixel.fill([80,0,0])
    pixel.write()
    print("ERROR")
    time.sleep(0.04)
    pixel.fill([0,0,0])
    pixel.write()

# Create an instance of BitReader with the callback
arduino = V5ExternalComm(
    clock=clock,
    data_port=data_port,
    cs_port=cs_port,
    on_message=data_recieved,
    on_error=error
)

cs_port.irq(trigger=cs_port.IRQ_RISING, handler=arduino.handle_cs_rising_edge)
cs_port.irq(trigger=cs_port.IRQ_FALLING, handler=arduino.handle_cs_falling_edge)
clock.irq(trigger=clock.IRQ_RISING, handler=arduino.handle_clock_rising_edge)

# Main loop
while True:
    # Main loop is idle; processing is handled by interrupts and the callback
    pass


