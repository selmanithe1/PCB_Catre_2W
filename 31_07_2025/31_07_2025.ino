#include <Wire.h>

#define FRAM_ADDR 0x50  // Replace with the actual I2C address of your FRAM device
// addresss : current position =0, pos_f =1, position1 =2, position2 =3
int values[5];          // Array to store 5 integer values
const int enA = 9;
const int in1 = 11;                                                      
const int in2 = 12;
const int buttonPin1 = A3;
const int buttonPin2 = A2;
const int buttonPin3 = A0;
const int buttonPin4 = 13;
const int powerPin = 5;
const int HESPin = 2;
const int ledpp2 = 6;


int speed_DC = 255;
int buttonState1 = 0;
int buttonState2 = 0;
int buttonState3 = 0;
int buttonState4 = 0;
int powerState = 1;
int sum = 50;
int i=1;
int j=1;
int pos_f=0;
volatile int position = 0;
unsigned long LastTimeChange = 0;
int HES = 0;
int PHES = 0;

int pos1=0;
int pos2=0;
int flaginit =0;

boolean Moving = false;
volatile boolean dir_up = false;
volatile boolean dir_down = false;
unsigned long buttonPressTime = 0;
boolean button3Pressed = false;
boolean button4Pressed = false;


void setup() {
  sei();
  attachInterrupt(digitalPinToInterrupt(2), rotation, RISING);
  Wire.begin();
  pinMode(enA, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(ledpp2, OUTPUT);
  pinMode(buttonPin1, INPUT);
  pinMode(buttonPin2, INPUT);
  pinMode(buttonPin3, INPUT);
  pinMode(buttonPin4, INPUT);
  pinMode(powerPin, INPUT);
  pinMode(HESPin, INPUT);
  motor_command(2,0);
  delay(200);
  readValuesFromFRAM();
  if (values[0] != 50){init_position(); } else {readValuesFromFRAM();}
  position=values[1];
  pos_f=values[2];
  pos1=values[3];
  pos2=values[4];


}

void loop() {
  powerState = digitalRead(powerPin);
  if (powerState ==LOW){
    values[1]=position;
    values[2]=pos_f;
    values[3]=pos1;
    values[4]=pos2;
    
    
  storeValuesInFRAM(values);

  delay(1000); // Optional delay to avoid multiple consecutive storages
  }
  buttonState1 = digitalRead(buttonPin1);
  buttonState2 = digitalRead(buttonPin2);
  buttonState3 = digitalRead(buttonPin3);
  if (buttonState1 == 1 && buttonState2 == 1 ) {                                               
    init_position();
   }
  if (buttonState2 == 1 && position<pos_f) {                                               
    motor_command(0,speed_DC);
   }
  if (buttonState1 == 1 && position>0) {                                               
    motor_command(1,speed_DC);
   }
  if((buttonState1 == 0 && buttonState2 == 0) || (position<=0 && buttonState1 == 1) || (position >= pos_f && buttonState2 == 1)) {motor_command(2,0);
  }

  if (buttonState3 == 1) {
    if (!button3Pressed) {
      // Button 3 is pressed for the first time
      buttonPressTime = millis();
      button3Pressed = true;
    }

    // Check if the button has been pressed for 3 seconds
    if (millis() - buttonPressTime >= 3000) {
      displacement(speed_DC, position - 10);
      displacement(speed_DC, position + 10);
      pos1 = position;
      delay(500);
    }
  } else {
    // Button 3 is not pressed
    if (button3Pressed) {
      // Button 3 was released, so execute instruction A
      displacement(speed_DC, pos1);
      delay(500);
      button3Pressed = false;
    }
  }

  if (buttonState4 == 1) {
    if (!button4Pressed) {
      // Button 4 is pressed for the first time
      buttonPressTime = millis();
      button4Pressed = true;
    }

    // Check if the button has been pressed for 3 seconds
    if (millis() - buttonPressTime >= 3000) {
      displacement(speed_DC, position - 10);
      displacement(speed_DC, position + 10);
      pos2 = position;
      delay(500);
    }
  } else {
    // Button 4 is not pressed
    if (button4Pressed) {
      // Button 4 was released, so execute instruction B
      displacement(speed_DC, pos2);
      delay(500);
      button4Pressed = false;
    }
  }
}


void motor_command(int motor_way,int motor_speed)
{
  if (motor_way == 1) {
    dir_down=false;
    dir_up=true;
    digitalWrite(in2, HIGH);
    digitalWrite(in1, LOW);
  }
  if (motor_way == 0) {
    dir_up=false;
    dir_down=true;
    digitalWrite(in2, LOW);
    digitalWrite(in1, HIGH);
  }
  if (motor_way == 2){analogWrite(enA,0);digitalWrite(in2, LOW);digitalWrite(in1, LOW);}
  analogWrite(enA,motor_speed);
}

void displacement(int sp, int disp_pos)                                                                         // sp = speed of displacement  & disp_pos = position to go
{                                                                                                                                    // determine way of motor
    while (position<disp_pos){
    motor_command(0,sp);
    }
    motor_command(2,0);
    
    while (position>disp_pos){
    motor_command(1,sp);
    }
    motor_command(2,0);                                                                                     // stop motor
  
    delay(200);                                                                                                   // wait  
}

void init_position()                                                                                // go down and up to learn stroke
{                                                                                   
  motor_command(1,255); 
  PHES = -1;
  HES = digitalRead(HESPin);
  LastTimeChange = millis();
  while ((millis() - LastTimeChange) <= 500)
  {HES = digitalRead(HESPin);
  if (HES != PHES){LastTimeChange = millis();}
  PHES = HES;
  }
  motor_command(2,0);
  delay(300);  
  motor_command(0,255);
  delay(500);
  motor_command(2,0);
  delay(1000);

  position=0;

  delay(1000);
  motor_command(0,255);
  PHES = -1;
  HES = digitalRead(HESPin);
  LastTimeChange = millis();
  while ((millis() - LastTimeChange) <= 500)
  {HES = digitalRead(HESPin);
  if (HES != PHES){LastTimeChange = millis();}
  PHES = HES;
  }
  motor_command(2,0);
  delay(300);  
  motor_command(1,255);
  delay(500);
  motor_command(2,0);
  delay(1000);
  pos_f=position;
  values[0]=50;                                                                                                                                                                                  
}

void storeValuesInFRAM(int data[]) {
  Wire.beginTransmission(FRAM_ADDR);
  Wire.write(0); // Start writing from address 0

  for (int i = 0; i < 5; ++i) {
    Wire.write((byte)(data[i] >> 8)); // Write the high byte
    Wire.write((byte)data[i]);        // Write the low byte
  }

  Wire.endTransmission();
}

void readValuesFromFRAM() {
  Wire.beginTransmission(FRAM_ADDR);
  Wire.write(0); // Start reading from address 0
  Wire.endTransmission();

  Wire.requestFrom(FRAM_ADDR, 10); // Request 10 bytes (2 bytes for each of the 5 values)

  for (int i = 0; i < 5; ++i) {
    byte highByte = Wire.read();
    byte lowByte = Wire.read();
    values[i] = (highByte << 8) | lowByte;
  }
}


void rotation()
{
 if (dir_down == true) {position = position+1;}
 if (dir_up == true) {position = position-1;}
}