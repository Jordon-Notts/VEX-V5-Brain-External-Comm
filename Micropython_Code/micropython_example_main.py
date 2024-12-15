# Import necessary modules
import time  # Import the time module for adding delays in the code

# Import the V5ExternalComm class from the custom library
from lib.V5_External_Comm_Lib import V5ExternalComm

# Define a callback function to handle received messages
def on_message_recieved_callback(data):
    """
    Callback function that gets executed when a message is received by the V5ExternalComm instance.
    
    Parameters:
    - data (str): The data/message received from the external device.
    
    Behavior:
    - Prints the received data to the console for debugging or further processing.
    """
    print(f"data received : {data}")  # Display the received message

# Example Usage:
# Create an instance of the V5ExternalComm class, configuring it for your hardware setup.
transceiver = V5ExternalComm(
    cs_pin_number=20,         # Chip Select (CS) pin number (GPIO 20)
    clock_pin_number=19,      # Clock pin number (GPIO 19)
    data_pin_number=18,       # Data pin number (GPIO 18)
    on_message_received=on_message_recieved_callback  # Set the callback function for received messages
)

# Initialize a counter variable to send sequential messages
count = 0  # This will be used to incrementally update the message being sent

# Main loop: This runs continuously
while True:
    # Send a message to the external device
    # The message includes a "Hello" string concatenated with the current count
    transceiver.send_data("Hello " + str(count))
    
    # Increment the count for the next message
    count += 1

    # Pause for 0.5 seconds before sending the next message
    # This delay ensures the communication isn't too rapid, allowing the external device to process
    time.sleep(0.5)
