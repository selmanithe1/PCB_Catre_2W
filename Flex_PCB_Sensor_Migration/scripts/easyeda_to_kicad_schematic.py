#!/usr/bin/env python3
"""
easyeda_to_kicad_schematic.py
==============================
Convertisseur EasyEDA JSON -> KiCad Schematic (.kicad_sch)
Projet : PCB Carte 2W - Migration Capteur Flex PCB
Auteur : Selmani Mohamed

Description:
    Convertit le fichier JSON schema EasyEDA vers le format natif KiCad,
    incluant les nouveaux composants pour le connecteur FPC 6 broches
    FH52K-12(6)SA-1SH(99) et les resistances de pull-down 220 Ohm.

Usage:
    pip install easyeda2kicad
    python easyeda_to_kicad_schematic.py \
        --input SCH_CardV2_copy_2025-09-15_BACKUP.json \
        --output output/CardV2_FlexPCB.kicad_sch
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIGURATION : Brochage connecteur FH52K-12(6)SA-1SH(99)
# ============================================================
# Pin 1: GND | Pin 2: DOWN_A | Pin 3: DOWN_B
# Pin 4: UP_A | Pin 5: UP_B  | Pin 6: GND
# Principe: pas de contact => I=0A (etat 0)
#           contact => I = U/R = 5V/20Ohm = 0.25A (etat 1)

FPC_CONNECTOR = {
    "reference": "J_FLEX",
    "value": "FH52K-12(6)SA-1SH(99)",
    "manufacturer": "HIROSE",
    "mpn": "FH52K-12(6)SA-1SH(99)",
    "description": "Connecteur FPC/FFC 6P, 1mm pitch, SMD, ZIF",
    "supply_voltage": "5V",
    "sensor_resistance": "~20 Ohm (approximatif)",
    "max_current": "0.25A (I=U/R=5V/20Ohm)",
    "pins": [
        {"number": 1, "name": "GND",    "type": "pwrIn"},
        {"number": 2, "name": "DOWN_A", "type": "input"},
        {"number": 3, "name": "DOWN_B", "type": "input"},
        {"number": 4, "name": "UP_A",   "type": "input"},
        {"number": 5, "name": "UP_B",   "type": "input"},
        {"number": 6, "name": "GND",    "type": "pwrIn"},
    ]
}

PULLDOWN_RESISTORS = [
    {"reference": "R_UP",   "value": "220", "nets": ["UP_SIG",   "GND"]},
    {"reference": "R_DOWN", "value": "220", "nets": ["DOWN_SIG", "GND"]},
]

# ============================================================
# KICAD SCHEMATIC HEADER
# ============================================================

def get_kicad_header(date_str):
    return f"""(kicad_sch
  (version 20231120)
  (generator easyeda_to_kicad_cardv2)
  (paper A4)
  (title_block
    (title "PCB Carte 2W - Capteur Flex PCB Johnson Electric")
    (date "{date_str}")
    (rev "2.0")
    (company "AT C229 Project")
    (comment 1 "Migration HES -> Flex PCB FH52K-12(6)SA-1SH(99)")
    (comment 2 "Auteur: Selmani Mohamed")
    (comment 3 "5V | ~0.25A @ 20Ohm | Capteur 0/1 numerique")
  )
"""

# ============================================================
# PARSING EASYEDA JSON
# ============================================================

def parse_easyeda_schematic(json_path):
    """Parse le fichier JSON EasyEDA et extrait les composants."""
    print(f"[INFO] Chargement schema EasyEDA: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    components, wires, nets = [], [], {}
    schematics = data.get("schematics", [data])
    for sheet in schematics:
        data_str = sheet.get("dataStr", sheet)
        shapes = data_str.get("shape", [])
        for shape in shapes:
            if isinstance(shape, str):
                parts = shape.split("~")
                if parts[0] == "WIRE" and len(parts) >= 4:
                    coords = parts[3].split(" ")
                    if len(coords) >= 4:
                        wires.append({
                            "x1": float(coords[0]), "y1": float(coords[1]),
                            "x2": float(coords[2]), "y2": float(coords[3]),
                            "net": parts[2] if len(parts) > 2 else ""
                        })
    print(f"[INFO] Fils trouves: {len(wires)}")
    return {"components": components, "wires": wires, "nets": nets}

# ============================================================
# CONVERSION COORDONNEES
# ============================================================

def easyeda_to_kicad_mm(x, y):
    """Convertit coordonnees EasyEDA (pixel) -> KiCad (mm).
    EasyEDA: 1px = 10 mils = 0.254mm. Offset de reference EasyEDA ~ 4000,3000.
    """
    SCALE = 0.0254
    kx = round((x - 4000) * SCALE, 3)
    ky = round((y - 3000) * SCALE, 3)
    return kx, ky

# ============================================================
# GENERATION COMPOSANTS KICAD
# ============================================================

def gen_fpc_connector(conn, px, py):
    """Genere un composant connecteur FPC KiCad (.kicad_sch format)."""
    pins = ""
    for p in conn["pins"]:
        pin_y = py + (p["number"] - 3.5) * 2.54
        pins += f"""
    (pin {p["type"]} line (at {px-5.08:.3f} {pin_y:.3f} 0) (length 2.54)
      (name "{p["name"]}" (effects (font (size 1.27 1.27))))
      (number "{p["number"]}" (effects (font (size 1.27 1.27))))
    )"""
    return f"""
  (symbol "{conn["reference"]}" (in_bom yes) (on_board yes)
    (property "Reference" "{conn["reference"]}" (at {px:.3f} {py-10:.3f} 0)
      (effects (font (size 1.27 1.27))))
    (property "Value" "{conn["value"]}" (at {px:.3f} {py+10:.3f} 0)
      (effects (font (size 1.27 1.27))))
    (property "Footprint" "Connector_FFC-FPC:Hirose_FH52_06-1SH_1x06-1MP_1mm"
      (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "{conn["reference"]}_0_1"
      (rectangle (start -2.54 -8.89) (end 2.54 8.89)
        (stroke (width 0) (type default))
        (fill (type background)))
      {pins}
    )
  )"""

def gen_resistor(ref, value, px, py):
    """Genere un symbole resistance KiCad."""
    return f"""
  (symbol "{ref}" (in_bom yes) (on_board yes)
    (property "Reference" "{ref}" (at {px:.3f} {py-2:.3f} 0)
      (effects (font (size 1.27 1.27))))
    (property "Value" "{value} Ohm" (at {px:.3f} {py+2:.3f} 0)
      (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_1206_3216Metric"
      (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Description" "Pull-down resistor for Flex PCB sensor"
      (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "{ref}_0_1"
      (rectangle (start {px-0.762:.3f} {py+0.508:.3f}) (end {px+0.762:.3f} {py-0.508:.3f})
        (stroke (width 0) (type default))
        (fill (type background)))
    )
    (pin passive line (at {px-2.54:.3f} {py:.3f} 0) (length 1.524)
      (name "~" (effects (font (size 1.27 1.27))))
      (number "1" (effects (font (size 1.27 1.27))))
    )
    (pin passive line (at {px+2.54:.3f} {py:.3f} 180) (length 1.524)
      (name "~" (effects (font (size 1.27 1.27))))
      (number "2" (effects (font (size 1.27 1.27))))
    )
  )"""

# ============================================================
# GENERATION FICHIER KICAD_SCH
# ============================================================

def generate_kicad_schematic(easyeda_data, output_path):
    """Genere le fichier .kicad_sch complet."""
    print(f"[INFO] Generation schema KiCad: {output_path}")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    # Positions des composants
    fpc_x, fpc_y = 150.0, 100.0
    r_up_x, r_up_y = 172.0, 90.0
    r_dn_x, r_dn_y = 172.0, 115.0
    # Construire le schema
    content = get_kicad_header(date_str)
    content += gen_fpc_connector(FPC_CONNECTOR, fpc_x, fpc_y)
    content += gen_resistor("R_UP", "220", r_up_x, r_up_y)
    content += gen_resistor("R_DOWN", "220", r_dn_x, r_dn_y)
    # Ajouter les fils convertis
    for w in easyeda_data.get("wires", []):
        x1, y1 = easyeda_to_kicad_mm(w["x1"], w["y1"])
        x2, y2 = easyeda_to_kicad_mm(w["x2"], w["y2"])
        content += f"""
  (wire (pts (xy {x1:.3f} {y1:.3f}) (xy {x2:.3f} {y2:.3f}))
    (stroke (width 0) (type default)))"""
    content += "\n)\n"  # Fermeture kicad_sch
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Schema KiCad: {output_path} ({os.path.getsize(output_path)} octets)")

# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="EasyEDA JSON -> KiCad Schematic Converter (PCB Carte 2W)")
    parser.add_argument("--input", "-i", required=True,
                        help="Chemin vers le JSON EasyEDA schematic")
    parser.add_argument("--output", "-o", required=True,
                        help="Chemin de sortie .kicad_sch")
    args = parser.parse_args()
    if not os.path.exists(args.input):
        print(f"[ERREUR] Fichier source introuvable: {args.input}", file=sys.stderr)
        sys.exit(1)
    print("=" * 60)
    print("  EasyEDA -> KiCad Schematic Converter v1.0")
    print("  PCB Carte 2W - Migration Capteur Flex PCB FH52K")
    print("  Brochage: 1=GND 2=DOWN 3=DOWN 4=UP 5=UP 6=GND")
    print("  Electrique: 5V, R~20Ohm, I=0.25A au contact")
    print("=" * 60)
    data = parse_easyeda_schematic(args.input)
    generate_kicad_schematic(data, args.output)
    print("\n[TERMINE] Ouvrir le .kicad_sch dans KiCad 7/8.")

if __name__ == "__main__":
    main()
