# PCB Carte 2W — Actionneur Flex Sensor (Johnson Electric)

> Projet de carte PCB 2 voies pour le pilotage d'un actionneur linéaire
> > via un capteur Flex PCB résistif de Johnson Electric.
> > > Conçu pour l'application **AT C229** — interface 2 boutons (Up / Down).
> > >
> > > ---
> > >
> > > ## Table des matières
> > >
> > > 1. [Contexte du projet](#1-contexte-du-projet)
> > > 2. 2. [Spécifications techniques](#2-spécifications-techniques)
> > >    3. 3. [Architecture de la carte](#3-architecture-de-la-carte)
> > >       4. 4. [Composants principaux (BOM)](#4-composants-principaux-bom)
> > >          5. 5. [Brochage Arduino](#5-brochage-arduino)
> > >             6. 6. [Firmware — Programme C++](#6-firmware--programme-c)
> > >                7. 7. [Variantes de cartes](#7-variantes-de-cartes)
> > >                   8. 8. [Structure des fichiers](#8-structure-des-fichiers)
> > >                      9. 9. [Commande & Fabrication](#9-commande--fabrication)
> > >                         10. 10. [Tâches en cours](#10-tâches-en-cours)
> > >                             11. 11. [Équipe](#11-équipe)
> > >                                
> > >                                 12. ---
> > >                                
> > >                                 13. ## 1. Contexte du projet
> > >                                
> > >                                 14. La carte **2W** est une évolution de la carte existante de Sohaib. Elle doit être modifiée pour :
> > >
> > > - Intégrer le **capteur Flex PCB résistif de Johnson Electric** (en remplacement du capteur à effet Hall HES).
> > > - - Piloter l'actionneur via un driver moteur **L298P**.
> > >   - - Préparer la transition vers la future **carte 4W** (prévue pour avril).
> > >     - - Offrir uniquement **2 boutons** (Up & Down) comme interface utilisateur sur AT C229.
> > >      
> > >       - ---
> > >
> > > ## 2. Spécifications techniques
> > >
> > > ### Capteur Flex PCB (Johnson Electric)
> > >
> > > | Paramètre | Valeur |
> > > |---|---|
> > > | Tension d'alimentation | **5 V** (confirmé par Paul Dyckes) |
> > > | Type | Résistif |
> > > | Nombre de broches | **6 pins** (dont 2 masses) |
> > > | Résistance par capteur | ~15 Ω |
> > > | Résistance de piste (100 mm) | ~12 Ω |
> > > | Lecture ADC | 10 bits (0–1023) |
> > > | `FLEX_MIN` (position haute) | ~50 (à calibrer) |
> > > | `FLEX_MAX` (position basse) | ~900 (à calibrer) |
> > > | `FLEX_DEADBAND` | 5 (tolérance d'arrêt) |
> > >
> > > ### Connecteur FPC/FFC
> > >
> > > | Paramètre | Valeur |
> > > |---|---|
> > > | Référence | `FH52K-12(6)SA-1SH(99)` |
> > > | Fabricant | HIROSE / HRS |
> > > | Contacts | 6 (12P6C) |
> > > | Largeur | 8,1 mm |
> > > | Fournisseur | Laurent GEORGES (déjà acheté) |
> > >
> > > ### Alimentation carte
> > >
> > > - **5 V** régulés par deux régulateurs `L7805CDT-TR` (ST Microelectronics)
> > >
> > > - ---
> > >
> > > ## 3. Architecture de la carte
> > >
> > > ```
> > > [Alimentation 5V] --> [L7805CDT-TR x2]
> > >         |
> > > [Arduino / µC] <-- [Bouton UP (A3)] <-- [Bouton DOWN (A2)]
> > >         |
> > >    [L298P Driver] --> [Moteur (H2 - connecteur 4 pins)]
> > >         ^
> > > [Capteur Flex (A1)] <-- [Diviseur de tension 220Ohm / Sensor]
> > >         |
> > >   [FRAM FM24CL16B - I2C SDA:A4 / SCL:A5] --> sauvegarde position
> > > ```
> > >
> > > ---
> > >
> > > ## 4. Composants principaux (BOM)
> > >
> > > | Désignateur | Composant | Description |
> > > |---|---|---|
> > > | L298P | L298P (ST) | Driver moteur H-Bridge, POWERSO-20 |
> > > | U1 | LM741CN (TI) | Amplificateur opérationnel, DIP-8 |
> > > | U2, U3 | L7805CDT-TR (ST) | Régulateur 5V, TO-252 |
> > > | U5 | FM24CL16B-GTR (Cypress) | FRAM I2C 16Kbit, SOIC-8 |
> > > | U7, U8 | SS14HE3_B/I (Vishay) | Diode Schottky, SMA |
> > > | SK1 | ICS-28P | Support CI 28 broches, DIP-28 |
> > > | D1 | MM1Z5V1 | Diode Zener 5,1V, SOD-123 |
> > > | D2–D5 | SS34 | Diode Schottky 3A, SMA |
> > > | C1, C2 | 10 µF | Condensateur électrolytique, SMD |
> > > | C4 | 1000 µF | Condensateur électrolytique, SMD |
> > > | U9, U10 | 220 µF | Condensateur électrolytique, SMD |
> > > | R1 | 10 kOhm | Résistance, R1206 |
> > > | R2 | 4,7 kOhm | Résistance, R1206 |
> > > | R3 | 180 Ohm | Résistance puissance, R2512 |
> > > | R4 | 1 kOhm | Résistance, R2010 |
> > > | H2 | Connecteur Moteur | HDR 1x4, pas 2,54 mm |
> > > | H3 | Connecteur Power | HDR 1x2, pas 2,54 mm |
> > > | H4 | Connecteur Boutons | HDR 1x6, pas 2,54 mm |
> > >
> > > > Fichier BOM complet : [`BOM_CardV2 copy_2025-09-15.csv`](./BOM_CardV2%20copy_2025-09-15.csv)
> > > >
> > > > ---
> > > >
> > > > ## 5. Brochage Arduino
> > > >
> > > > | Signal | Pin Arduino | Note |
> > > > |---|---|---|
> > > > | Motor Enable A | 9 (enA) | PWM |
> > > > | Motor IN1 | 11 | Direction |
> > > > | Motor IN2 | 12 | Direction |
> > > > | Bouton UP | A3 | Flèche vers le haut |
> > > > | Bouton DOWN | A2 | Flèche vers le bas |
> > > > | Capteur Flex | A1 | Lecture analogique (0–1023) |
> > > > | Power Sense | 5 | Détection coupure alimentation |
> > > > | LED | 6 | Indicateur |
> > > > | FRAM SDA | A4 | I2C via Wire.h |
> > > > | FRAM SCL | A5 | I2C via Wire.h |
> > > >
> > > > ---
> > > >
> > > > ## 6. Firmware — Programme C++
> > > >
> > > > Le firmware est écrit en **C++ Arduino** (`.ino`).
> > > >
> > > > **Fichier principal** : [`31_07_2025/31_07_2025.ino`](./31_07_2025/31_07_2025.ino)
> > > >
> > > > ### Fonctionnement
> > > >
> > > > - Lecture analogique du capteur Flex (remplace le capteur Hall HES).
> > > > - - Contrôle moteur via L298P (PWM sur `enA`, direction sur `in1`/`in2`).
> > > >   - - Mémorisation de la position en **FRAM (I2C)** à l'adresse `0x50`.
> > > >     - - Gestion des boutons UP/DOWN avec arrêt automatique en fin de course.
> > > >       - - Calibration manuelle : ajuster `FLEX_MIN` et `FLEX_MAX` selon le capteur réel.
> > > >        
> > > >         - ### Paramètres à calibrer
> > > >        
> > > >         - ```cpp
> > > >           #define FLEX_MIN      50   // Valeur ADC en position HAUTE (à ajuster)
> > > >           #define FLEX_MAX      900  // Valeur ADC en position BASSE (à ajuster)
> > > >           #define FLEX_DEADBAND 5    // Tolérance d'arrêt (+/- 5 unités ADC)
int motor_speed = 200;     // Vitesse PWM (0–255)
```

### Adresses FRAM

| Index | Contenu |
|---|---|
| [0] | Flag d'initialisation |
| [1] | position_raw |
| [2] | pos_f_raw |
| [3] | pos1_raw |
| [4] | pos2_raw |

---

## 7. Variantes de cartes

| Dossier | Description |
|---|---|
| `3 Buttons card with capacitive sensors/` | Variante 3 boutons avec capteurs capacitifs |
| `3 Buttons card without capacitive sensors/` | Variante 3 boutons sans capteurs capacitifs |
| `31_07_2025/` (carte principale) | Version 2 boutons + capteur Flex résistif |

---

## 8. Structure des fichiers

```
PCB_Catre_2W/
├── README.md                                        <- Ce fichier
├── Details techniques.txt                           <- Notes de brief projet
├── Tesca.pptx                                       <- Présentation projet
│
├── [Racine] Fichiers CardV2 principale
│   ├── PCB_PCB_CardV2_2_2025-09-15.json            <- Fichier PCB EasyEDA
│   ├── PCB_PCB_CardV2_2_2025-09-15.pdf             <- Export PCB (visualisation)
│   ├── SCH_CardV2 copy_2025-09-15_BACKUP.json      <- Schéma EasyEDA (backup)
│   ├── Schematic_CardV2 copy_2025-09-15.pdf        <- Export schéma
│   └── BOM_CardV2 copy_2025-09-15.csv              <- Bill of Materials
│
├── 31_07_2025/                                      <- Firmware Arduino
│   └── 31_07_2025.ino                              <- Programme principal C++
│
├── 3 Buttons card with capacitive sensors/          <- Variante schéma
│   ├── SCH_Carte_des_boutons_capacitives_2025-09-15.json
│   └── Schematic_Carte_des_boutons_capacitives_2025-09-15.pdf
│
├── 3 Buttons card without capacitive sensors/       <- Variante schéma
│   ├── SCH_Card_Capacitive_without_capacitor_2025-09-15.json
│   └── Schematic_Card_Capacitive_without_capacitor_2025-09-15.pdf
│
└── Images/                                          <- Captures et visuels
    ├── image.png / image (1).png / image (2).png
        ├── image006.png / image009.png
            └── Untitled3 (2).png / Untitled4 (2).png / Untitled6 (2).png
            ```

            ---

            ## 9. Commande & Fabrication

            - Fabricant cible : **[JLCPCB](https://jlcpcb.com)**
            - Fournisseur composants : **LCSC** (toutes les références sont dans le BOM)
            - Format requis pour commande : fichiers **Gerber** à générer depuis EasyEDA avant envoi

            ---

            ## 10. Tâches en cours

            - [ ] Valider la réutilisation / modification de la carte 2W existante
            - [ ] Finaliser le layout PCB CardV2 (intégrer connecteur FPC Johnson Electric)
            - [ ] Calibrer les valeurs `FLEX_MIN` / `FLEX_MAX` avec le capteur réel
            - [ ] Modifier le programme C++ pour le nouveau capteur Flex
            - [ ] Générer les fichiers Gerber et commander chez JLCPCB
            - [ ] Préparer la transition vers la carte **4W** (prévue en avril)

            ---

            ## 11. Équipe

            | Personne | Rôle |
            |---|---|
            | **Mohamed SELMANI** | Conception PCB & développement firmware |
            | **Laurent GEORGES** | Responsable projet, achat connecteur FPC |
            | **Paul Dyckes** | Validation technique capteur Johnson Electric |
            | **Sohaib** | Auteur de la carte 2W originale (référence) |
