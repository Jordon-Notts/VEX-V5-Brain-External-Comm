import vex as vx
import time

# Initialize the brain and input pin
brain = vx.Brain()

# Variables to track timing and state

port_a = vx.AnalogIn(brain.three_wire_port.a)

def print_to_brain(message, row):
    """Utility to print messages on the VEX Brain screen."""
    brain.screen.clear_row(row)
    brain.screen.set_cursor(row, 1)
    brain.screen.print(message)

# Main loop for edge detection
while True:
    print_to_brain(port_a.value(),2)
    time.sleep(1)