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


// ID as defined in okm
#define KEYREADER_ID 20

// #define COMMON_ANODE

#ifdef COMMON_ANODE
#define LED_ON LOW
#define LED_OFF HIGH
#else
#define LED_ON HIGH
#define LED_OFF LOW
#endif

// #define INVERT_RELAY

#ifdef INVERT_RELAY
#define REL_ON LOW
#define REL_OFF HIGH
#else
#define REL_ON HIGH
#define REL_OFF LOW
#endif

#define DE_RE_PIN 9

String in_msg;
String rsp_msg;
String msg;
String splittedMsg[2];

constexpr uint8_t redLed = 4;   // Set Led Pins
constexpr uint8_t greenLed = 5;
constexpr uint8_t blueLed = 6;

constexpr uint8_t relay = 8;     // Set Relay Pin

boolean is_unlocked = false; // Needed to keep consitant led state

bool new_read;    // Variable who keeps if we have Successful Read from Reader
byte readCard[4];   // Stores scanned ID read from RFID Module

// Create MFRC522 instance.
constexpr uint8_t RST_PIN = 7;
constexpr uint8_t SS_PIN = 10;

MFRC522 mfrc522(SS_PIN, RST_PIN);

///////////////////////////////////////// Setup ///////////////////////////////////
void setup() {

  // Avoid Heap fragmentation !?!
  // read : https://cpp4arduino.com/2018/11/06/what-is-heap-fragmentation.html
  in_msg.reserve(100);
  rsp_msg.reserve(100);
  msg.reserve(100);
  splittedMsg[0].reserve(50);
  splittedMsg[1].reserve(50);

  pinMode(DE_RE_PIN, OUTPUT);
  set_receive_mode();

  pinMode(SS_PIN, OUTPUT);

  pinMode(redLed, OUTPUT);
  pinMode(greenLed, OUTPUT);
  pinMode(relay, OUTPUT);

  test_leds();

  digitalWrite(relay, LOW);    // Make sure door is locked
  digitalWrite(redLed, LED_OFF);  // Make sure led is off
  digitalWrite(greenLed, LED_OFF);  // Make sure led is off
  digitalWrite(blueLed, LED_OFF);  // Make sure led is off

  //Protocol Configuration
  Serial.begin(9600);  // Initialize serial communications with PC
  SPI.begin();           // MFRC522 Hardware uses SPI protocol
  mfrc522.PCD_Init();    // Initialize MFRC522 Hardware

  //If you set Antenna Gain to Max it will increase reading distance
  //mfrc522.PCD_SetAntennaGain(mfrc522.RxGain_max);

  
  // For debug via proper serial without RS485
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
    // discard eventual extra bytes after ;
    Serial.flush();

    splitArray(in_msg, splittedMsg, ':');
    if (splittedMsg[0] == String(KEYREADER_ID)) {
      msg = splittedMsg[1];

      if (msg == "ask_for_new") {
        if (new_read) {
          rsp_msg = "new_read:";
          for ( uint8_t i = 0; i < 4; i++) {
            rsp_msg += String(readCard[i], HEX);
          }
          send_message(rsp_msg);
          new_read = false;
        } else {
          send_message("new_read:none");
        }
      } else if (msg ==  "lock") {
        send_message("confirm:lock");
        lock();
      } else if (msg == "unlock") {
        send_message("confirm:unlock");
        unlock();
      } else if (msg == "denied") {
        send_message("confirm:denied");
        denied();
      } else { // If the message is not known, simply echo with id
        rsp_msg = String(KEYREADER_ID) + ":unknown_order";
        send_message(rsp_msg);
        unknown();
      }
    }
  }

  // check led state
  if (is_unlocked){
    digitalWrite(greenLed, LED_ON);
    digitalWrite(redLed, LED_OFF);
    digitalWrite(blueLed, LED_OFF);
  } else {
    // redLed is turned on when a read occur (before transmission)
    // so we don't turn it off here
    // TODO : change to blue when available
    digitalWrite(greenLed, LED_OFF);
    digitalWrite(blueLed, LED_OFF);
  }

}

void splitArray(String data, String splittedMsg[2], char separator)
{
  int sepAt;
  int maxIndex = data.length(); 

  for (int i=0; i < maxIndex; i++){
    if (data.charAt(i) == separator) {
      sepAt = i;
    }
  }                                
  splittedMsg[0] = data.substring(0, sepAt);
  splittedMsg[1] = data.substring(sepAt+1, maxIndex);
}

/////////////////////////////////////////  MAX485 communication //////////////////////////////
void send_message(String msg){
    // Wait extra 20ms to be sure (is what raspy waits before passing to receive mode)
    delay(20);
    set_send_mode();

    Serial.print(msg + ';');

    // Wait for serial to be transmitted
    while (Serial.availableForWrite() < SERIAL_TX_BUFFER_SIZE - 1){
      delay(1);                                                
    }                                                          
    // Wait extra 20ms to be sure message is transmitted
    delay(20);

    set_receive_mode();
}

void set_send_mode(){
  digitalWrite(DE_RE_PIN, HIGH);
}

void set_receive_mode(){
  digitalWrite(DE_RE_PIN, LOW);
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

void test_leds() {
  for ( uint8_t i = 0; i < 3; i++) {
    digitalWrite(redLed, LED_ON);   
    delay(100);
    digitalWrite(redLed, LED_OFF);   
    delay(100);
  }
  for ( uint8_t i = 0; i < 3; i++) {
    digitalWrite(greenLed, LED_ON);   
    delay(100);
    digitalWrite(greenLed, LED_OFF);   
    delay(100);
  }
  for ( uint8_t i = 0; i < 3; i++) {
    digitalWrite(blueLed, LED_ON);   
    delay(100);
    digitalWrite(blueLed, LED_OFF);   
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
  digitalWrite(redLed, LED_ON);
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
