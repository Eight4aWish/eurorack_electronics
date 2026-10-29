# Waveshare ESP32-P4-WIFI6 on the analogue board

Checked 2026-10-14 against the Rev A pin map (`docs/analogue_board_spec.md` §5, schematic
sheet 1). The board is the Waveshare **ESP32-P4-WIFI6** (SKU 32020; "-M" has headers fitted):
an ESP32-P4NRW32 with 32 MB flash, plus an ESP32-C6-MINI-1 over SDIO for Wi-Fi 6, on a 2×20
header with the Raspberry Pi Pico pinout. The ESP32-P4-Pico has the same header but no C6.

**Verdict:** it plugs in and can work, but it is not a drop-in Pico 2. It needs:

- one line of firmware before anything else;
- a footprint position that allows for its extra length;
- acceptance that, in this board, its USB-C is a serial port only and its Wi-Fi will be weak.

It is not a Rev A target (§5 decides Pico 2 and Teensy 4.1). The board change it prompted,
pull-ups on CS_ADC, CS_DAC and CS_POT, helps every module.

## Hard problems

1. **Pins 21, 22 and 24 are on a programmable supply.** They are GPIO48, 47 and 46, which carry
   SPIA_MISO, CS_ADC and SPIA_SCK. All three sit in the I/O bank VDD_IO_5, which also holds the
   microSD pins (GPIO39-48; Espressif hardware design guide, pin table). On this board that bank
   is powered from the P4's internal LDO channel 4 (Waveshare schematic, ESP_LDO_VO4).
   - **The two vendors disagree on its power-up value.** Espressif says it outputs 0 until
     software sets it. Waveshare says it defaults to 1.8 V.
   - **ESP-IDF leaves it alone.** It reserves only LDO channels 1 (flash) and 2 (PSRAM).
   - **What goes wrong:**
     - Until firmware acts, the converter bus is dead.
     - At 1.8 V, the ADS8688's 3.3 V output on GPIO48 exceeds the pin's absolute maximum of
       VDD + 0.3 V.
     - The SD driver can switch the bank to 1.8 V for UHS-I.
   - **Fix, in firmware:** first thing, call `esp_ldo_acquire_channel` for channel 4 at
     3300 mV (pass-through), and never enable UHS-I on the card.
   - **Fix, on the board (done):** CS_ADC, CS_DAC and CS_POT have 10 kΩ pull-ups, so no
     converter is selected while a module boots.
   - **Why not move the nets:** that would break the Pico 2 mapping, because GP16-19 are the
     RP2350's SPI0 pins.
2. **Length.** The board is 71 × 21 mm against the Pico's 51 × 21 mm. The extra length is
   3.2 mm at the USB end and 16.9 mm at the far (antenna) end.
   - With the USB end toward the board centre (§4.3), the antenna end reaches about 17 mm past
     where a Pico ends. Placed the way a Pico is placed, it would overhang the top edge into the
     rail.
   - **To take it:** at checkpoint 2, leave about 18 mm free beyond the Pico footprint's far end.
   - **Knock-on (estimate, to check on the 1:1 printout):** with its far end at the top edge,
     its USB plug lands about 72 mm down, and the plug keep-out reaches about 102 mm. That is
     on top of the bottom-centre power header, which is [decided]. The Teensy's keep-out ends
     around 92 mm and clears it. Supporting the P4 means moving the header, a very short
     right-angle cable, or no USB for the P4 in the rack (its USB-C is only a serial bridge
     anyway).

## Soft problems

- **Pins 16 and 17 (GPIO8 and GPIO7) are the board's own I2C bus.** They have 2.2 kΩ pull-ups
  and 22 pF, and go to the on-board ES8311 codec and the display and camera connectors.
  - SPIB_MISO and CS_595 still work.
  - A false I2C address match on the ES8311 is unlikely but not ruled out.
