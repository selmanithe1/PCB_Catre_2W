import json
import copy
import math

# ─────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────
with open("SCH_CardV2 copy_2025-09-15.json", "r", encoding="utf-8") as f:
    data = json.load(f)

shapes = data["schematics"][0]["dataStr"]["shape"]

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def remove_shapes(shapes, keywords):
    """Remove shapes that contain ANY of the given keywords."""
    return [s for s in shapes if not any(kw in s for kw in keywords)]

# ─────────────────────────────────────────────
# 1. REMOVE old HES circuit
#    - LM741 (U1)
#    - R1 (10kΩ pullup for HES)       -> "R1~" label in LIB string
#    - R2 (4.7kΩ) and R3 (180Ω LED)  -> keep R2/R3, they go to the motor logic
#    - HES net labels (HES+, HES-)
#    - Wires linked to LM741 block
# ─────────────────────────────────────────────
keywords_to_remove = [
    "LM741CN",          # U1 component
    "^^HES+~",          # HES+ net label
    "^^HES-~",          # HES- net label
    "^^HESPin~",        # HESPin net label
    "flag_gge1396",     # HES+ flag
    "flag_gge1399",     # HES- flag
    "flag_gge1321",     # HESPin flag (to ICS)
    "flag_gge1384",     # HESPin flag (to rest)
    "ARG06FTC1002",     # R1 10kΩ
]

shapes = remove_shapes(shapes, keywords_to_remove)

# ─────────────────────────────────────────────
# 2. REMOVE B3 / B4 button net labels
#    (we keep B1=UP, B2=DOWN)
# ─────────────────────────────────────────────
keywords_b34 = [
    "^^B3~",
    "^^B4~",
    "flag_gge1489",
    "flag_gge1492",
]
shapes = remove_shapes(shapes, keywords_b34)

# ─────────────────────────────────────────────
# 3. REPLACE 6-pin button header (H4) with 4-pin
#    by relabelling the component comment
# ─────────────────────────────────────────────
new_shapes = []
for s in shapes:
    if "HDR-M-2.54_1X6" in s and "Buttons" in s:
        # Replace footprint and pin count label in the LIB string
        s = s.replace("HDR-M-2.54_1X6", "HDR-M-2.54_1X4")
        s = s.replace("`Buttons`", "`Buttons (UP/DWN)`")
        # Remove pin 5 and pin 6 definitions from the string
        # Pin5 and Pin6 are the B3/B4 pins - strip them from #@$ segments
        parts = s.split("#@$")
        parts = [p for p in parts if not (("show~1~5~" in p) or ("show~1~6~" in p))]
        s = "#@$".join(parts)
    new_shapes.append(s)
shapes = new_shapes

# ─────────────────────────────────────────────
# 4. ADD Flex Sensor Connector (generic 6-pin HDR)
#    Placed at position (805, -170) - empty area on schematic
#    Net names: FLEX_GND1/2 -> GND, FLEX_SIG -> A1
# ─────────────────────────────────────────────
flex_connector = (
    'LIB~805~-170~package`HDR-M-2.54_1X6`Contributor`LCEDA_Lib`spicePre`J`spiceSymbolName`HDR-M-2.54_1x6`'
    '~~0~gge_flex_conn_001~282f7786cb6144d097ae00194c3e3fb3~f5b1d9403e49471cab43bc5a1bec336f~0~gge_flex_conn_u~'
    'yes~yes~~1586865170~'
    '#@$T~N~818~-168~0~#000080~Arial~4pt~~~~comment~Flex Sensor (FH52K/6P)~1~start~gge_flex_t1~0~pinpart'
    '#@$T~P~837~-168~0~#000080~Arial~4pt~~~~comment~J_FLEX~1~start~gge_flex_t2~0~pinpart'
    '#@$R~795~-205~2~2~20~70~#880000~1~0~none~gge_flex_rect~0~'
    '#@$P~show~0~1~785~-195~180~gge_flex_p1~0^^785~-195^^M 785 -195 h 10~#000000^^1~799~-193~0~1~start~~~#000000^^0~795~-196~0~1~end~~~#000000^^0~792~-195^^0~M 795 -192 L 798 -195 L 795 -198'
    '#@$P~show~0~2~785~-185~180~gge_flex_p2~0^^785~-185^^M 785 -185 h 10~#000000^^1~799~-183~0~2~start~~~#000000^^0~795~-186~0~2~end~~~#000000^^0~792~-185^^0~M 795 -182 L 798 -185 L 795 -188'
    '#@$P~show~0~3~785~-175~180~gge_flex_p3~0^^785~-175^^M 785 -175 h 10~#000000^^1~799~-173~0~3~start~~~#000000^^0~795~-176~0~3~end~~~#000000^^0~792~-175^^0~M 795 -172 L 798 -175 L 795 -178'
    '#@$P~show~0~4~785~-165~180~gge_flex_p4~0^^785~-165^^M 785 -165 h 10~#000000^^1~799~-163~0~4~start~~~#000000^^0~795~-166~0~4~end~~~#000000^^0~792~-165^^0~M 795 -162 L 798 -165 L 795 -168'
    '#@$P~show~0~5~785~-155~180~gge_flex_p5~0^^785~-155^^M 785 -155 h 10~#000000^^1~799~-153~0~5~start~~~#000000^^0~795~-156~0~5~end~~~#000000^^0~792~-155^^0~M 795 -152 L 798 -155 L 795 -158'
    '#@$P~show~0~6~785~-145~180~gge_flex_p6~0^^785~-145^^M 785 -145 h 10~#000000^^1~799~-143~0~6~start~~~#000000^^0~795~-146~0~6~end~~~#000000^^0~792~-145^^0~M 795 -142 L 798 -145 L 795 -148'
)

