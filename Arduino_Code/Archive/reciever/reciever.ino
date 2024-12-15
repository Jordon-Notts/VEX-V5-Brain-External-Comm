#define CS_PIN 2       // Chip Select (CS) pin
#define CLOCK_PIN 3    // Clock pin
#define DATA_PIN 4     // Data pin

unsigned long previousMillis = 0; // Stores the last time millis was sent
const unsigned long interval = 1000; // Interval in milliseconds

const int pin_change_delay = 10; // Delay for the 5V brain to register pin changes (in microseconds)

void setup() {
  pinMode(CS_PIN, INPUT_PULLUP);    // Set CS as an output
  pinMode(CLOCK_PIN, INPUT_PULLUP); // Set Clock as an output
  pinMode(DATA_PIN, INPUT_PULLUP);  // Set Data as an output

//   digitalWrite(CS_PIN, LOW);    // Initialize CS to HIGH (inactive)
//   digitalWrite(CLOCK_PIN, LOW);  // Initialize Clock to LOW
//   digitalWrite(DATA_PIN, LOW);   // Initialize Data to LOW

  // Initialize Serial for debugging
  Serial.begin(115200); // Short delay for stability600);
  Serial.println("Setup complete. Ready to send data...");
}

void loop() {
  unsigned long currentMillis = millis(); // Get the current time

  // Check if it's time to send the data
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    // Convert millis to a string and send it
    String millisString = String(currentMillis);
    Serial.println("Sending data:");
    Serial.println("---------------");#define CS_PIN 2       // Chip Select (CS) pin
#define CLOCK_PIN 3    // Clock pin
#define DATA_PIN 4     // Data pin

volatile bool cs_active = false;   // Tracks if CS is active
volatile uint8_t current_byte = 0; // Stores the currently received byte
volatile int bit_position = 7;     // Bit position for receiving a byte
volatile bool byte_ready = false;  // Flag to indicate a byte has been received
volatile size_t length = 0;        // Length of the message
volatile uint8_t checksum = 0;     // Checksum of the received data
String received_data = "";         // Stores the received message

void setup() {
  pinMode(CS_PIN, INPUT_PULLUP);    // Set CS as input with pull-up
  pinMode(CLOCK_PIN, INPUT_PULLUP); // Set Clock as input with pull-up
  pinMode(DATA_PIN, INPUT_PULLUP);  // Set Data as input with pull-up

  // Attach interrupts
  attachInterrupt(digitalPinToInterrupt(CS_PIN), csISR, CHANGE);   // CS interrupt
  attachInterrupt(digitalPinToInterrupt(CLOCK_PIN), clockISR, RISING); // Clock interrupt

  // Initialize Serial for debugging
  Serial.begin(115200);
  Serial.println("Receiver setup complete. Waiting for data...");
}

void loop() {
  // Check if a complete message has been received
  if (byte_ready && cs_active) {
    byte_ready = false; // Reset flag

    // If length is not set, this is the first byte (length byte)
    if (length == 0) {
      length = current_byte;
      Serial.print("Message length received: ");
      Serial.println(length);
    } else if (received_data.length() < length) {
      // Add received byte to the message
      received_data += char(current_byte);
      Serial.print("Received char: ");
      Serial.println(char(current_byte));
    } else if (received_data.length() == length) {
      // Last byte is the checksum
      checksum = current_byte;
      Serial.print("Checksum received: ");
      Serial.println(checksum);

      // Validate checksum
      if (validateChecksum(received_data, checksum)) {
        Serial.println("Data received successfully:");
        Serial.println(received_data);
      } else {
        Serial.println("Checksum mismatch. Data corrupted.");
      }

      // Reset for next message
      resetReceiver();
    }
  }
}

// ISR for Chip Select (CS) pin
void csISR() {
  cs_active = digitalRead(CS_PIN) == HIGH;
  if (!cs_active) {
    resetReceiver(); // Reset receiver if CS is deactivated
  }
}

// ISR for Clock pin
void clockISR() {
  if (cs_active) {
    // Read the current bit from DATA_PIN
    current_byte |= (digitalRead(DATA_PIN) << bit_position);
    bit_position--;

    // If all bits of the byte are received
    if (bit_position < 0) {
      bit_position = 7;   // Reset bit position
      byte_ready = true;  // Set flag for a complete byte
    }
  }
}

// Validate the checksum
bool validateChecksum(String data, uint8_t received_checksum) {
  uint8_t calculated_checksum = 0;
  for (size_t i = 0; i < data.length(); i++) {
    calculated_checksum += data[i];
  }
  return (calculated_checksum % 256) == received_checksum;
}

// Reset the receiver for the next message
void resetReceiver() {
  current_byte = 0;
  bit_position = 7;
  byte_ready = false;
  length = 0;
  checksum = 0;
  received_data = "";
}

    Serial.print("String: ");
    Serial.println(millisString);
    send_string(millisString);
  }
}

void send_string(String data) {
  // Calculate the length and checksum
  size_t length = data.length();          // Length of the string
  uint8_t checksum = calculateChecksum(data); // Calculate checksum

  // Activate CS
  digitalWrite(CS_PIN, HIGH);

  // Debug output for metadata
  Serial.print("Length:\t\t");
  Serial.print(length);
  Serial.print("\t");

  // Send the length (1 byte)
  sendByte(length);

  Serial.println("");


  // Send each character of the string as ASCII (1 byte per character)
  for (size_t i = 0; i < length; i++) {
    
    Serial.print("Sending char: \t");
    Serial.print(data[i]);  // Print the character being sent
    
    Serial.print("\t");

    sendByte(data[i]);  // Send each character's ASCII value

    Serial.println();  // Print the character being sent
    
  }

  Serial.print("Checksum: \t");
  Serial.print(checksum);
  Serial.print("\t");

  // Send the checksum (1 byte)
  sendByte(checksum);

  // Deactivate CS
  digitalWrite(CS_PIN, LOW);
  digitalWrite(DATA_PIN, LOW);

  // Debug output for completion
  Serial.println("\nData sent.");
  Serial.println("---------------");
}

void sendByte(uint8_t b) {
  // Send a byte (8 bits)
  for (int i = 7; i >= 0; i--) {
    // Set the data bit
    Serial.print((b >> i) & 1);
    
    digitalWrite(DATA_PIN, (b >> i) & 1);
    // Generate a clock pulse
    digitalWrite(CLOCK_PIN, HIGH);
    delayMicroseconds(pin_change_delay); // Short delay for stability
    digitalWrite(CLOCK_PIN, LOW);
    delayMicroseconds(pin_change_delay);
  }
}

uint8_t calculateChecksum(String data) {
  // Calculate a simple checksum as the sum of ASCII values modulo 256
  uint8_t checksum = 0;
  for (size_t i = 0; i < data.length(); i++) {
    checksum += data[i];
  }
  return checksum % 256;
}