- **Pins 19 and 20 (GPIO24 and GPIO25) are the USB-JTAG pads.** GPIO25 (PROBE) has the USB
  pull-up enabled until firmware sets the pin up as a GPIO.
- **Power.**
  - Pin 39 is a real 5 V input, ORed with USB through a P-FET ideal diode, so USB plugged in at
    the same time is safe.
  - Its MP1658 buck needs at least 4.5 V, and MOD_5V is about 4.6 V after the Schottky: thin.
  - The board draws up to an estimated 0.45-0.7 A; the C6 alone peaks at 382 mA on transmit.
  - Raising +5VD to about 5.2 V, or using a lower-drop diode, would restore margin.
- **USB-C is a UART bridge (CH343P)**, not native USB. USB-MIDI needs the board's separate
  4-pin USB-OTG connector.
- **Wi-Fi.** The C6's PCB antenna sits at the far end. On headers it would be about 11-13 mm
  over our ground plane, inside a metal case. Espressif asks for at least 15 mm clearance, so
  expect it to be largely unusable in the rack.
- **Unpowered pins.** The P4 is not 5 V-tolerant or protected when unpowered, unlike the
  RP2350, so our 3.3 V pull-ups back-feed it slightly during power-up.
- **Toolchain.** Use ESP-IDF; Arduino support is limited. Wi-Fi needs ESP-Hosted running on the
  C6. Check the chip revision: ESP-IDF 5.5.3 and later need
  `CONFIG_ESP32P4_SELECTS_REV_LESS_V3=y` for v1.x silicon. None of the RP2350 firmware ports.

## Fine

- No boot-strap pins (GPIO34-38) reach the header, so our power-up states can't upset boot.
- Every other header GPIO is on a 3.3 V bank.
- Two SPI masters, I2S with a 12.288 MHz MCLK from the audio PLL, I2C, UART and RMT (for the
  WS2812s) all route through the GPIO matrix to our pins. 17 MHz SPI is fine.
- Pin 30 is the chip reset (as RUN is on the Pico). Pin 37 is the regulator enable. Pin 35 is
  GPIO20, which we leave unconnected.
- The microSD slot uses GPIO39-45; none of them reaches the header. The card goes in at the USB
  end and is meant to stay in. Underside clearance is about 5 mm.

## Pin table

Board signal and bank are from the Waveshare schematic, p.1, interface block; banks are from
the ESP32-P4 datasheet v0.7, Table 2-1.

| Pico pin | P4 board | Bank | Our net | Verdict |
|---|---|---|---|---|
| 1, 2 | GPIO52, 51 | VDD_IO_6 (3V3) | SPARE1, SPARE2 | OK |
| 4, 5 | GPIO31, 30 | VDD_IO_4 (3V3) | SDA, SCL | OK |
| 6, 7 | GPIO29, 28 | VDD_IO_4 | EXP_INT, LED_DATA | OK |
| 9, 10 | GPIO50, 49 | VDD_IO_6 | GATE_IN1, 2 | OK |
| 11, 12 | GPIO5, 4 | VDD_LP (3V3) | GATE_IN3, 4 | OK |
| 14, 15 | GPIO3, 2 | VDD_LP | SPIB_SCK, MOSI | OK |
| 16 | GPIO8, board I2C SCL | VDD_LP | SPIB_MISO | soft |
| 17 | GPIO7, board I2C SDA | VDD_LP | CS_595 | soft |
| 19, 20 | GPIO24, 25 (USB-JTAG) | VDD_IO_4 | CS_POT, PROBE | soft |
| 21, 22, 24 | **GPIO48, 47, 46** | **VDD_IO_5 = LDO channel 4** | SPIA_MISO, CS_ADC, SPIA_SCK | **hard** |
| 25, 26 | GPIO33, 32 | VDD_IO_4 | SPIA_MOSI, CS_DAC | OK |
| 27, 29 | GPIO27, 26 | VDD_IO_4 | MCLK, I2S_DIN | OK |
| 31, 32, 34 | GPIO23, 22, 21 | VDD_IO_0 (3V3) | BCK, LRCK, I2S_DOUT | OK |
| 30 | chip enable (reset) | — | RUN | OK |
| 35 | GPIO20 | VDD_IO_0 | unconnected | OK |
| 39 | VCC_5V (buck in, ORed with USB) | — | MOD_5V | OK, thin margin |
| 36, 37, 40 | 3V3 out, regulator enable, USB VBUS | — | unconnected | OK |

