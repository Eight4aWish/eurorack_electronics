"""Parts catalogue: KiCad symbol, footprint, LCSC number and datasheet for every part on the board.

LCSC numbers were checked against the JLCPCB parts API on 2026-10-14. "Basic" parts carry no
per-type assembly fee in JLCPCB Economic PCBA; "Extended" parts cost $3.07 a type per order.
"""

LIB = "analogue_board"

ICS = {
    "PCM3060": dict(lib="Audio:PCM3060", value="PCM3060PWR", fp="Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm",
                    lcsc="C2651841", mpn="PCM3060PWR", ds="https://www.ti.com/lit/ds/symlink/pcm3060.pdf", jlc="Extended"),
    "ADS8688": dict(lib="Analog_ADC:ADS8688", value="ADS8688IDBTR", fp="Package_SO:TSSOP-38_4.4x9.7mm_P0.5mm",
                    lcsc="C527390", mpn="ADS8688IDBTR", ds="https://www.ti.com/lit/ds/symlink/ads8688.pdf", jlc="Extended"),
    "DAC8568": dict(lib=f"{LIB}:DAC8568xPW", value="DAC8568IAPWR", fp="Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
                    lcsc="C486051", mpn="DAC8568IAPWR", ds="https://www.ti.com/lit/ds/symlink/dac8568.pdf", jlc="Extended"),
    "MCP3208": dict(lib="Analog_ADC:MCP3208", value="MCP3208-CI/SL", fp="Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
                    lcsc="C16939", mpn="MCP3208-CI/SL", ds="https://ww1.microchip.com/downloads/en/DeviceDoc/21298e.pdf", jlc="Extended"),
    "DG412": dict(lib="Analog_Switch:DG412xUE", value="DG412DQ-T1-E3", fp="Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
                  lcsc="C2651920", mpn="DG412DQ-T1-E3", ds="https://www.vishay.com/docs/61564/dg411.pdf", jlc="Extended"),
    "TL074H": dict(lib="Amplifier_Operational:TL074", value="TL074HIDR", fp="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
                   lcsc="C2878713", mpn="TL074HIDR", ds="https://www.ti.com/lit/ds/symlink/tl074h.pdf", jlc="Extended"),
    "LM393": dict(lib="Comparator:LM393", value="LM393DR2G", fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
                  lcsc="C7955", mpn="LM393DR2G", ds="https://www.onsemi.com/pdf/datasheet/lm393-d.pdf", jlc="Basic"),
    "74HCT595": dict(lib="74xx:74HCT595", value="74HCT595D", fp="Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
                     lcsc="C282339", mpn="74HCT595D,118", ds="https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf", jlc="Extended"),
    "TCA9555": dict(lib="Interface_Expansion:TCA9555PWR", value="TCA9555PWR", fp="Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm",
                    lcsc="C465732", mpn="TCA9555PWR", ds="https://www.ti.com/lit/ds/symlink/tca9555.pdf", jlc="Extended"),
    "M24C64": dict(lib="Memory_EEPROM:M24C01-RMN", value="M24C64-RMN6TP", fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
                   lcsc="C79988", mpn="M24C64-RMN6TP", ds="https://www.st.com/resource/en/datasheet/m24c64-r.pdf", jlc="Extended (Preferred)"),
    "AHCT1G125": dict(lib="74xGxx:74AHCT1G125", value="SN74AHCT1G125DBVR", fp="Package_TO_SOT_SMD:SOT-23-5",
                      lcsc="C7484", mpn="SN74AHCT1G125DBVR", ds="https://www.ti.com/lit/ds/symlink/sn74ahct1g125.pdf", jlc="Extended"),
    "XC6206": dict(lib="Regulator_Linear:XC6206PxxxMR", value="XC6206P332MR-G", fp="Package_TO_SOT_SMD:SOT-23",
                   lcsc="C5446", mpn="XC6206P332MR-G", ds="https://www.torexsemi.com/file/xc6206/XC6206.pdf", jlc="Basic"),
    "L78M05": dict(lib="Regulator_Linear:LM78M05_TO252", value="L78M05ABDT-TR", fp="Package_TO_SOT_SMD:TO-252-2",
                   lcsc="C58069", mpn="L78M05ABDT-TR", ds="https://www.st.com/resource/en/datasheet/l78m.pdf", jlc="Basic"),
    "TPS54308": dict(lib="Regulator_Switching:TPS54202DDC", value="TPS54308DDCR", fp="Package_TO_SOT_SMD:SOT-23-6",
                     lcsc="C168839", mpn="TPS54308DDCR", ds="https://www.ti.com/lit/ds/symlink/tps54308.pdf", jlc="Extended",
                     note="Forced-PWM (FCCM). Pin-compatible fallback with the same values: TPS54202DDCR C191884 (pulse-skips at light load)"),
    "SS14": dict(lib="Diode:SS14", value="SS14", fp="Diode_SMD:D_SMA", lcsc="C2480", mpn="SS14",
                 ds="https://www.lcsc.com/datasheet/lcsc_datasheet_2407101109_MDD-Microdiode-Semiconductor-SS14_C2480.pdf", jlc="Basic", prefix="D"),
    # 3 A in the same SMA footprint: the +12 V entry can carry ~0.75 A with an ESP32-P4 and a lit LED chain
    "SS34": dict(lib="Diode:SS34", value="SS34", fp="Diode_SMD:D_SMA", lcsc="C8678", mpn="SS34",
                 ds="https://www.lcsc.com/datasheet/lcsc_datasheet_2407101107_MDD-Microdiode-Semiconductor-SS34_C8678.pdf", jlc="Basic", prefix="D"),
    "BAT54S": dict(lib="Diode:BAT54S", value="BAT54S", fp="Package_TO_SOT_SMD:SOT-23", lcsc="C408389", mpn="BAT54S",
                   ds="https://www.lcsc.com/datasheet/lcsc_datasheet_2407101108_MDD-Microdiode-Semiconductor-BAT54S_C408389.pdf", jlc="Extended", prefix="D"),
    # BAV99 uses the BAT54S symbol: both datasheets give 1 = anode, 2 = cathode, 3 = common (series pair)
    "BAV99": dict(lib="Diode:BAT54S", value="BAV99", fp="Package_TO_SOT_SMD:SOT-23", lcsc="C2500", mpn="BAV99,215",
                  ds="https://assets.nexperia.com/documents/data-sheet/BAV99_SER.pdf", jlc="Basic", prefix="D"),
    "FERRITE": dict(lib="Device:FerriteBead_Small", value="BLM18PG121SN1D", fp="Inductor_SMD:L_0603_1608Metric",
                    lcsc="C14709", mpn="BLM18PG121SN1D", ds="", jlc="Basic", prefix="FB"),
    "L_BUCK": dict(lib="Device:L_Small", value="15uH", fp="Inductor_SMD:L_Sunlord_SWPA5040S",
                   lcsc="C44888", mpn="SWPA5040S150MT", ds="", jlc="Extended", prefix="L"),
    "EURO_PWR": dict(lib="Connector_Generic:Conn_02x05_Odd_Even", value="Eurorack power 2x5 shrouded",
                     fp="Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical", lcsc="", mpn="2x5 2.54 mm shrouded box header",
                     ds="", jlc="hand-soldered", prefix="J"),
    "QWIIC": dict(lib="Connector_Generic_MountingPin:Conn_01x04_MountingPin", value="Qwiic SM04B-SRSS-TB",
                  fp="Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal", lcsc="C160404",
                  mpn="SM04B-SRSS-TB(LF)(SN)", ds="", jlc="Extended", prefix="J"),
    "PICO2": dict(lib=f"{LIB}:RaspberryPi_Pico2", value="Raspberry Pi Pico 2", fp=f"{LIB}:Pico2_Socket",
                  lcsc="", mpn="SC1631 on 2x20 female headers", ds="https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf",
                  jlc="hand-soldered", prefix="A"),
    "TEENSY41": dict(lib=f"{LIB}:Teensy41", value="Teensy 4.1", fp=f"{LIB}:Teensy41_Socket", lcsc="",
                     mpn="PJRC Teensy 4.1 on 2x24 female headers", ds="https://www.pjrc.com/store/teensy41.html",
                     jlc="hand-soldered", prefix="A"),
    "EDGE_L": dict(lib=f"{LIB}:EdgeStrip_40", value="Edge strip, left", fp=f"{LIB}:EdgeStrip_40_Left", lcsc="",
                   mpn="", ds="docs/n8synth_platform.md", jlc="bare holes", prefix="J"),
    "EDGE_R": dict(lib=f"{LIB}:EdgeStrip_40", value="Edge strip, right", fp=f"{LIB}:EdgeStrip_40_Right", lcsc="",
                   mpn="", ds="docs/n8synth_platform.md", jlc="bare holes", prefix="J"),
    "H11L1": dict(lib="Isolator:H11L1", value="H11L1SR2M", fp="Package_DIP:SMDIP-6_W7.62mm", lcsc="C20082",
                  mpn="H11L1SR2M", ds="https://www.onsemi.com/pdf/datasheet/h11l1m-d.pdf", jlc="Extended"),
    "AO3401A": dict(lib="Transistor_FET:AO3401A", value="AO3401A", fp="Package_TO_SOT_SMD:SOT-23", lcsc="C15127",
                    mpn="AO3401A", ds="https://www.aosmd.com/res/datasheets/AO3401A.pdf", jlc="Basic", prefix="Q"),
    "1N4148WS": dict(lib="Diode:1N4148WS", value="1N4148WS", fp="Diode_SMD:D_SOD-323", lcsc="C2128", mpn="1N4148WS",
                     ds="", jlc="Basic", prefix="D"),
    "TVS15": dict(lib="Device:D_TVS", value="PESD15VL1BA", fp="Diode_SMD:D_SOD-323", lcsc="C85378",
                  mpn="PESD15VL1BA,115", ds="https://assets.nexperia.com/documents/data-sheet/PESD15VL1BA.pdf",
                  jlc="Extended", prefix="D"),
    "SJ_OPEN": dict(lib="Jumper:SolderJumper_2_Open", value="SolderJumper open",
                    fp="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm", lcsc="", mpn="", ds="",
                    jlc="bare pad", prefix="JP"),
    "TP": dict(lib="Connector:TestPoint", value="TP", fp="TestPoint:TestPoint_Pad_D1.0mm", lcsc="", mpn="",
               ds="", jlc="bare pad", prefix="TP"),
    "FID": dict(lib="Mechanical:Fiducial", value="Fiducial", fp="Fiducial:Fiducial_1mm_Mask2mm", lcsc="", mpn="",
                ds="", jlc="bare pad", prefix="FID"),
}

