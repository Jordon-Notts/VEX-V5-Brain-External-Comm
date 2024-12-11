import time

from machine import Pin

clock = Pin(19, Pin.IN, Pin.PULL_DOWN)
data_port = Pin(18, Pin.IN, Pin.PULL_DOWN)
cs_port = Pin(20, Pin.IN, Pin.PULL_DOWN)

class V5ExternalComm:

    LENGTH_FIELD_SIZE = 8
    CHECKSUM_FIELD_SIZE = 8
    PIN_CHANGE_DELAY_US = 200  # Delay in microseconds

    def __init__(self, clock, data_port, cs_port, on_message=None):
        self.cs = cs_port
        self.data = data_port
        self.clock = clock
        self.payload = []
        self.on_message = on_message

    def handle_cs_rising_edge(self, pin):

        self.payload = []

    def handle_clock_rising_edge(self, pin):

        if self.cs.value() == 1:

            self.payload.append(self.data.value())

    def handle_cs_falling_edge(self, pin):

        print(self.payload)
        
        if self.payload:
            length, data, checksum, valid = self.decode_payload(self.payload)
            if valid:
                if self.on_message:
                    self.on_message(length, data, checksum, valid)
            else:
                self.send_string("ERROR")

    def send_string(self, data_str):
        # Convert the string to a sequence of bytes
        data_bytes = data_str.encode('ascii')
        length = len(data_bytes)
        checksum = self.calculate_checksum(data_bytes)

        # Set CS high to start transmission
        self.cs.value(1)

        # Send length (1 byte)
        self.send_byte(length)

        # Send each character as a byte
        for b in data_bytes:
            self.send_byte(b)

        # Send the checksum
        self.send_byte(checksum)

        # Set CS low to end transmission
        self.cs.value(0)
        self.data.value(0)

        print("Data sent.")
        print("---------------")

    def send_byte(self, b):
        # Send a single byte bit-by-bit, MSB first
        for i in range(7, -1, -1):
            bit = (b >> i) & 1
            self.data.value(bit)
            # Pulse the clock
            self.clock.value(1)

            time.sleep_us(self.PIN_CHANGE_DELAY_US)

            self.clock.value(0)

            time.sleep_us(self.PIN_CHANGE_DELAY_US)

    def calculate_checksum(self, data_bytes):
        # Sum of ASCII values mod 256
        return sum(data_bytes) % 256

    def decode_payload(self, bits):
        index = 0
        if len(bits) < self.LENGTH_FIELD_SIZE:
            return None, None, None, False

        length_in_bytes = int(''.join(map(str, bits[index:index + self.LENGTH_FIELD_SIZE])), 2)
        index += self.LENGTH_FIELD_SIZE
        length_in_bits = length_in_bytes * 8

        if len(bits) < index + length_in_bits:

            return None, None, None, False
        
        data_bits = bits[index:index + length_in_bits]
        
        index += length_in_bits

        # Convert data_bits to string
        data_str = ''
        for i in range(0, len(data_bits), 8):
            byte_bits = data_bits[i:i+8]
            byte_val = int(''.join(map(str, byte_bits)), 2)
            data_str += chr(byte_val)

        if len(bits) < index + self.CHECKSUM_FIELD_SIZE:

            return None, None, None, False
        
        checksum = int(''.join(map(str, bits[index:index + self.CHECKSUM_FIELD_SIZE])), 2)

        calculated_checksum = sum(bytearray(data_str, 'ascii')) % 256

        valid = (checksum == calculated_checksum)

        return length_in_bytes, data_str, checksum, valid

def display_blocks(length, data, checksum, valid):
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
    print("Len: {}, Data: {}, Chksum: {}, Valid: {}".format(
        length,
        data if data else "None",
        checksum if checksum is not None else "None",
        valid
    ))


# Create an instance of BitReader with the callback
arduino = V5ExternalComm(
    clock=clock,
    data_port=data_port,
    cs_port=cs_port,
    on_message=display_blocks
)

cs_port.irq(trigger=cs_port.IRQ_RISING, handler=arduino.handle_cs_rising_edge)
cs_port.irq(trigger=cs_port.IRQ_FALLING, handler=arduino.handle_cs_falling_edge)
clock.irq(trigger=clock.IRQ_RISING, handler=arduino.handle_clock_rising_edge)

# Main loop
while True:
    # Main loop is idle; processing is handled by interrupts and the callback
    pass
