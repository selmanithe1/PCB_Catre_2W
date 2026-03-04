#!/usr/bin/env python3
"""
generate_kicad_fpc_component.py
================================
Generateur symbole+empreinte KiCad pour FH52K-12(6)SA-1SH(99)
Brochage: 1=GND | 2=DOWN | 3=DOWN | 4=UP | 5=UP | 6=GND
Electrique: 5V | R~20Ohm | I=0.25A | Capteur 0/1

Usage: python generate_kicad_fpc_component.py --output-dir output/
"""

import argparse, os
from datetime import datetime

COMP = {
    "name": "FH52K-12(6)SA-1SH(99)",
    "desc": "Connecteur FFC/FPC 6P 1mm pitch SMD ZIF HIROSE",
    "keywords": "FFC FPC 6pin 1mm ZIF SMD HIROSE FH52",
    "datasheet": "https://www.hirose.com/product/series/FH52",
    "code_fournisseur": "4399219",
    "tension": "5V",
    "resistance": "~20 Ohm",
    "courant": "0.25A (I=U/R=5/20)",
    "logique": "0=repos I=0A / 1=contact I=0.25A",
    "pitch": 1.0,
    "contacts": 6,
    "pad_w": 0.6, "pad_h": 1.5,
    "bw": 8.1, "bh": 4.0,
    "pins": [
        (1, "GND",    "pwrIn",  "L"),
        (2, "DOWN_A", "input",  "L"),
        (3, "DOWN_B", "input",  "L"),
        (4, "UP_A",   "input",  "R"),
        (5, "UP_B",   "input",  "R"),
        (6, "GND",    "pwrIn",  "R"),
    ]
}

