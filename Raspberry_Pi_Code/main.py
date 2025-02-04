
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

if __name__ == "__main__":

    CS_PIN = 21
    CLOCK_PIN = 22
    DATA_PIN = 23

    comm = V5ExternalComm(cs_pin=CS_PIN, clock_pin=CLOCK_PIN, data_pin=DATA_PIN, on_message_received=on_message_recieved_callback)

    # Example usage: Send "HELLO"
    
    count = 0 

    while True:

        comm.send_data(f"RPI_OUT {count}")

        count += 1

        time.sleep(5)
