#!/usr/bin/env python3
"""
easyeda_to_kicad_pcb.py
========================
Convertisseur EasyEDA PCB JSON -> KiCad PCB (.kicad_pcb)
Projet : PCB Carte 2W - Migration Capteur Flex PCB Johnson Electric
Auteur : Selmani Mohamed

Ajoute automatiquement empreinte FPC FH52K-12(6)SA-1SH(99)
et resistances pull-down 220 Ohm.

Brochage 6 pins:
  Pin 1 = GND  | Pin 2 = DOWN | Pin 3 = DOWN
  Pin 4 = UP   | Pin 5 = UP   | Pin 6 = GND

Electrique: 5V, R~20Ohm, I=5/20=0.25A au contact
"""

import argparse, json, os, sys
from datetime import datetime

FPC_FOOTPRINT = {
    "ref": "J_FLEX",
    "value": "FH52K-12(6)SA-1SH(99)",
    "pitch": 1.0,
    "pad_w": 0.6, "pad_h": 1.5,
    "pads": [
        (1, -2.5, 0.0, "GND"),
        (2, -1.5, 0.0, "DOWN_SIG"),
        (3, -0.5, 0.0, "DOWN_SIG"),
        (4,  0.5, 0.0, "UP_SIG"),
        (5,  1.5, 0.0, "UP_SIG"),
        (6,  2.5, 0.0, "GND"),
    ],
    "mech_pads": [(-4.55, 0.0), (4.55, 0.0)],
    "trace_width": 0.3,
}

LAYER_MAP = {
    1:"F.Cu", 2:"B.Cu", 3:"F.SilkS", 4:"B.SilkS",
    5:"F.Mask", 6:"B.Mask", 7:"Edge.Cuts",
    10:"In1.Cu", 11:"In2.Cu",
    21:"F.Courtyard", 22:"B.Courtyard"
}

def to_mm(x, y):
    s = 0.0254
    return round((float(x)-4000)*s, 4), round((float(y)-3000)*s, 4)

def get_layer(lid):
    return LAYER_MAP.get(int(lid), "F.Cu")

