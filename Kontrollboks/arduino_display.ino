// Inkluderer SevSeg-biblioteket som gir funksjoner for å kontrollere 7-segment displays.
#include "SevSeg.h"
SevSeg sevseg;

void setup() {
  Serial.begin(9600);// Starter seriell kommunikasjon med en baudrate på 9600 for å komunisere med Adafurit-en ved hjelp av TX og RX.
  byte numDigits = 4;// Antall siffer i displayet.
  byte digitPins[] = {10, 11, 12, 13};// Definerer hvilke pinner på Arduinoen som er koblet til de enkelte sifrene på displayet.
  byte segmentPins[] = {9, 2, 3, 5, 6, 8, 7, 4};// Definerer pinnene som kontrollerer de individuelle segmentene på hvert siffer.
  
  //ting vi trenger for å få displayet til å fungere:
  bool resistorsOnSegments = true;
  bool updateWithDelaysIn = true;
  byte hardwareConfig = COMMON_CATHODE;

  // Initialiserer SevSeg-objektet med de definerte konfigurasjonene.
  sevseg.begin(hardwareConfig, numDigits, digitPins, segmentPins, resistorsOnSegments);
  // Setter lysstyrken på displayet til 90 (på en skala fra 0 til 100).
  sevseg.setBrightness(90);
  // Setter tallet som skal vises til 1234 som en initial verdi for å se at alt fungerer som det skal.
  sevseg.setNumber(1234);
}

void loop() {
  // Sjekker om det er tilgjengelig data på den serielle porten fra adafruit-en.
  if (Serial.available() > 0) {
    
    String received = Serial.readStringUntil('\n');// Leser dataen fra Adafuriten
    int number = received.toInt();// Konverterer den mottatte strengen til et heltall. Dette er altså høyden til CanSat-en
   
   // Skriver ut det mottatte tallet til den serielle monitoren.
    Serial.print("Received: ");
    Serial.println(number);
    // Setter det mottatte tallet til å vises på displayet.
    sevseg.setNumber(number);
  }
  // Oppdaterer displayet kontinuerlig.
  sevseg.refreshDisplay();
}
