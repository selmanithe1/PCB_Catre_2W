/*
 * Carte 2W - CardV2 Flex Sensor Version
 * 
 * MODIFICATIONS vs version originale (31_07_2025.ino):
 * - Capteur HES (effet Hall) REMPLACÉ par capteur Flex résistif Johnson Electric
 * - Lecture Analogique (analogRead) au lieu d'interruption
 * - Interface simplifiée : 2 boutons seulement (UP / DOWN)
 * - Calibration : positions haute/basse mémorisées par lecture analogique
 * - FRAM conservée pour sauvegarder position
 * 
 * BROCHAGE:
 *   Motor   : enA=9, in1=11, in2=12
 *   Bouton UP   : A3  (comme avant)
 *   Bouton DOWN : A2  (comme avant)
 *   Capteur Flex: A1  (NOUVEAU - diviseur de tension 220Ω/Sensor)
 *   Power sense : 5   (inchangé)
 *   LED         : 6   (inchangé)
 *   FRAM (I2C)  : SDA=A4, SCL=A5 via Wire.h
 */

#include <Wire.h>

// ─── ADRESSE FRAM ───────────────────────────────────────────────────────────
#define FRAM_ADDR 0x50
// Addresses FRAM: [0]=flag init, [1]=position_raw, [2]=pos_f_raw, [3]=pos1_raw, [4]=pos2_raw

// ─── PINS ────────────────────────────────────────────────────────────────────
const int enA        = 9;
const int in1        = 11;
const int in2        = 12;
const int btnUp      = A3;   // Bouton UP (flèche vers le haut)
const int btnDown    = A2;   // Bouton DOWN (flèche vers le bas)
const int flexPin    = A1;   // Capteur Flex (nouveau)
const int powerPin   = 5;    // Détection coupure alimentation
const int ledPin     = 6;

// ─── PARAMÈTRES CAPTEUR FLEX ────────────────────────────────────────────────
// Calibration à faire une première fois : noter les valeurs ADC en position
// haute (FLEX_MIN) et basse (FLEX_MAX) du moteur.
// Le capteur lit entre 0 et 1023 (10-bit ADC).
#define FLEX_MIN  50     // Valeur ADC en position haute (ajuster après test)
#define FLEX_MAX  900    // Valeur ADC en position basse (ajuster après test)
#define FLEX_DEADBAND 5  // Tolérance pour considérer qu'on est arrivé à destination

// ─── VITESSE MOTEUR ─────────────────────────────────────────────────────────
int motor_speed = 200; // PWM 0-255

// ─── ÉTATS ──────────────────────────────────────────────────────────────────
int values[5];   // [0]=flag, [1]=pos_raw, [2]=pos_f_raw, [3]=pos1_raw, [4]=pos2_raw

int pos_f  = FLEX_MAX;  // Fin de course analogique
int pos1   = -1;        // Position mémorisée 1 (plus utilisée par bouton, gardée FRAM)
int pos2   = -1;        // Position mémorisée 2

// Lecture boutons
int stUp   = 0;
int stDown = 0;

// ─────────────────────────────────────────────────────────────────────────────
// SETUP
// ─────────────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  Wire.begin();

  pinMode(enA,      OUTPUT);
  pinMode(in1,      OUTPUT);
  pinMode(in2,      OUTPUT);
  pinMode(ledPin,   OUTPUT);
  pinMode(btnUp,    INPUT);
  pinMode(btnDown,  INPUT);
  pinMode(powerPin, INPUT);
  pinMode(flexPin,  INPUT);

  motor_stop();
  delay(200);

  // Lecture FRAM
  readValuesFromFRAM();
  if (values[0] == 50) {
    // Données valides en mémoire
    pos_f = values[2];
    pos1  = values[3];
    pos2  = values[4];
    Serial.println("[INIT] FRAM ok. Positions restaurees.");
  } else {
    // Première mise en route : calibration auto
    Serial.println("[INIT] Premiere mise en route. Calibration...");
    calibrate();
  }

  // Affiche les valeurs au démarrage sur Serial
  Serial.print("[FLEX] Position initiale: ");
  Serial.println(readFlex());
}