def parse_pcb(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    tracks, vias = [], []
    for sh in d.get("shape", []):
        if not isinstance(sh, str): continue
        p = sh.split("~")
        if p[0]=="TRACK" and len(p)>=5:
            coords = [float(c) for c in p[4].split() if c]
            segs = []
            for i in range(0, len(coords)-2, 2):
                segs.append((coords[i],coords[i+1],coords[i+2],coords[i+3]))
            try:
                tracks.append({
                    "width": float(p[1]),
                    "layer": get_layer(p[2]),
                    "net": p[3], "segs": segs
                })
            except: pass
        elif p[0]=="VIA" and len(p)>=5:
            try:
                x,y = to_mm(p[1],p[2])
                vias.append({"x":x,"y":y,
                    "drill":float(p[3])*0.0254,
                    "outer":float(p[4])*0.0254})
            except: pass
    print(f"[INFO] Pistes: {len(tracks)}, Vias: {len(vias)}")
    return {"tracks": tracks, "vias": vias}

def header(ds):
    return f"""(kicad_pcb
  (version 20240108)(generator easyeda_to_kicad_cardv2)
  (general (thickness 1.6))
  (paper A4)
  (title_block
    (title "PCB Carte 2W - Flex PCB FH52K")
    (date "{ds}")(rev 2.0)
    (company "AT C229 - Selmani Mohamed")
    (comment 1 "HES -> Flex PCB FH52K-12(6)SA-1SH(99)")
    (comment 2 "5V | R~20Ohm | I=0.25A | 0/1 numerique")
    (comment 3 "Pin1=GND 2,3=DOWN 4,5=UP 6=GND"))
  (net 0 "")(net 1 "GND")(net 2 "UP_SIG")(net 3 "DOWN_SIG")(net 4 "+5V")
"""

def fpc_fp(fp, px, py):
    ps = ""
    for num, dx, dy, net in fp["pads"]:
        ps += f"""  (pad "{num}" smd rect
    (at {px+dx:.4f} {py+dy:.4f})(size {fp["pad_w"]} {fp["pad_h"]})
    (layers "F.Cu" "F.Paste" "F.Mask")(net {num} "{net}"))\n"""
    for mpx,mpy in fp["mech_pads"]:
        ps += f"""  (pad "" smd rect
    (at {px+mpx:.4f} {py+mpy:.4f})(size 1.6 1.6)
    (layers "F.Cu" "F.Paste" "F.Mask"))\n"""
    return f"""(footprint "Connector_FFC-FPC:Hirose_FH52_06-1SH_1x06-1MP_1mm"
  (layer "F.Cu")(at {px:.4f} {py:.4f})
  (descr "FH52K 6P 1mm SMD ZIF - Pin1=GND 2,3=DOWN 4,5=UP 6=GND")
  (property "Reference" "{fp["ref"]}" (at 0 -5)(layer "F.SilkS")
    (effects (font (size 1 1)(thickness 0.15))))
  (property "Value" "{fp["value"]}" (at 0 5)(layer "F.Fab")
    (effects (font (size 1 1)(thickness 0.15))))
  (fp_text "1=GND 2,3=DOWN 4,5=UP 6=GND" (at 0 3)(layer "F.Fab")
    (effects (font (size 0.8 0.8)(thickness 0.12))))
  (fp_text "5V R~20Ohm I=0.25A" (at 0 4.2)(layer "F.Fab")
    (effects (font (size 0.6 0.6)(thickness 0.1))))
  {ps})\n"""

def res_fp(ref, val, px, py, net1, net2):
    return f"""(footprint "Resistor_SMD:R_1206_3216Metric"
  (layer "F.Cu")(at {px:.4f} {py:.4f})
  (descr "220 Ohm pull-down pour capteur Flex PCB")
  (property "Reference" "{ref}" (at 0 -2)(layer "F.SilkS")
    (effects (font (size 1 1)(thickness 0.15))))
  (property "Value" "{val} Ohm" (at 0 2)(layer "F.Fab")
    (effects (font (size 1 1)(thickness 0.15))))
  (pad "1" smd rect (at -1.6 0)(size 1.6 1.8)
    (layers "F.Cu" "F.Paste" "F.Mask")(net 1 "{net1}"))
  (pad "2" smd rect (at  1.6 0)(size 1.6 1.8)
    (layers "F.Cu" "F.Paste" "F.Mask")(net 2 "{net2}"))
  (fp_line (start -1.6 -0.9)(end 1.6 -0.9)(layer "F.CrtYd")(width 0.05))
  (fp_line (start  1.6 -0.9)(end 1.6  0.9)(layer "F.CrtYd")(width 0.05))
  (fp_line (start  1.6  0.9)(end -1.6 0.9)(layer "F.CrtYd")(width 0.05))
  (fp_line (start -1.6  0.9)(end -1.6 -0.9)(layer "F.CrtYd")(width 0.05)))
"""

def tracks_str(data):
    s = ""
    for t in data["tracks"]:
        w = max(round(t["width"]*0.0254,4), 0.15)
        for x1,y1,x2,y2 in t["segs"]:
            kx1,ky1 = to_mm(x1,y1)
            kx2,ky2 = to_mm(x2,y2)
            s += f"""(segment (start {kx1} {ky1})(end {kx2} {ky2})
  (width {w})(layer "{t["layer"]}")(net 0))\n"""
    return s

def vias_str(data):
    s = ""
    for v in data["vias"]:
        s += f"""(via (at {v["x"]} {v["y"]})
  (size {v["outer"]:.4f})(drill {v["drill"]:.4f})
  (layers "F.Cu" "B.Cu")(net 0))\n"""
    return s

def generate(data, out):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    ds = datetime.now().strftime("%Y-%m-%d")
    c = header(ds)
    c += fpc_fp(FPC_FOOTPRINT, 150.0, 20.0)
    c += res_fp("R_UP",   "220", 162.0, 30.0, "UP_SIG",   "GND")
    c += res_fp("R_DOWN", "220", 162.0, 36.0, "DOWN_SIG", "GND")
    c += tracks_str(data)
    c += vias_str(data)
    c += ")\n"
    with open(out,"w",encoding="utf-8") as f: f.write(c)
    print(f"[OK] {out} ({os.path.getsize(out)} octets)")

def main():
    ap = argparse.ArgumentParser(description="EasyEDA PCB -> KiCad PCB")
    ap.add_argument("--input","-i",required=True)
    ap.add_argument("--output","-o",required=True)
    a = ap.parse_args()
    if not os.path.exists(a.input):
        print(f"[ERR] Introuvable: {a.input}",file=sys.stderr)
        sys.exit(1)
    print("EasyEDA PCB -> KiCad PCB | Carte 2W Flex FH52K")
    print("  Brochage: 1=GND 2,3=DOWN 4,5=UP 6=GND")
    print("  Electrique: 5V | R~20Ohm | I=0.25A")
    generate(parse_pcb(a.input), a.output)
    print("Etapes suivantes:")
    print("  1. KiCad: placer J_FLEX en bord de carte")
    print("  2. Router: GND(1,6)->masse, DOWN(2,3)->A2, UP(4,5)->A3")
    print("  3. Trace min: 0.3mm | DRC -> Gerber -> JLCPCB")

if __name__ == "__main__": main()