RES = {  # (value, size) -> LCSC, all JLC Basic, 1 %
    ("0R", "0402"): "C17168", ("0R", "0603"): "C21189", ("0R", "0805"): "C17477",
    ("10R", "0402"): "C25077", ("33R", "0402"): "C25105", ("100R", "0402"): "C25076", ("330R", "0402"): "C25104",
    ("1k", "0402"): "C11702", ("1.5k", "0402"): "C25867", ("2k", "0402"): "C4109", ("2.2k", "0402"): "C25879",
    ("3.3k", "0402"): "C25890", ("4.7k", "0402"): "C25900", ("5.1k", "0402"): "C25905", ("10k", "0402"): "C25744",
    ("12k", "0402"): "C25752", ("15k", "0402"): "C25756", ("20k", "0402"): "C25765", ("22k", "0402"): "C25768",
    ("33k", "0402"): "C25779", ("47k", "0402"): "C25792", ("51k", "0402"): "C25794", ("100k", "0402"): "C25741",
    ("200k", "0402"): "C25764", ("1M", "0402"): "C26083",
    ("13k", "0603"): "C22797", ("30k", "0603"): "C22984", ("220k", "0603"): "C22961",
    ("680R", "0603"): "C23228", ("5.1R", "0603"): "C25197", ("510k", "0603"): "C23192", ("75k", "0603"): "C23242",
    ("100R", "0805"): "C17408", ("220R", "0805"): "C17557", ("1k", "0805"): "C17513",
    ("100R", "1206"): "C17901", ("1k", "1206"): "C4410",
}

