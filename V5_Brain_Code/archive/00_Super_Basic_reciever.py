from vex import *

# Initialize the brain and payload
brain = Brain()

payload = []

def clock_pin_rising_edge():
    """
    Handle clock rising edge to read a data bit.
    """
    global payload
    # Check if CS is active (high)
    if cs.value() == 1:
        # Read the data pin and append the bit to the payload
        payload.append(data.value())

def cs_pin_falling_edge():
    """
    Handle CS falling edge to process the payload.
    """
    global payload
    if payload:
        # Display the bits on the Brain's screen
        display_bits(payload)
        # Reset payload for the next sequence
        payload = []

def display_bits(bits):
    """
    Display the received bits on the Brain's screen.

    Parameters:
    - bits: list of int
        The list of bits received during the last data transmission.
    """
    brain.screen.clear_screen()
    brain.screen.print("Bits: {}".format(''.join(map(str, bits))))

# Initialize the pins
clock = DigitalIn(brain.three_wire_port.a)
data = DigitalIn(brain.three_wire_port.b)
cs = DigitalIn(brain.three_wire_port.c)

# Set up interrupts
clock.high(clock_pin_rising_edge)  # Trigger on rising edge of clock
cs.low(cs_pin_falling_edge)  # Trigger on falling edge of CS

# Main loop
while True:
    # Main loop is idle; processing is handled by interrupts
    pass
