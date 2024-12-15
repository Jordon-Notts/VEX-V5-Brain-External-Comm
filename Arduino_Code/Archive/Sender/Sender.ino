#define CS_PIN 2       // Chip Select (CS) pin
#define CLOCK_PIN 3    // Clock pin
#define DATA_PIN 4     // Data pin

unsigned long previousMillis = 0; // Stores the last time millis was sent
const unsigned long interval = 1000; // Interval in milliseconds

const int pin_change_delay = 10; // Delay for the 5V brain to register pin changes (in microseconds)

void setup() {
  pinMode(CS_PIN, OUTPUT);    // Set CS as an output
  pinMode(CLOCK_PIN, OUTPUT); // Set Clock as an output
  pinMode(DATA_PIN, OUTPUT);  // Set Data as an output

  digitalWrite(CS_PIN, LOW);    // Initialize CS to HIGH (inactive)
  digitalWrite(CLOCK_PIN, LOW);  // Initialize Clock to LOW
  digitalWrite(DATA_PIN, LOW);   // Initialize Data to LOW

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
    Serial.println("---------------");
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
