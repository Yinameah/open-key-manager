/*
  -*- coding: utf-8 -*-
 
  This file is part of the Open Key Managment
  A rfid key manager system based on raspberryPi and Arduino
 
  Copyright 2020 Aurélien Cibrario <aurelien.cibrario@gmail.com>
 
  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
 
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
 
  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.

*/


/*



 * **Stores Information on EEPROM**

   Information stored on non volatile Arduino's EEPROM memory to preserve Users' tag and Master Card. No Information lost
   if power lost. EEPROM has unlimited Read cycle but roughly 100,000 limited Write cycle.

 * **Security**
   To keep it simple we are going to use Tag's Unique IDs. It's simple and not hacker proof.

   @license Released into the public domain.

   Typical pin layout used:
   -----------------------------------------------------------------------------------------
               MFRC522      Arduino       Arduino   Arduino    Arduino          Arduino
               Reader/PCD   Uno/101       Mega      Nano v3    Leonardo/Micro   Pro Micro
   Signal      Pin          Pin           Pin       Pin        Pin              Pin
   -----------------------------------------------------------------------------------------
   RST/Reset   RST          9             5         D9         RESET/ICSP-5     RST
   SPI SS      SDA(SS)      10            53        D10        10               10
   SPI MOSI    MOSI         11 / ICSP-4   51        D11        ICSP-4           16
   SPI MISO    MISO         12 / ICSP-1   50        D12        ICSP-1           14
   SPI SCK     SCK          13 / ICSP-3   52        D13        ICSP-3           15
*/

#include <EEPROM.h>     // We are going to read and write PICC's UIDs from/to EEPROM
#include <SPI.h>        // RC522 Module uses SPI protocol
#include <MFRC522.h>  // Library for Mifare RC522 Devices

/*
  Instead of a Relay you may want to use a servo. Servos can lock and unlock door locks too
  Relay will be used by default
*/

// #include <Servo.h>

/*
  For visualizing whats going on hardware we need some leds and to control door lock a relay and a wipe button
  (or some other hardware) Used common anode led,digitalWriting HIGH turns OFF led Mind that if you are going
  to use common cathode led or just seperate leds, simply comment out #define COMMON_ANODE,
*/

// #define COMMON_ANODE

#ifdef COMMON_ANODE
#define LED_ON LOW
#define LED_OFF HIGH
#else
#define LED_ON HIGH
#define LED_OFF LOW
#endif

#define KEYREADER_ID 20

String in_msg = "";
String rsp_msg = "";

constexpr uint8_t redLed = 3;   // Set Led Pins
constexpr uint8_t greenLed = 2;
constexpr uint8_t blueLed = 1;

constexpr uint8_t relay = 4;     // Set Relay Pin

boolean is_unlocked = false; // Needed to keep consitant led state

uint8_t successRead;    // Variable integer to keep if we have Successful Read from Reader

bool new_read;    // Variable who keeps if we have Successful Read from Reader
byte readCard[4];   // Stores scanned ID read from RFID Module

// Create MFRC522 instance.
constexpr uint8_t RST_PIN = 2;     // Configurable, see typical pin layout above
constexpr uint8_t SS_PIN = 10;     // Configurable, see typical pin layout above

MFRC522 mfrc522(SS_PIN, RST_PIN);

///////////////////////////////////////// Setup ///////////////////////////////////
void setup() {
  pinMode(SS_PIN, OUTPUT);

  //Arduino Pin Configuration
  pinMode(redLed, OUTPUT);
  pinMode(greenLed, OUTPUT);
  pinMode(relay, OUTPUT);
  //Be careful how relay circuit behave on while resetting or power-cycling your Arduino
  digitalWrite(relay, LOW);    // Make sure door is locked
  digitalWrite(redLed, LED_OFF);  // Make sure led is off
  digitalWrite(greenLed, LED_OFF);  // Make sure led is off

  //Protocol Configuration
  Serial.begin(115200);  // Initialize serial communications with PC
  SPI.begin();           // MFRC522 Hardware uses SPI protocol
  mfrc522.PCD_Init();    // Initialize MFRC522 Hardware

  //If you set Antenna Gain to Max it will increase reading distance
  //mfrc522.PCD_SetAntennaGain(mfrc522.RxGain_max);

  Serial.println(F("Open Key Manager - Arduino with max485 initialized"));
  Serial.print("ID of device : ");
  Serial.println(KEYREADER_ID);
  ShowReaderDetails();  // Show details of PCD - MFRC522 Card Reader details
}


