import vex as vx
import time

# Initialize the brain and input pin
brain = vx.Brain()

# Variables to track timing and state

port_a = vx.DigitalIn(brain.three_wire_port.a)

def print_to_brain(message, row):
    """Utility to print messages on the VEX Brain screen."""
    brain.screen.clear_row(row)
    brain.screen.set_cursor(row, 1)
    brain.screen.print(message)

global start_time

start_time = None

global end_time

def rising_edge_detected():
    """Callback for rising edge (LOW to HIGH)."""

    global start_time

    print_to_brain("Pin HIGH detected!", 2)

    start_time = brain.timer.time()

def falling_edge_detected():
    """Callback for falling edge (HIGH to LOW)."""
    print_to_brain("Pin LOW detected!", 2)

    end_time = brain.timer.time()

    global start_time

    if start_time == None:
        print_to_brain("FIRST RUN", 3)
    else:
        print_to_brain(end_time - start_time ,3)

port_a.low(falling_edge_detected)
port_a.high(rising_edge_detected)

# Main loop for edge detection
while True:

    time.sleep(200)
