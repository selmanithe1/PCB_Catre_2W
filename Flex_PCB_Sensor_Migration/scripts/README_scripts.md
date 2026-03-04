# Scripts de Migration EasyEDA -> KiCad
## PCB Carte 2W - Migration Capteur Flex PCB FH52K-12(6)SA-1SH(99)

Ce dossier contient les scripts Python pour convertir les fichiers EasyEDA
du projet PCB Carte 2W vers le format KiCad, avec integration du nouveau
connecteur FPC 6 broches.

---

## Contexte du changement de capteur

| Aspect | Ancien (HES) | Nouveau (Flex PCB) |
|--------|-------------|-------------------|
| Type | Effet Hall (magnetique) | Resistif (contact) |
| Broches | 3 (VCC, GND, SIG) | 6 (2xGND, 2xUP, 2xDOWN) |
| Connecteur | JST/DIP standard | FPC FH52K-12(6)SA-1SH(99) |
| Lecture | Interruption numerique | digitalRead() / analogRead() |
| Logique | 0 = champ absent | 0 = pas contact (I=0A) |
|         | 1 = champ detecte | 1 = contact (I=U/R=0.25A) |

## Principe electrique du capteur Flex

```
Alimentation : 5V
Resistance capteur (approx.) : ~20 Ohm (piste ~12 Ohm + capteur ~15 Ohm)
Courant au contact : I = U/R = 5V / 20 Ohm = 0.25A
Capteur numerique : 0 (repos) / 1 (appui)
```

## Brochage connecteur FH52K-12(6)SA-1SH(99)

```
Broche 1 : GND    (masse)
Broche 2 : DOWN   (signal capteur bas, vers Arduino A2)
Broche 3 : DOWN   (signal capteur bas, double)
Broche 4 : UP     (signal capteur haut, vers Arduino A3)
Broche 5 : UP     (signal capteur haut, double)
Broche 6 : GND    (masse)
```

---

## Installation

```bash
# Prerequis : Python 3.8+, KiCad 7 ou 8
pip install easyeda2kicad

# Cloner le projet
git clone https://github.com/selmanithe1/PCB_Catre_2W.git
cd PCB_Catre_2W
```

---

## Scripts disponibles

### 1. `easyeda_to_kicad_schematic.py`

Convertit le schema EasyEDA JSON vers le format KiCad (.kicad_sch).
Ajoute automatiquement le connecteur FPC J_FLEX et les resistances pull-down R_UP/R_DOWN (220 Ohm).

```bash
python scripts/easyeda_to_kicad_schematic.py \
  --input SCH_CardV2_copy_2025-09-15_BACKUP.json \
  --output output/CardV2_FlexPCB.kicad_sch
```

**Composants generes automatiquement :**
- `J_FLEX` : Connecteur FPC FH52K-12(6)SA-1SH(99)
- `R_UP` : Resistance pull-down 220 Ohm (signal UP)
- `R_DOWN` : Resistance pull-down 220 Ohm (signal DOWN)

---

### 2. `easyeda_to_kicad_pcb.py`

Convertit le PCB EasyEDA JSON vers le format KiCad (.kicad_pcb).
Ajoute l empreinte du connecteur FPC et les resistances.

```bash
python scripts/easyeda_to_kicad_pcb.py \
  --input PCB_PCB_CardV2_2_2025-09-15.json \
  --output output/CardV2_FlexPCB.kicad_pcb
```

**Notes importantes :**
- Placer J_FLEX **en bord de carte** pour l insertion du cable flexible
- Largeur de piste recommandee : **0.3 mm** (pour 0.25A)
- Executer DRC apres placement

---

### 3. `generate_kicad_fpc_component.py`

Genere le symbole schematique et l empreinte PCB du connecteur FH52K.

```bash
python scripts/generate_kicad_fpc_component.py --output-dir output/
```

**Fichiers generes :**
- `output/FH52K_6P.kicad_sym` : Symbole schematique KiCad
- `output/FH52K_6P.kicad_mod` : Empreinte PCB KiCad

**Integration dans KiCad :**
1. `Preferences > Manage Symbol Libraries > Add` -> selectionner `FH52K_6P.kicad_sym`
2. `Preferences > Manage Footprint Libraries > Add` -> selectionner le dossier `output/`
3. Dans le schema : `Place > Add Symbol > FH52K-12(6)SA-1SH(99)`

---

## Workflow complet

```bash
# Etape 1 : Generer le composant FPC
python scripts/generate_kicad_fpc_component.py --output-dir output/

# Etape 2 : Convertir le schema
python scripts/easyeda_to_kicad_schematic.py \
  --input SCH_CardV2_copy_2025-09-15_BACKUP.json \
  --output output/CardV2_FlexPCB.kicad_sch

# Etape 3 : Convertir le PCB
python scripts/easyeda_to_kicad_pcb.py \
  --input PCB_PCB_CardV2_2_2025-09-15.json \
  --output output/CardV2_FlexPCB.kicad_pcb

# Etape 4 : Ouvrir dans KiCad
# - Ouvrir output/CardV2_FlexPCB.kicad_sch dans KiCad Schematic Editor
# - Verifier le placement des composants
# - Tools > Update PCB from Schematic
# - Placer J_FLEX en bord de carte
# - Router les pistes (0.3mm min)
# - DRC -> generer Gerber -> commander sur JLCPCB
```

---

## Modifications du firmware (Arduino)

Le fichier `31_07_2025/31_07_2025.ino` contient deja le code adapte au
nouveau capteur Flex PCB. Points cles :

```cpp
const int btnUp   = A3;  // UP  capteur Flex (broches 4+5)
const int btnDown = A2;  // DOWN capteur Flex (broches 2+3)
const int flexPin = A1;  // Lecture analogique position

#define FLEX_MIN 50    // ADC position haute (a calibrer)
#define FLEX_MAX 900   // ADC position basse (a calibrer)
```

---

## Informations composant

| Parametre | Valeur |
|-----------|--------|
| Reference | FH52K-12(6)SA-1SH(99) |
| Fabricant | HIROSE / HRS |
| Type | FPC/FFC, 6P, 1mm pitch, SMD ZIF |
| Code commande | 4399219 (Farnell/RS) |
| Prix unitaire | 2.22 EUR HT |
| Quantite commandee | 13 pieces |

---

## Equipe

- **Selmani Mohamed** - Conception PCB & Firmware
- **Laurent Georges** - Responsable projet, achat connecteurs
- **Paul Dyckes** - Validation technique capteur Johnson Electric
