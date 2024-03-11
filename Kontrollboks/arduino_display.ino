#include "SevSeg.h"
SevSeg sevseg;
int number_display = 577;

int last_run = 0;
void setup() {
  Serial.begin(9600);
  byte numDigits = 4;
  byte digitPins[] = {10, 11, 12, 13};
  byte segmentPins[] = {9, 2, 3, 5, 6, 8, 7, 4};
  bool resistorsOnSegments = true;
  bool updateWithDelaysIn = true;
  byte hardwareConfig = COMMON_CATHODE;
  sevseg.begin(hardwareConfig, numDigits, digitPins, segmentPins, resistorsOnSegments);
  sevseg.setBrightness(90);
  sevseg.setNumber(1234);
}
void loop() {
  int sensorValue = analogRead(A0);

  Serial.println(sensorValue);
  if (Serial.available() > 0) {
    String received = Serial.readStringUntil('\n'); // Read the incoming data until newline
    int number = received.toInt();
    Serial.print("Received: ");
    Serial.println(number); // Print the received data
    sevseg.setNumber(number);
  }
  // Refresh the display continuously
  sevseg.refreshDisplay();
}

