from vex import *

# Initialize the brain
brain = Brain()

class V5ExternalComm:
    """
    A class to handle bit reading via clock, data, and chip select (CS) pins.
    """
    def __init__(self, clock, data_port, cs_port):
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
            a single argument, which is a list of bits.
        """

        # Initialize pins
        self.cs = cs_port  # CS pin
        self.data = data_port  # Data pin
        self.clock = clock  # Clock pin

        # Initialize payload
        self.payload = []

    def handle_clock_rising_edge(self):
        """
        Handle clock rising edge to read a data bit.
        """
        # Check if CS is active (high)
        if self.cs.value() == 1:
            # Read the data pin and append the bit to the payload
            self.payload.append(self.data.value())

    def handle_cs_falling_edge(self):
        """
        Handle CS falling edge to process the payload.
        """
        if self.payload:

            brain.screen.clear_screen()
            brain.screen.print("Bits: {}".format(''.join(map(str, self.payload))))

            # Reset payload for the next sequence
            self.payload = []

clock=DigitalIn(brain.three_wire_port.a),
data_port=DigitalIn(brain.three_wire_port.b),
cs_port=DigitalIn(brain.three_wire_port.c)

# Create an instance of BitReader with the callback
bit_reader = V5ExternalComm(
    clock=clock,
    data_port=data_port,
    cs_port=cs_port
)

# Set up interrupts
clock.high(bit_reader.handle_clock_rising_edge)  # Trigger on rising edge of clock
cs_port.low(bit_reader.handle_cs_falling_edge)  # Trigger on falling edge of CS

# Main loop
while True:
    # Main loop is idle; processing is handled by interrupts and the callback
    pass