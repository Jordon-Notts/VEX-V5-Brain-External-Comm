import RPi.GPIO as GPIO
import time

class V5ExternalComm:
    
    def __init__(self, cs_pin, clock_pin, data_pin, on_message_received=None):
        self.cs_pin = cs_pin
        self.clock_pin = clock_pin
        self.data_pin = data_pin
        self.running = False
        self.cs_active = False  # Indicates if CS is active (HIGH)
        self.current_byte = []  # Store bits for the current byte
        self.received_data = []  # Store all received bytes
        self.on_message_received = on_message_received

        self.last_message = ""

        self.set_pins_receive()

    def process_and_display_buffer(self):
        """
        Process and validate the received payload, displaying it in a detailed tabular format.
        """
        # Convert received data (bytes) to a binary bitstream
        bitstream = []

        for byte in self.received_data:
            bitstream.extend([int(bit) for bit in f"{byte:08b}"])  # Convert each byte to 8 bits

        print("\nRECEIVE\nBuffer content (raw):", "".join(map(str, bitstream)))

        if len(bitstream) < 16:
            print("Error: Buffer too short to process.")
            return

        try:
            # Decode length
            length_bits = bitstream[:8]
            length = int("".join(map(str, length_bits)), 2)
            print(f"Length: {length}\tBinary: {''.join(map(str, length_bits))}\n")

            # Check if buffer has enough bits for length, data, and checksum
            if len(bitstream) < 8 + length * 8 + 8:
                print("Error: Insufficient bits for data and checksum.")
                return

            # Decode data
            data_bits = bitstream[8:8 + length * 8]
            received_data = []
            print("Bytes (ASCII and Binary):")
            for i in range(0, len(data_bits), 8):
                char_bits = data_bits[i:i + 8]
                char = chr(int("".join(map(str, char_bits)), 2))
                received_data.append(char)
                binary_representation = "".join(map(str, char_bits))
                print(f"Byte {i // 8 + 1}: ASCII '{char if 32 <= ord(char) <= 126 else '.'}' "
                    f"({ord(char)}) Binary {binary_representation}")

            decoded_data = "".join(received_data)

            # Decode checksum
            checksum_bits = bitstream[8 + length * 8:8 + length * 8 + 8]
            received_checksum = int("".join(map(str, checksum_bits)), 2)
            print(f"\nChecksum: {received_checksum}\tBinary: {''.join(map(str, checksum_bits))}")

            # Validate checksum
            calculated_checksum = self.calculate_checksum(decoded_data)
            if received_checksum == calculated_checksum:
                print("Checksum validation passed.")

                if decoded_data == "ERROR":
                    self.send_data(self.last_message)
                else:
                    if self.on_message_received:
                        self.on_message_received(decoded_data)
            else:
                print(f"Checksum mismatch. Received: {received_checksum}, Calculated: {calculated_checksum}")
                self.send_data("ERROR")

        except Exception as e:

            print(f"Error processing buffer: {e}")


    def send_data(self, data):
        """
        Send data to the external device by toggling clock and data pins.
        """

        if data != "ERROR":
            self.last_message = data

        print(f"\nSEND: {data}\n")

        while True:
            try:
                if GPIO.input(self.cs_pin) == 0:
                    break
            except:
                pass
                time.sleep(0.001)

        self.set_pins_send()  # Configure pins for sending mode

        # Activate CS pin to start transmission
        GPIO.output(self.cs_pin, GPIO.HIGH)
        time.sleep(0.00001)  # Brief delay for stability

        # Convert data to binary stream (length, data, checksum)
        length = len(data)
        checksum = self.calculate_checksum(data)
        payload = self.encode_payload(length, data, checksum)

        # Send each bit in the payload
        for bit in payload:
            GPIO.output(self.data_pin, bit)  # Set data pin to bit value
            GPIO.output(self.clock_pin, GPIO.HIGH)  # Rising edge
            time.sleep(0.0001)  # Delay for clock timing
            GPIO.output(self.clock_pin, GPIO.LOW)  # Falling edge

        # Deactivate CS pin to end transmission
        GPIO.output(self.cs_pin, GPIO.LOW)

        self.set_pins_receive()  # Restore pins to receive mode

    def encode_payload(self, length, data, checksum):
        """
        Encode the length, data, and checksum into a binary stream.
        """
        bits = [int(bit) for bit in f"{length:08b}"]  # Length in 8 bits
        for char in data:
            bits.extend([int(bit) for bit in f"{ord(char):08b}"])  # ASCII of each character
        bits.extend([int(bit) for bit in f"{checksum:08b}"])  # Checksum in 8 bits
        return bits

    def handle_cs_change(self, pin):
        """
        Handles changes on the CS pin and logs when communication starts or ends.
        """
        cs_state = GPIO.input(self.cs_pin)
        self.cs_active = cs_state == 1  # Update CS active state

        if self.cs_active:
            # print("\nCS ACTIVE (HIGH): Communication started\n")
            self.current_byte = []  # Reset current byte buffer
            self.received_data = []  # Clear received data buffer
        else:
            # print("\nCS INACTIVE (LOW): Communication ended\n")
            self.process_and_display_buffer()  # Display the captured data

    def log_pins(self, pin):
        """
        Logs the state of the data pin when the clock pin goes high.
        Captures 8 bits as one byte and calculates its ASCII value.
        """
        if self.cs_active:  # Only log if CS is active

            data_state = GPIO.input(self.data_pin)
            self.current_byte.append(data_state)

            # If we have 8 bits, process the byte
            if len(self.current_byte) == 8:
                byte_value = int("".join(map(str, self.current_byte)), 2)  # Convert bits to integer
                self.received_data.append(byte_value)  # Store the byte
                self.current_byte = []  # Clear the byte buffer

    def calculate_checksum(self, data):
        """
        Calculate the checksum for the given data.
        """
        return sum(bytearray(data, 'ascii')) % 256

    def set_pins_receive(self):
        """
        Configure GPIO pins for receive mode.
        """
        GPIO.cleanup()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.cs_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.clock_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.data_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        GPIO.add_event_detect(self.clock_pin, GPIO.RISING, callback=self.log_pins)
        GPIO.add_event_detect(self.cs_pin, GPIO.BOTH, callback=self.handle_cs_change)

    def set_pins_send(self):
        """
        Configure GPIO pins for send mode.
        """
        GPIO.cleanup()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.cs_pin, GPIO.OUT)
        GPIO.setup(self.clock_pin, GPIO.OUT)
        GPIO.setup(self.data_pin, GPIO.OUT)

        GPIO.output(self.cs_pin, GPIO.LOW)
        GPIO.output(self.clock_pin, GPIO.LOW)
        GPIO.output(self.data_pin, GPIO.LOW)
