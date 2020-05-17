// possibly standard for whatever
//#define LED_BUILTIN 7
// standard for UNO


#define DE_RE_PIN 9

#define BUILDIN_LED 13

String in_msg = "";
String rsp_msg = "";

// the setup function runs once when you press reset or power the board
void setup() {
  // initialize digital pin LED_BUILTIN as an output.
  pinMode(DE_RE_PIN, OUTPUT);

  set_receive_mode();

  Serial.begin(9600);

  pinMode(BUILDIN_LED, OUTPUT);

  digitalWrite(BUILDIN_LED, HIGH);
  delay(500);
  digitalWrite(BUILDIN_LED, LOW);
  delay(500);
  digitalWrite(BUILDIN_LED, HIGH);
  delay(500);
  digitalWrite(BUILDIN_LED, LOW);
}

// the loop function runs over and over again forever
void loop() {

  if (Serial.available() > 1) {

    // read until ; or timeout after 1 sec
    in_msg = Serial.readStringUntil(';');

    if (in_msg == "bidule:machin40"){
      rsp_msg = "------- !!  succes !! ---------";
    }
    else{
      rsp_msg = "nop !";
    }


    // Wait extra 20ms to be sure (is what raspy waits before passing to receive mode)
    delay(20);
    set_send_mode();


    Serial.print(rsp_msg + ';');

    // Wait for serial to be transmitted
    while (Serial.availableForWrite() < SERIAL_TX_BUFFER_SIZE - 1){
      delay(1);                                                
    }                                                          
    // Wait extra 20ms to be sure message is transmitted
    delay(20);

    set_receive_mode();
    /*Serial.print(millis());                  */
    /*Serial.println(" : end of transmission");*/
  }


}


void set_send_mode(){
  digitalWrite(BUILDIN_LED, HIGH);
  digitalWrite(DE_RE_PIN, HIGH);
}
void set_receive_mode(){
  digitalWrite(DE_RE_PIN, LOW);
  digitalWrite(BUILDIN_LED, LOW);
}