## Bench tests

David's board, on its own (not on the analogue board), 2026-10-27 to 29. It is chip revision v3.2
with 32 MB flash. The firmware is ESP-IDF 5.5.4, outside this repo.

- **Camera.** A Waveshare RPi Camera (B) rev 2.0 (OV5647) on CAMERA (J1). Both MIPI sockets are
  22-pin 0.5 mm, Raspberry Pi 5 style. The sensor answered on the board's I2C (GPIO8 SCL, GPIO7
  SDA), and Waveshare's `17_simple_video_server` streamed it over Wi-Fi.
- **HDMI.** DISPLAY (J2) feeds Olimex's MIPI-HDMI (LT8912B) through a Raspberry Pi display adapter
  cable (22 to 15 pin; the camera version is wired differently). The board's I2C finds the bridge
  at 0x48 to 0x4A and the sink's EDID at 0x50, through Olimex's DDC. Standard 1280×720p60 (CEA
  VIC 4) locked first time on a USB capture card. Its 74.25 MHz pixel clock comes from the APLL,
  with the DSI host's own colour bars.
- **Camera to HDMI, live.** The sensor's 1280×960 mode is cropped to 1280×720 in the PPA and shown
  at about 22 frames/s. Lines sometimes jump sideways. The likely cause is the display DMA running
  short of PSRAM bandwidth, with camera, crop and display all in PSRAM. The colour bars, which use
  no PSRAM, were steady. Not chased; the real target is 720×720.

What it means for the module:

- **Pins 16 and 17 (GPIO8 and GPIO7) carry the camera's and the bridge's I2C.** That confirms
  reserving them on Rev B.
- **The APLL can't do both jobs.** The planned I2S MCLK (12.288 MHz) and an exact video pixel clock
  both want it. Firmware has to choose: a video timing from the fixed PLLs (Espressif's 80 MHz
  1280×720 comes from 240 MHz ÷ 3), or the MCLK from elsewhere. Open.
- **The display it is for is the TLQ-SCREEN** (round 720×720, DVI, Tiliqua's 720×720p60 timing).
  It is awaited; that mode is the next step.

## Sources

- Waveshare product page and docs: https://www.waveshare.com/esp32-p4-wifi6.htm,
  https://docs.waveshare.com/ESP32-P4-WIFI6
- Schematic: https://files.waveshare.com/wiki/ESP32-P4-WIFI6/ESP32-P4-WIFI6-datasheet.pdf
- Drawings and STEP model: https://files.waveshare.com/wiki/ESP32-P4-WIFI6/ESP32-P4-WIFI6.zip
- ESP32-P4 datasheet v0.7: https://documentation.espressif.com/esp32-p4_datasheet_en.pdf
- ESP32-P4 hardware design guidelines: https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32p4/schematic-checklist-esp32p4.html
- ESP-IDF LDO driver, SD host, SPI, I2S and GPIO documentation for the ESP32-P4
- ESP32-C6-MINI-1 datasheet; MP1658 datasheet; Waveshare ESP32-P4-Module wiki (the "default
  1.8 V" claim)
- Not verified: the LDO's actual reset value (the vendors disagree), I2S jitter, the board's
  measured current, the height of its underside parts (from the drawing), and the MCP3208's
  output-low level against the 2.2 kΩ pull-up on pin 16.