# ─────────────────────────────────────────────
# 5. ADD R_Flex 220Ω resistor (at ~725, -175)
# ─────────────────────────────────────────────
r_flex = (
    'LIB~725~-175~package`R1206`nameAlias`Value`Contributor`LCSC`Supplier`LCSC`'
    'Supplier Part`C137262`spicePre`R`spiceSymbolName`RC1206`~~0~gge_rflex_001~'
    '8e9b1be4bcb6420dbd1d09bf04b02792~888000a133834d72b294e225701662e8~0~gge_rflex_u~yes~yes~~1543050362~'
    '#@$T~N~719~-183~0~#000080~Arial~4pt~~~~comment~220Ω~1~start~gge_rflex_t1~0~pinpart'
    '#@$T~P~721~-189~0~#000080~Arial~4pt~~~~comment~R_Flex~1~start~gge_rflex_t2~0~pinpart'
    '#@$R~715~-179~~~20~8~#A00000~1~0~none~gge_rflex_rect~0~'
    '#@$P~show~0~2~745~-175~0~gge_rflex_p2~0^^745~-175^^M 735 -175 h 10~#800^^0~731~-175~0~2~end~~~#800^^0~739~-179~0~2~start~~~#800^^0~757~-175^^0~M 754 -178 L 751 -175 L 754 -172'
    '#@$P~show~0~1~705~-175~180~gge_rflex_p1~0^^705~-175^^M 715 -175 h -10~#800^^0~719~-175~0~1~start~~~#800^^0~711~-179~0~1~end~~~#800^^0~692~-175^^0~M 695 -172 L 698 -175 L 695 -178'
)

# ─────────────────────────────────────────────
# 6. ADD Net Labels
# ─────────────────────────────────────────────

# +5V power flag at R_Flex pin 1 (left side, at X=692, Y=-175)
vcc_rflex = (
    'F~part_netLabel_VCC~692~-175~90~gge_vcc_rflex~~0^^692~-175^^+5Vd~#000000~652~-170.93~0~start~1~'
    'Times New Roman~9pt~flag_gge_vcc_rflex_f^^PL~682 -175 692 -175~#000000~1~0~transparent~gge_vcc_rflex_p1~0'
    '^^PL~682 -170 682 -180~#000000~1~0~transparent~gge_vcc_rflex_p2~0'
)

# GND for connector pins 1&2
gnd_flex1 = (
    'F~part_netLabel_gnD~775~-195~270~gge_gnd_flex1~~0^^775~-195^^GND~#000000~732~-190.93~0~start~1~'
    'Times New Roman~9pt~flag_gge_gnd_f1^^PL~765 -195 775 -195~#000000~1~0~transparent~gge_gnd_f1_p1~0'
    '^^PL~765 -204 765 -186~#000000~1~0~transparent~gge_gnd_f1_p2~0'
    '^^PL~763 -201 763 -189~#000000~1~0~transparent~gge_gnd_f1_p3~0'
)
gnd_flex2 = (
    'F~part_netLabel_gnD~775~-185~270~gge_gnd_flex2~~0^^775~-185^^GND~#000000~732~-180.93~0~start~1~'
    'Times New Roman~9pt~flag_gge_gnd_f2^^PL~765 -185 775 -185~#000000~1~0~transparent~gge_gnd_f2_p1~0'
    '^^PL~765 -194 765 -176~#000000~1~0~transparent~gge_gnd_f2_p2~0'
    '^^PL~763 -191 763 -179~#000000~1~0~transparent~gge_gnd_f2_p3~0'
)