///////////////////////////////////////// Main Loop ///////////////////////////////////
void loop () {

  // Read potential new badge
  getID();

  if (Serial.available() > 0) {
    // read until ; or timeout after 1 sec
    in_msg = Serial.readStringUntil(';');

    if (in_msg == "order:ask_for_new") {
      if (new_read) {
        rsp_msg = "new_read:";
        for ( uint8_t i = 0; i < 4; i++) {
          rsp_msg += String(readCard[i], HEX);
        }
        rsp_msg += ";";
        new_read = false;
      } else {
        rsp_msg = "new_read:none;";
      }
    } else if (in_msg ==  "order:lock") {
      lock();
      rsp_msg = "confirm:lock;";
    } else if (in_msg == "order:unlock") {
      unlock();
      rsp_msg = "confirm:unlock;";
    } else if (in_msg == "order:denied") {
      denied();
      rsp_msg = "confirm:denied;";
    } else { // If the message is not known, simply echo
      unknown();
      rsp_msg = in_msg + ";";
    }

    Serial.print(rsp_msg);
  }

  // check led state
  if (is_unlocked){
    digitalWrite(greenLed, LED_ON);
    digitalWrite(redLed, LED_OFF);
    digitalWrite(blueLed, LED_OFF);
  } else {
    digitalWrite(greenLed, LED_OFF);
    digitalWrite(redLed, LED_OFF);
    digitalWrite(blueLed, LED_OFF);
  }

}

/////////////////////////////////////////  Accesses    ///////////////////////////////////
void unlock (){
  delay(1000);
  digitalWrite(redLed, LED_OFF);   

  is_unlocked = true;
  digitalWrite(relay, HIGH); //Open relay
}

void lock (){
  digitalWrite(redLed, LED_ON);   
  digitalWrite(greenLed, LED_ON);  
  delay(1000);
  digitalWrite(greenLed, LED_OFF);  
  delay(1000);
  digitalWrite(redLed, LED_OFF);   

  is_unlocked = false;
  digitalWrite(relay, LOW); //Close relay
}

void denied() {
  digitalWrite(greenLed, LED_OFF);  
  for ( uint8_t i = 0; i < 3; i++) {
    digitalWrite(redLed, LED_ON);   
    delay(200);
    digitalWrite(redLed, LED_OFF);  
    delay(200);
  }
  digitalWrite(redLed, LED_ON);   
  delay(1000);
  digitalWrite(redLed, LED_OFF);  
}

void unknown() {
  for ( uint8_t i = 0; i < 6; i++) {
    digitalWrite(redLed, LED_ON);   
    delay(100);
    digitalWrite(redLed, LED_OFF);  
    delay(100);
  }
}


///////////////////////////////////////// Get PICC's UID ///////////////////////////////////
uint8_t getID() {
  // Getting ready for Reading PICCs
  if ( ! mfrc522.PICC_IsNewCardPresent()) { //If a new PICC placed to RFID reader continue
    return 0;
  }
  if ( ! mfrc522.PICC_ReadCardSerial()) {   //Since a PICC placed get Serial and continue
    return 0;
  }
  // There are Mifare PICCs which have 4 byte or 7 byte UID care if you use 7 byte PICC
  // I think we should assume every PICC as they have 4 byte UID
  // Until we support 7 byte PICCs
  for ( uint8_t i = 0; i < 4; i++) {  //
    readCard[i] = mfrc522.uid.uidByte[i];
  }
  new_read = true;
  mfrc522.PICC_HaltA(); // Stop reading
  return 1;
}

void ShowReaderDetails() {
  // Get the MFRC522 software version
  byte v = mfrc522.PCD_ReadRegister(mfrc522.VersionReg);
  Serial.print(F("MFRC522 Software Version: 0x"));
  Serial.print(v, HEX);
  if (v == 0x91)
    Serial.print(F(" = v1.0"));
  else if (v == 0x92)
    Serial.print(F(" = v2.0"));
  else
    Serial.print(F(" (unknown),probably a chinese clone?"));
  Serial.println("");
  // When 0x00 or 0xFF is returned, communication probably failed
  if ((v == 0x00) || (v == 0xFF)) {
    Serial.println(F("WARNING: Communication failure, is the MFRC522 properly connected?"));
    Serial.println(F("SYSTEM HALTED: Check connections."));
    // Visualize system is halted
    digitalWrite(greenLed, LED_OFF);  // Make sure green LED is off
    digitalWrite(redLed, LED_ON);   // Turn on red LED
    while (true); // do not go further
  }
}
