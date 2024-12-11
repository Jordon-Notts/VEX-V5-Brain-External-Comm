from vex import *

brain = Brain()

class V5ExternalComm:
    """
    A class to handle bit reading via clock, data, and chip select (CS) pins.
    """
    LENGTH_FIELD_SIZE = 8  # Fixed size for length field (in bits)
    CHECKSUM_FIELD_SIZE = 8  # Fixed size for checksum field (in bits)

    def __init__(self, clock, data_port, cs_port, on_message=None):
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
        self.cs = cs_port  # CS pin
        self.data = data_port  # Data pin
        self.clock = clock  # Clock pin

        # Initialize payload
        self.payload = []

        # User-defined callback
        self.on_message = on_message

    def clock_pin_rising_edge(self):
        """
        Handle clock rising edge to read a data bit.
        """
        # Check if CS is active (high)
        if self.cs.value() == 1:
            # Read the data pin and append the bit to the payload
            self.payload.append(self.data.value())

    def cs_pin_falling_edge(self):
        """
        Handle CS falling edge to process the payload.
        """
        if self.payload:
            # Decode the payload into its components
            length, data, checksum, valid = self.decode_payload(self.payload)

            # Trigger the on_message callback if defined
            if self.on_message:
                self.on_message(length, data, checksum, valid)

            # Reset payload for the next sequence
            self.payload = []

    def decode_payload(self, bits):
        """
        Decode the bit payload into a data block.

        Parameters:
        - bits: list of int
            The raw list of bits.

        Returns:
        - length: int
            The length of the data block.
        - data: list of int
            The extracted data bits.
        - checksum: int
            The checksum of the data block.
        - valid: bool
            Whether the checksum matches the calculated checksum.
        """
        index = 0

        # Read length (assume fixed LENGTH_FIELD_SIZE bits)
        if len(bits) < self.LENGTH_FIELD_SIZE:
            return None, None, None, False
        length = int(''.join(map(str, bits[index:index + self.LENGTH_FIELD_SIZE])), 2)
        index += self.LENGTH_FIELD_SIZE

        # Read data (length bits)
        if len(bits) < index + length:
            return None, None, None, False
        data = bits[index:index + length]
        index += length

        # Read checksum (assume fixed CHECKSUM_FIELD_SIZE bits)
        if len(bits) < index + self.CHECKSUM_FIELD_SIZE:
            return None, None, None, False
        checksum = int(''.join(map(str, bits[index:index + self.CHECKSUM_FIELD_SIZE])), 2)

        # Calculate checksum for validation
        calculated_checksum = sum(data) % 256
        valid = checksum == calculated_checksum

        return length, data, checksum, valid

def display_blocks(length, data, checksum, valid):
    """
    Callback to display the received blocks on the Brain's screen.

    Parameters:
    - length: int
        Length of the data block.
    - data: list of int
        The data bits of the block.
    - checksum: int
        The checksum of the block.
    - valid: bool
        Whether the checksum is valid.
    """
    brain.screen.clear_screen()
    brain.screen.print("Len: {}, Data: {}, Chksum: {}, Valid: {}".format(
        length,
        ''.join(map(str, data)) if data else "None",
        checksum if checksum is not None else "None",
        valid
    ))

clock=DigitalIn(brain.three_wire_port.a),
data_port=DigitalIn(brain.three_wire_port.b),
cs_port=DigitalIn(brain.three_wire_port.c)

# Create an instance of BitReader with the callback
arduino = V5ExternalComm(
    clock=clock,
    data_port=data_port,
    cs_port=cs_port,
    on_message=display_blocks
)

# Set up interrupts
clock.high(arduino.clock_pin_rising_edge)  # Trigger on rising edge of clock
cs_port.low(arduino.cs_pin_falling_edge)  # Trigger on falling edge of CS

# Main loop
while True:
    # Main loop is idle; processing is handled by interrupts and the callback
    pass