# Net A1 label at junction R_Flex & Flex connector pin3
a1_label = (
    'F~part_netLabel_netPort~757~-175~0~gge_a1_label~~0^^757~-175^^FlexA1~#0000FF~709~-171.45~0~~1~'
    'Times New Roman~8pt~flag_gge_a1^^PL~757 -175 762 -180 777 -180 777 -170 762 -170 757 -175~'
    '#0000FF~1~0~transparent~gge_a1_lp~0'
)
flex_p3_label = (
    'F~part_netLabel_netPort~775~-175~0~gge_flex_p3_net~~0^^775~-175^^FlexA1~#0000FF~727~-171.29~0~~1~'
    'Times New Roman~8pt~flag_gge_flexA1^^PL~775 -175 770 -170 755 -170 755 -180 770 -180 775 -175~'
    '#0000FF~1~0~transparent~gge_flex_p3_lp~0'
)
flex_p4_label = (
    'F~part_netLabel_netPort~775~-165~0~gge_flex_p4_net~~0^^775~-165^^FlexA1~#0000FF~727~-161.29~0~~1~'
    'Times New Roman~8pt~flag_gge_flexA1b^^PL~775 -165 770 -160 755 -160 755 -170 770 -170 775 -165~'
    '#0000FF~1~0~transparent~gge_flex_p4_lp~0'
)
# Pins 5 & 6 -> "NC" (no connect)
nc_flex5 = 'F~part_netLabel_netPort~775~-155~0~gge_nc_f5~~0^^775~-155^^NC_FLEX5~#0000FF~727~-151.29~0~~1~Times New Roman~8pt~flag_gge_nc5^^PL~775 -155 770 -150 755 -150 755 -160 770 -160 775 -155~#0000FF~1~0~transparent~gge_nc_f5_lp~0'
nc_flex6 = 'F~part_netLabel_netPort~775~-145~0~gge_nc_f6~~0^^775~-145^^NC_FLEX6~#0000FF~727~-141.29~0~~1~Times New Roman~8pt~flag_gge_nc6^^PL~775 -145 770 -140 755 -140 755 -150 770 -150 775 -145~#0000FF~1~0~transparent~gge_nc_f6_lp~0'

# Arduino side: FlexA1 net label (links to A1 pin on the ICS socket SK1)
flex_arduino = (
    'F~part_netLabel_netPort~870~-685~0~gge_flex_ard~~0^^870~-685^^FlexA1~#0000FF~813~-681.25~0~~1~'
    'Times New Roman~8pt~flag_gge_flex_ard^^PL~870 -685 865 -680 850 -680 850 -690 865 -690 870 -685~'
    '#0000FF~1~0~transparent~gge_flex_ard_lp~0'
)

# ─────────────────────────────────────────────
# 7. Bounding box rect for new section
# ─────────────────────────────────────────────
section_box = 'R~675~-215~~~165~80~#000000~1~0~none~gge_flex_box~0~'
section_title = 'T~L~680~-220~0~#0000FF~~8pt~~~~comment~Flex Sensor Interface~1~start~gge_flex_title~0~pinpart'

# ─────────────────────────────────────────────
# 8. ASSEMBLE
# ─────────────────────────────────────────────
shapes.append(flex_connector)
shapes.append(r_flex)
shapes.append(vcc_rflex)
shapes.append(gnd_flex1)
shapes.append(gnd_flex2)
shapes.append(a1_label)
shapes.append(flex_p3_label)
shapes.append(flex_p4_label)
shapes.append(nc_flex5)
shapes.append(nc_flex6)
shapes.append(flex_arduino)
shapes.append(section_box)
shapes.append(section_title)

# ─────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────
data["schematics"][0]["dataStr"]["shape"] = shapes
data["title"] = "CardV2_Flex_Sensor"

with open("SCH_CardV2 copy_2025-09-15.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done! Schematic modified successfully.")
print(f"Total shapes: {len(shapes)}")