// ─────────────────────────────────────────────────────────────────────────────
// LOOP
// ─────────────────────────────────────────────────────────────────────────────
void loop() {

  // Sauvegarde sur coupure d'alimentation
  if (digitalRead(powerPin) == LOW) {
    int curPos = readFlex();
    values[1] = curPos;
    values[2] = pos_f;
    values[3] = pos1;
    values[4] = pos2;
    storeValuesInFRAM(values);
    Serial.println("[POWER] Sauvegarde FRAM avant extinction.");
    delay(800);
  }

  stUp   = digitalRead(btnUp);
  stDown = digitalRead(btnDown);

  int curPos = readFlex();

  // Bouton UP (monter = diminuer la valeur ADC vers FLEX_MIN)
  if (stUp == HIGH && stDown == LOW) {
    if (curPos > FLEX_MIN) {
      motor_up();
    } else {
      motor_stop();
    }
  }
  // Bouton DOWN (descendre = augmenter la valeur ADC vers FLEX_MAX)
  else if (stDown == HIGH && stUp == LOW) {
    if (curPos < pos_f) {
      motor_down();
    } else {
      motor_stop();
    }
  }
  // Aucun bouton : arrêt
  else {
    motor_stop();
  }

  // Debug Serial (à commenter en production)
  Serial.print("Flex ADC: ");
  Serial.print(curPos);
  Serial.print("  |  BtnUp: ");
  Serial.print(stUp);
  Serial.print("  BtnDown: ");
  Serial.println(stDown);

  delay(50);
}

// ─────────────────────────────────────────────────────────────────────────────
// LECTURE CAPTEUR FLEX (moyenne sur 5 échantillons pour stabilité)
// ─────────────────────────────────────────────────────────────────────────────
int readFlex() {
  long sum = 0;
  for (int i = 0; i < 5; i++) {
    sum += analogRead(flexPin);
    delay(2);
  }
  return (int)(sum / 5);
}

// ─────────────────────────────────────────────────────────────────────────────
// DÉPLACEMENT VERS POSITION CIBLE (boucle fermée sur capteur Flex)
// ─────────────────────────────────────────────────────────────────────────────
void goTo(int target) {
  int cur = readFlex();
  unsigned long start = millis();

  while (abs(cur - target) > FLEX_DEADBAND) {
    cur = readFlex();

    if (cur > target) {
      motor_up();    // Diminuer ADC -> monter
    } else {
      motor_down();  // Augmenter ADC -> descendre
    }

    // Timeout sécurité 10 secondes
    if (millis() - start > 10000) {
      Serial.println("[WARN] Timeout deplacement!");
      break;
    }
    delay(20);
  }
  motor_stop();
}

// ─────────────────────────────────────────────────────────────────────────────
// CALIBRATION AUTO (trouver pos_f = fin de course basse)
// ─────────────────────────────────────────────────────────────────────────────
void calibrate() {
  // Monter jusqu'à la butée haute (valeur ADC stable)
  Serial.println("[CAL] Montee vers butee haute...");
  int prev = readFlex();
  motor_up();
  delay(500);
  unsigned long t = millis();
  while (millis() - t < 5000) {
    int cur = readFlex();
    if (abs(cur - prev) < 2) break;  // Plus de mouvement = butée
    prev = cur;
    delay(200);
  }
  motor_stop();
  delay(500);
  int highPos = readFlex();
  Serial.print("[CAL] Butee haute: "); Serial.println(highPos);

  delay(500);

  // Descendre jusqu'à la butée basse
  Serial.println("[CAL] Descente vers butee basse...");
  prev = readFlex();
  motor_down();
  delay(500);
  t = millis();
  while (millis() - t < 10000) {
    int cur = readFlex();
    if (abs(cur - prev) < 2) break;
    prev = cur;
    delay(200);
  }
  motor_stop();
  delay(500);
  pos_f = readFlex();
  Serial.print("[CAL] Butee basse (pos_f): "); Serial.println(pos_f);

  // Sauvegarde FRAM
  values[0] = 50;       // Flag "calibré"
  values[1] = pos_f;    // Position actuelle
  values[2] = pos_f;    // Fin de course
  values[3] = highPos;  // pos1 = butée haute
  values[4] = pos_f;    // pos2 = butée basse
  storeValuesInFRAM(values);
  Serial.println("[CAL] Calibration terminee et sauvegardee.");
}

// ─────────────────────────────────────────────────────────────────────────────
// COMMANDES MOTEUR
// ─────────────────────────────────────────────────────────────────────────────
void motor_up() {
  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  analogWrite(enA, motor_speed);
}

void motor_down() {
  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  analogWrite(enA, motor_speed);
}

void motor_stop() {
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  analogWrite(enA, 0);
}

// ─────────────────────────────────────────────────────────────────────────────
// FRAM : LECTURE / ÉCRITURE
// ─────────────────────────────────────────────────────────────────────────────
void storeValuesInFRAM(int data[]) {
  Wire.beginTransmission(FRAM_ADDR);
  Wire.write(0);
  for (int i = 0; i < 5; i++) {
    Wire.write((byte)(data[i] >> 8));
    Wire.write((byte)data[i]);
  }
  Wire.endTransmission();
}

void readValuesFromFRAM() {
  Wire.beginTransmission(FRAM_ADDR);
  Wire.write(0);
  Wire.endTransmission();
  Wire.requestFrom(FRAM_ADDR, 10);
  for (int i = 0; i < 5; i++) {
    byte hi = Wire.read();
    byte lo = Wire.read();
    values[i] = (hi << 8) | lo;
  }
}