def gen_symbol(c, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    lp = [(n,nm,t) for n,nm,t,s in c["pins"] if s=="L"]
    rp = [(n,nm,t) for n,nm,t,s in c["pins"] if s=="R"]
    h = max(len(lp),len(rp))*2.54+1.27
    ps = ""
    for i,(n,nm,t) in enumerate(lp):
        y = (len(lp)/2-i-0.5)*2.54
        ps += f"""
      (pin {t} line (at -5.08 {y:.3f} 0)(length 2.54)
        (name "{nm}" (effects (font (size 1.27 1.27))))
        (number "{n}" (effects (font (size 1.27 1.27)))))"""
    for i,(n,nm,t) in enumerate(rp):
        y = (len(rp)/2-i-0.5)*2.54
        ps += f"""
      (pin {t} line (at 5.08 {y:.3f} 180)(length 2.54)
        (name "{nm}" (effects (font (size 1.27 1.27))))
        (number "{n}" (effects (font (size 1.27 1.27)))))"""
    sym = f"""(kicad_symbol_lib (version 20231120)(generator kicad_symbol_editor)
  (symbol "{c["name"]}"
    (pin_names (offset 1.016))(in_bom yes)(on_board yes)
    (property "Reference" "J" (at 0 {h+1:.2f} 0)(effects (font (size 1.27 1.27))))
    (property "Value" "{c["name"]}" (at 0 {-h-1:.2f} 0)(effects (font (size 1.27 1.27))))
    (property "Footprint" "Connector_FFC-FPC:Hirose_FH52_06-1SH_1x06-1MP_1mm" (at 0 0 0)(effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "{c["datasheet"]}" (at 0 0 0)(effects (font (size 1.27 1.27)) hide))
    (property "Description" "{c["desc"]}" (at 0 0 0)(effects (font (size 1.27 1.27)) hide))
    (property "Tension" "{c["tension"]}" (at 0 0 0)(effects (font (size 1.27 1.27)) hide))
    (property "Courant_max" "{c["courant"]}" (at 0 0 0)(effects (font (size 1.27 1.27)) hide))
    (property "Logique" "{c["logique"]}" (at 0 0 0)(effects (font (size 1.27 1.27)) hide))
    (property "Code_Fournisseur" "{c["code_fournisseur"]}" (at 0 0 0)(effects (font (size 1.27 1.27)) hide))
    (symbol "{c["name"]}_0_1"
      (rectangle (start -2.54 {-h:.3f})(end 2.54 {h:.3f})
        (stroke (width 0.254)(type default))(fill (type background)))
      {ps}
    )
  )
)
"""
    with open(path,"w",encoding="utf-8") as f: f.write(sym)
    print(f"[OK] Symbole KiCad: {path}")

def gen_footprint(c, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    n, p, pw, ph = c["contacts"], c["pitch"], c["pad_w"], c["pad_h"]
    bw, bh = c["bw"], c["bh"]
    sx = -(n-1)/2*p
    nm_map = {1:"GND",2:"DOWN_SIG",3:"DOWN_SIG",4:"UP_SIG",5:"UP_SIG",6:"GND"}
    pads = ""
    for num,nm,t,s in c["pins"]:
        px = sx + (num-1)*p
        pads += f"""  (pad "{num}" smd rect (at {px:.4f} 0)(size {pw} {ph})
    (layers "F.Cu" "F.Paste" "F.Mask"))\n"""
    for mx in [-(bw/2+0.5), bw/2+0.5]:
        pads += f"""  (pad "" smd rect (at {mx:.4f} 0)(size 1.6 1.6)
    (layers "F.Cu" "F.Paste" "F.Mask"))\n"""
    mod = f"""(footprint "{c["name"]}"
  (version 20240108)(generator kicad_fpc_gen)(layer "F.Cu")
  (descr "{c["desc"]}")(tags "{c["keywords"]}")(attr smd)
  (property "Reference" "J" (at 0 {-bh/2-2:.2f} 0)(layer "F.SilkS")
    (effects (font (size 1 1)(thickness 0.15))))
  (property "Value" "{c["name"]}" (at 0 {bh/2+2:.2f} 0)(layer "F.Fab")
    (effects (font (size 1 1)(thickness 0.15))))
  (fp_text "1=GND 2,3=DOWN 4,5=UP 6=GND" (at 0 {bh/2+0.8:.2f} 0)(layer "F.Fab")
    (effects (font (size 0.8 0.8)(thickness 0.12))))
  (fp_text "{c["tension"]} R{c["resistance"]} I={c["courant"]}" (at 0 {bh/2+2:.2f} 0)(layer "F.Fab")
    (effects (font (size 0.6 0.6)(thickness 0.1))))
  (fp_line (start {-bw/2:.3f} {-bh/2:.3f})(end {bw/2:.3f} {-bh/2:.3f})(layer "F.SilkS")(width 0.12))
  (fp_line (start {bw/2:.3f} {-bh/2:.3f})(end {bw/2:.3f} {bh/2:.3f})(layer "F.SilkS")(width 0.12))
  (fp_line (start {bw/2:.3f} {bh/2:.3f})(end {-bw/2:.3f} {bh/2:.3f})(layer "F.SilkS")(width 0.12))
  (fp_line (start {-bw/2:.3f} {bh/2:.3f})(end {-bw/2:.3f} {-bh/2:.3f})(layer "F.SilkS")(width 0.12))
  (fp_line (start {-bw/2-0.2:.3f} {-bh/2-0.2:.3f})(end {bw/2+0.2:.3f} {-bh/2-0.2:.3f})(layer "F.CrtYd")(width 0.05))
  (fp_line (start {bw/2+0.2:.3f} {-bh/2-0.2:.3f})(end {bw/2+0.2:.3f} {bh/2+0.2:.3f})(layer "F.CrtYd")(width 0.05))
  (fp_line (start {bw/2+0.2:.3f} {bh/2+0.2:.3f})(end {-bw/2-0.2:.3f} {bh/2+0.2:.3f})(layer "F.CrtYd")(width 0.05))
  (fp_line (start {-bw/2-0.2:.3f} {bh/2+0.2:.3f})(end {-bw/2-0.2:.3f} {-bh/2-0.2:.3f})(layer "F.CrtYd")(width 0.05))
  {pads})
"""
    with open(path,"w",encoding="utf-8") as f: f.write(mod)
    print(f"[OK] Empreinte KiCad: {path}")

def main():
    ap = argparse.ArgumentParser(description="Generateur KiCad FH52K-12(6)SA-1SH(99)")
    ap.add_argument("--output-dir","-o",default="output")
    a = ap.parse_args()
    print("=" * 55)
    print("  Generateur KiCad: FH52K-12(6)SA-1SH(99)")
    print("  Brochage: 1=GND 2,3=DOWN 4,5=UP 6=GND")
    print("  Electrique: 5V | R~20Ohm | I=0.25A")
    print("  Capteur 0/1: repos=0A / contact=0.25A")
    print("=" * 55)
    gen_symbol(COMP, os.path.join(a.output_dir,"FH52K_6P.kicad_sym"))
    gen_footprint(COMP, os.path.join(a.output_dir,"FH52K_6P.kicad_mod"))
    print()
    print("Integration KiCad:")
    print("  Preferences > Manage Symbol Libraries > Ajouter .kicad_sym")
    print("  Preferences > Manage Footprint Libraries > Ajouter dossier .kicad_mod")

if __name__=="__main__": main()
