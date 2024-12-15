# Import necessary modules
import RPi.GPIO as GPIO
import time

class V5ExternalComm:
    """
    This class facilitates communication with an external device using clock, data, 
    and chip select (CS) pins. It also includes LED indication and payload processing.
    """

    def __init__(self, cs_pin_number, clock_pin_number, data_pin_number, on_message_received=None):
        """
        Initialize the V5ExternalComm class for communication with an external device.

        Parameters:
        - cs_pin_number (int): GPIO pin number for the Chip Select (CS) signal.
            This pin is used to indicate when the external device is ready to send or receive data. 
            The CS pin is usually active LOW (0 means communication is active).

        - clock_pin_number (int): GPIO pin number for the Clock signal.
            The Clock pin determines when bits are transmitted or received. A rising clock edge is
            typically used to synchronize data transfer.

        - data_pin_number (int): GPIO pin number for the Data signal.
            This pin carries the actual data bits being sent to or received from the external device.

        - on_message_received (callable, optional): A callback function to handle messages when they are successfully received.
            The callback function should accept a single parameter (the received message as a string).
        """

        # Store the pin numbers provided by the user for later use
        self.cs_pin_number = cs_pin_number
        self.clock_pin_number = clock_pin_number
        self.data_pin_number = data_pin_number

        # Callback function for message handling
        self.on_message_received = on_message_received

        # Initialize state variables
        self.buffer = []  # Buffer for storing received bits during communication
        self.last_message = ""  # Keeps track of the last valid message sent or received

        # Initialize pin objects for CS, Clock, and Data signals.
        self.cs_pin = None
        self.clock_pin = None
        self.data_pin = None

        # Communication configuration constants:
        self.BIT_DELAY_US = 1000  # Delay between bits in microseconds (1ms)
        self.MAX_BUFFER_SIZE = 256  # Maximum allowed payload size in bits

        # Flag to indicate the current mode (True = receiving, False = sending)
        self.reciving = False

        # Set the pins to "receive mode" by default.
        self.set_pins_receive()

    def calculate_checksum(self, data):
        """
        Calculate the checksum of the input string.
        """
        return sum(bytearray(data, 'ascii')) % 256

    def int_to_bits(self, value, bit_count):
        """
        Convert an integer into a list of bits (binary representation).
        """
        return [(value >> i) & 1 for i in range(bit_count - 1, -1, -1)]

    def encode_payload(self, length, data, checksum):
        """
        Encode the length, data, and checksum into a single bit stream.
        """
        bits = self.int_to_bits(length, 8)  # Encode length (8 bits)
        for char in data:
            bits.extend(self.int_to_bits(ord(char), 8))  # Encode each character (8 bits per char)
        bits.extend(self.int_to_bits(checksum, 8))  # Encode checksum (8 bits)
        return bits

    def send_data(self, data):
        """
        Send data to the external device by toggling clock and data pins.
        """
        # Ensure the pins are set to receive mode initially
        self.set_pins_receive()

        # Wait until the CS pin is low (ready state)
        while self.cs_pin.value() == 1:
            time.sleep_us(10)  # Short delay to avoid busy-waiting

        # Switch pins to send mode
        self.set_pins_send()

        # Calculate the payload components
        length = len(data)
        checksum = self.calculate_checksum(data)
        payload = self.encode_payload(length, data, checksum)

        # Activate CS pin to start transmission
        self.cs_pin.on()
        time.sleep_us(10)  # Brief delay for signal stability

        # Send the encoded payload bit by bit
        for bit in payload:
            self.data_pin.value(bit)  # Set data pin to the current bit value
            self.clock_pin.on()  # Toggle clock pin high
            time.sleep_us(self.BIT_DELAY_US)  # Hold for the bit delay
            self.clock_pin.off()  # Toggle clock pin low
            time.sleep_us(self.BIT_DELAY_US)

        # Deactivate CS pin to end transmission
        self.cs_pin.off()

        print(f"Data sent: {data}")  # Print the sent data for debugging

        # Reset the pins to receive mode
        self.set_pins_receive()

    def reset_buffer(self):
        """
        Clear the payload buffer.
        """
        self.buffer = []

    def process_buffer(self):
        """
        Process and validate the received payload.
        """
        # Check if payload has the minimum required bits
        if len(self.buffer) < 16:
            return

        # Decode the length from the first 8 bits
        length_bits = self.buffer[:8]
        length = int("".join(map(str, length_bits)), 2)

        # Check if payload has sufficient bits for length, data, and checksum
        if len(self.buffer) >= (8 + length * 8 + 8):
            data_bits = self.buffer[8:8 + length * 8]
            data = "".join(
                chr(int("".join(map(str, data_bits[i:i + 8])), 2)) for i in range(0, len(data_bits), 8))

            checksum_bits = self.buffer[8 + length * 8:8 + length * 8 + 8]
            received_checksum = int("".join(map(str, checksum_bits)), 2)

            # Validate the checksum
            if received_checksum == self.calculate_checksum(data):

                if data == "ERROR":
                    self.send_data(self.last_message)  # Resend last message on error
                else:
                    self.last_message = data  # Update last message
                    if self.on_message_received != None:
                        self.on_message_received(data)
                    else:
                        print(f"Received: {data}")  # Print the received data
            else:

                self.receive_error()  # Handle checksum mismatch error

            self.reset_buffer()

    def receive_error(self):
        """
        Handle errors during reception and send an error message.
        """
        print("Error detected. Sending 'ERROR'.")
        print("Received data (raw):", "".join(map(str, self.buffer)))
        self.send_data("ERROR")

    def handle_clock_change(self, pin):
        """
        Handle clock pin rising edge to read incoming bits.
        """
        if self.reciving:
            if self.cs_pin.value() == 1:  # Only read when CS is active
                if len(self.buffer) < self.MAX_BUFFER_SIZE:
                    self.buffer.append(self.data_pin.value())  # Append bit to payload

    def handle_cs_change(self, pin):
        """
        Handle CS pin state changes to manage data transmission.
        """
        if self.reciving:
            if self.cs_pin.value() == 1:  # CS HIGH: Transmission ends
                self.reset_buffer()

            else:  # CS LOW: Transmission starts
                self.process_buffer()

    def set_pins_receive(self):
        """
        Configure the pins for receiving mode.
        """
        self.cs_pin = Pin(self.cs_pin_number, Pin.IN)
        self.clock_pin = Pin(self.clock_pin_number, Pin.IN)
        self.data_pin = Pin(self.data_pin_number, Pin.IN)

        self.cs_pin.irq(trigger=Pin.IRQ_RISING, handler=self.handle_cs_change)
        self.cs_pin.irq(trigger=Pin.IRQ_FALLING, handler=self.handle_cs_change)
        self.clock_pin.irq(trigger=Pin.IRQ_RISING, handler=self.handle_clock_change)

        self.reciving = True

    def set_pins_send(self):
        """
        Configure the pins for sending mode.
        """
        self.reciving = False

        self.cs_pin = Pin(self.cs_pin_number, Pin.OUT)
        self.clock_pin = Pin(self.clock_pin_number, Pin.OUT)
        self.data_pin = Pin(self.data_pin_number, Pin.OUT)

        self.cs_pin.value(0)
        self.clock_pin.value(0)
        self.data_pin.value(0)