CAP = {  # (value, size) -> (LCSC, rating, dielectric), all JLC Basic
    ("100n", "0402"): ("C1525", "16V", "X7R"), ("10n", "0402"): ("C15195", "50V", "X7R"),
    ("1n", "0402"): ("C1523", "50V", "X7R"), ("1u", "0402"): ("C52923", "25V", "X5R"),
    ("100p", "0402"): ("C1546", "50V", "C0G"), ("47p", "0402"): ("C1567", "50V", "C0G"),
    ("22p", "0402"): ("C1555", "50V", "C0G"),
    ("100n", "0603"): ("C14663", "50V", "X7R"), ("1u", "0603"): ("C15849", "50V", "X5R"),
    ("4.7u", "0603"): ("C19666", "16V", "X5R"),
    ("1u", "0805"): ("C28323", "50V", "X7R"), ("10u", "0805"): ("C15850", "25V", "X5R"),
    ("22u", "0805"): ("C45783", "25V", "X5R"),
    ("10u", "1206"): ("C13585", "50V", "X5R"), ("22u", "1206"): ("C12891", "25V", "X5R"),
    ("47u", "1206"): ("C96123", "10V", "X5R"),
    # Extended or not fitted: (LCSC, rating, dielectric, JLC library)
    ("1n C0G", "0603"): ("C106246", "50V", "C0G", "Extended"),
    ("470p", "0402"): ("", "50V", "C0G", "not fitted"),
}

FP_R = {"0402": "Resistor_SMD:R_0402_1005Metric", "0603": "Resistor_SMD:R_0603_1608Metric", "0805": "Resistor_SMD:R_0805_2012Metric",
        "1206": "Resistor_SMD:R_1206_3216Metric"}
FP_C = {"0402": "Capacitor_SMD:C_0402_1005Metric", "0603": "Capacitor_SMD:C_0603_1608Metric",
        "0805": "Capacitor_SMD:C_0805_2012Metric", "1206": "Capacitor_SMD:C_1206_3216Metric"}


def holes_part(n):
    return dict(lib=f"Connector_Generic:Conn_01x{n:02d}", value=f"holes 1x{n}",
                fp=f"Connector_PinHeader_2.54mm:PinHeader_1x{n:02d}_P2.54mm_Vertical", lcsc="", mpn="",
                ds="", jlc="bare holes", prefix="J")
