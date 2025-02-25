from vex import *

# Initialize the brain
brain = Brain()

class V5ExternalComm:
    """
    A class to handle bit reading via clock, data, and chip select (CS) pins.
    """
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
            a list of decoded data blocks.
        """

        # Initialize pins
        self.cs = cs_port  # CS pin
        self.data = data_port  # Data pin
        self.clock = clock  # Clock pin

        # Initialize payload
        self.payload = []

        # User-defined callback
        self.on_message = on_message

        # Set up interrupts
        self.clock.high(self.clock_pin_rising_edge)  # Trigger on rising edge of clock
        self.cs.low(self.cs_pin_falling_edge)  # Trigger on falling edge of CS

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
            # Convert the payload to data blocks
            data_blocks = self.decode_payload(self.payload)

            # Trigger the on_message callback if defined
            if self.on_message:
                self.on_message(data_blocks)

            # Reset payload for the next sequence
            self.payload = []

    def decode_payload(self,bits):
        """
        Decode the bit payload into a series of data blocks.

        Parameters:
        - bits: list of int
            The raw list of bits.

        Returns:
        - list of dict
            A list of decoded data blocks in the format:
            {"length": int, "data": list of int, "checksum": int, "valid": bool}
        """
        index = 0
        blocks = []

        while index < len(bits):
            # Read length (assume 8 bits for length)
            if index + 8 > len(bits):
                break
            length = int(''.join(map(str, bits[index:index + 8])), 2)
            index += 8

            # Read data (length bits)
            if index + length > len(bits):
                break
            data = bits[index:index + length]
            index += length

            # Read checksum (assume 8 bits for checksum)
            if index + 8 > len(bits):
                break
            checksum = int(''.join(map(str, bits[index:index + 8])), 2)
            index += 8

            # Calculate checksum for validation
            calculated_checksum = sum(data) % 256

            # Append the decoded block
            blocks.append({
                "length": length,
                "data": data,
                "checksum": checksum,
                "valid": (checksum == calculated_checksum)
            })

        return blocks

def display_blocks(blocks):
    """
    Callback to display the received blocks on the Brain's screen.

    Parameters:
    - blocks: list of dict
        A list of decoded data blocks.
    """
    brain.screen.clear_screen()
    for block in blocks:
        brain.screen.print("Len: {}, Data: {}, Valid: {}".format(
            block["length"],
            ''.join(map(str, block["data"])),
            block["valid"]
        ))
        brain.screen.next_row()


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