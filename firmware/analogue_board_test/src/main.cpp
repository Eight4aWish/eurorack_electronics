// Analogue board Rev A (Teensy 4.1, teensy_core_midi): the stage 6 bring-up test of
// docs/analogue_board_bringup.md. One serial command per block; each prints what it read and a
// pass mark. Pins, nets and part values are from the board netlist
// (hardware/analogue_board/teensy_core_midi/output/analogue_board_teensy_core_midi.net) and the
// pin map in tools/analogue_board/design.py.
//
// Nothing on the board is driven until its block is asked for. At boot only I2C runs, and the
// M24C64 must answer before any other bus starts (spec §15, firmware requirement 1).

#include <Arduino.h>
#include <Audio.h>
#include <QuadEncoder.h>
#include <SPI.h>
#include <WS2812Serial.h>
#include <Wire.h>

// ---- pins (Teensy numbering)
constexpr uint8_t PIN_CS_ADC = 10, PIN_CS_DAC = 9;                      // SPI-A: SCK 13, MOSI 11, MISO 12
constexpr uint8_t PIN_SPIB_MISO = 39, PIN_CS_595 = 38, PIN_CS_POT = 37;  // SPI-B (SPI1): SCK 27, MOSI 26
constexpr uint8_t PIN_EXP_INT = 22, PIN_LED_DATA = 17;                  // I2S on 23/21/20/7/8, I2C on 18/19
constexpr uint8_t PIN_GATE_IN[4] = {2, 3, 4, 5};
// every board net on the module except SDA/SCL: inputs at boot (MIDI is Serial1 on 0 and 1)
constexpr uint8_t BOARD_PINS[] = {13, 11, 12, 10, 9, 27, 26, 39, 38, 37, 23, 21, 20, 7, 8, 22, 17, 2, 3, 4, 5, 0, 1};

// ---- I2C
constexpr uint8_t ADDR_TCA = 0x20, ADDR_EE = 0x50;
enum : uint8_t { TCA_IN0, TCA_IN1, TCA_OUT0, TCA_OUT1, TCA_POL0, TCA_POL1, TCA_CFG0, TCA_CFG1 };
// TCA9555 port 0: P00-P05 the CV1-6 jack switches (1 = on), P06 GATE_OE_N, P07 button SW9 (input).
// Port 1: buttons SW1-8. Every button line idles high (10 kΩ up) and reads 0 when pressed.
constexpr uint8_t SW_ALL = 0x3F, OE_N = 0x40;
constexpr uint16_t EE_TEST = 0x1FE0;  // the last 32-byte page; calibration will start at the bottom

// ---- converters
SPISettings SPI_CONV(4000000, MSBFIRST, SPI_MODE1);   // ADS8688 and DAC8568 both latch on falling edges; 17 MHz allowed
SPISettings SPI_PANEL(1000000, MSBFIRST, SPI_MODE0);  // MCP3208 at 3.3 V: 1 MHz at most (requirement 14)
constexpr uint16_t DAC_ZERO = 32544;                  // the code for 0 V at the jack (spec §15)
constexpr float VBIAS = 2.25f * 100 / 1100;           // an open CV input: 1 MΩ to the ADS8688's 2.25 V against 100 kΩ
constexpr float RLOAD = 100.0f * 1000 / 1100;         // ...and the same pair as a load, kΩ

// CV out stage (spec §15): Vout = 4.3 Vdac - 3.3 OFFSET_REF, OFFSET_REF = 2.5 V x 22k / 34k
static float cv_out_volts(float code) { return 4.3f * 2.5f * code / 65536 - 3.3f * 2.5f * 22 / 34; }
// what ADC channel n reads with its switch on and nothing patched: the op-amp through the switch's
// 25 Ω, 1 kΩ to the jack and 1 kΩ to the ADC pin, into 100 kΩ to ground and the ADC's 1 MΩ to its bias
static float cv_read_expected(float v) { return VBIAS + (v - VBIAS) * RLOAD / (RLOAD + 2.025f); }
// the jack itself, from the ADC reading: add back the drop across the 1 kΩ on the ADC side
static float jack_from_adc(float v) { return v + (v - VBIAS) / RLOAD; }

// ---- state
static bool powered, exp_ready, spia_ready, adc_ready, dac_ready, spib_ready, audio_ready, leds_ready, enc_ready, midi_ready;
static uint8_t port0 = OE_N;  // TCA9555 output port 0: switches off, gate outputs disabled

static AudioSynthWaveform *wave;
static AudioRecordQueue *rec[2];

constexpr int NUM_LEDS = 16;  // data for 16; a shorter chain shows the first few
static byte led_draw[NUM_LEDS * 3];
DMAMEM static byte led_frame[NUM_LEDS * 12];
static WS2812Serial leds(NUM_LEDS, led_frame, led_draw, PIN_LED_DATA, WS2812_GRB);
static QuadEncoder *enc;

// ---- serial
static char line[48];

static bool read_line() {  // true once a whole line (possibly empty) is in `line`
  static uint8_t n = 0;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r' || c == '\n') {
      line[n] = 0;
      n = 0;
      return true;
    }
    if (n < sizeof(line) - 1) line[n++] = c;
  }
  return false;
}

static void drain() {
  delay(5);
  while (Serial.available()) Serial.read();
}

static bool wait_enter(const char *prompt) {  // false if the answer starts with q
  drain();
  Serial.printf("  %s [Enter, or q to stop] ", prompt);
  while (!read_line()) {
  }
  Serial.println();
  return line[0] != 'q';
}

static bool enter_pressed() {
  if (!Serial.available()) return false;
  drain();
  return true;
}

static void verdict(bool ok, const char *what) { Serial.printf("  %s  %s\n", ok ? "PASS" : "FAIL", what); }

// ---- I2C devices
static bool i2c_present(uint8_t a) {
  Wire.beginTransmission(a);
  return Wire.endTransmission() == 0;
}

static bool tca_write(uint8_t reg, uint8_t v) {
  Wire.beginTransmission(ADDR_TCA);
  Wire.write(reg);
  Wire.write(v);
  return Wire.endTransmission() == 0;
}

static bool tca_read(uint8_t reg, uint8_t &v) {
  Wire.beginTransmission(ADDR_TCA);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(ADDR_TCA, (uint8_t)1) != 1) return false;
  v = Wire.read();
  return true;
}

static bool expander_start() {
  if (exp_ready) return true;
  // the output register first, so each pin comes up at that level as it turns into an output
  exp_ready = tca_write(TCA_OUT0, port0) && tca_write(TCA_CFG0, 0x80) && tca_write(TCA_CFG1, 0xFF);
  if (!exp_ready) Serial.println("  The TCA9555 did not take its settings: run block 1.");
  return exp_ready;
}

static bool set_port0(uint8_t v) {
  port0 = v;
  return tca_write(TCA_OUT0, v);
}

static bool ee_write(uint16_t a, const uint8_t *d, uint8_t n) {  // n <= 16, inside one page
  Wire.beginTransmission(ADDR_EE);
  Wire.write(a >> 8);
  Wire.write(a & 0xFF);
  Wire.write(d, n);
  if (Wire.endTransmission() != 0) return false;
  for (uint32_t t = millis(); millis() - t < 20;)  // no acknowledge until the write cycle (5 ms max) ends
    if (i2c_present(ADDR_EE)) return true;
  return false;
}

static bool ee_read(uint16_t a, uint8_t *d, uint8_t n) {
  Wire.beginTransmission(ADDR_EE);
  Wire.write(a >> 8);
  Wire.write(a & 0xFF);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(ADDR_EE, n) != n) return false;
  for (uint8_t i = 0; i < n; i++) d[i] = Wire.read();
  return true;
}

// ---- SPI-A: ADS8688 and DAC8568
static void spia_start() {
  if (spia_ready) return;
  digitalWrite(PIN_CS_ADC, HIGH);
  pinMode(PIN_CS_ADC, OUTPUT);
  digitalWrite(PIN_CS_DAC, HIGH);
  pinMode(PIN_CS_DAC, OUTPUT);
  SPI.begin();
  spia_ready = true;
}

static uint16_t adc_frame(uint16_t cmd) {  // 32 clocks: a command in, the previous frame's conversion out
  SPI.beginTransaction(SPI_CONV);
  digitalWriteFast(PIN_CS_ADC, LOW);
  SPI.transfer16(cmd);
  uint16_t r = SPI.transfer16(0);
  digitalWriteFast(PIN_CS_ADC, HIGH);
  SPI.endTransaction();
  return r;
}

static uint8_t adc_reg(uint8_t reg, int val = -1) {  // read if val < 0; a write echoes the byte written
  SPI.beginTransaction(SPI_CONV);
  digitalWriteFast(PIN_CS_ADC, LOW);
  SPI.transfer16((reg << 9) | (val >= 0 ? 0x100 | val : 0));
  uint8_t r = SPI.transfer(0);
  digitalWriteFast(PIN_CS_ADC, HIGH);
  SPI.endTransaction();
  return r;
}

static float adc_read(uint8_t ch, int n = 16) {  // volts, the mean of n conversions on ±10.24 V
  adc_frame(0xC000 | (ch << 10));                // MAN_Ch_n: converts in the next frame
  uint32_t sum = 0;
  for (int i = 0; i < n; i++) sum += adc_frame(0x0000);  // NO_OP: carry on with that channel
  return ((float)sum / n - 32768) * 20.48f / 65536;
}

// write 0x01 to channel 1's range register and read it, then the same with 0x00: a stuck MISO
// echoes one value only
static bool adc_echo(bool print) {
  uint8_t e1 = adc_reg(0x05, 0x01), r1 = adc_reg(0x05), e0 = adc_reg(0x05, 0x00), r0 = adc_reg(0x05);
  if (print)
    Serial.printf("  Range register, channel 1: wrote 01, echoed %02X, read %02X; wrote 00, echoed %02X, read %02X\n",
                  e1, r1, e0, r0);
  return e1 == 0x01 && r1 == 0x01 && e0 == 0x00 && r0 == 0x00;
}

static bool adc_start(bool print = false) {
  if (adc_ready && !print) return true;
  spia_start();
  bool ok = adc_echo(print);
  for (uint8_t ch = 0; ok && ch < 8; ch++) ok = adc_reg(0x05 + ch, 0x00) == 0x00 && adc_reg(0x05 + ch) == 0x00;  // ±10.24 V
  adc_ready = ok;
  if (!ok && !print) Serial.println("  The ADS8688 is not answering: run block 4.");
  return ok;
}

static void dac_frame(uint32_t w) {
  SPI.beginTransaction(SPI_CONV);
  digitalWriteFast(PIN_CS_DAC, LOW);
  SPI.transfer16(w >> 16);
  SPI.transfer16(w & 0xFFFF);
  digitalWriteFast(PIN_CS_DAC, HIGH);
  SPI.endTransaction();
}

static void dac_write(uint8_t ch, uint16_t code) { dac_frame(0x03000000 | (ch << 20) | ((uint32_t)code << 4)); }  // write and update

static bool dac_start() {  // the start-up order of spec §15, firmware requirement 3
  if (dac_ready) return true;
  if (!expander_start() || !set_port0(port0 & ~SW_ALL)) return false;  // 1. every jack switch off
  spia_start();
  for (uint8_t ch = 0; ch < 8; ch++) dac_write(ch, DAC_ZERO);  // 2. 0 V codes while the reference is still off
  dac_frame(0x090A0000);                                       // 3. internal reference on: flexible mode, always on
  delay(10);                                                   // 4. settle (to confirm on the bench)
  dac_ready = true;  // 5 and 6 (targets, then switches) are each block's own; 7: never the software reset
  return true;
}

// ---- SPI-B: 74HCT595 and MCP3208
static void spib_start() {
  if (spib_ready) return;
  digitalWrite(PIN_CS_595, HIGH);
  pinMode(PIN_CS_595, OUTPUT);
  digitalWrite(PIN_CS_POT, HIGH);
  pinMode(PIN_CS_POT, OUTPUT);
  SPI1.setMISO(PIN_SPIB_MISO);
  SPI1.begin();
  spib_ready = true;
}

// the 595 shifts every panel-bus frame, so always a whole word before RCLK (requirement 14)
static void gates_write(uint8_t word) {  // bit 0 = gate out 1
  SPI1.beginTransaction(SPI_PANEL);
  SPI1.transfer(word);
  SPI1.endTransaction();
  digitalWriteFast(PIN_CS_595, LOW);  // RCLK: latches on the rising edge
  delayMicroseconds(1);
  digitalWriteFast(PIN_CS_595, HIGH);
}

static uint16_t pot_read(uint8_t ch) {  // MCP3208, single-ended: start, SGL, D2-D0, then 12 bits
  SPI1.beginTransaction(SPI_PANEL);
  digitalWriteFast(PIN_CS_POT, LOW);
  SPI1.transfer(0x06 | (ch >> 2));
  uint8_t hi = SPI1.transfer((ch & 3) << 6);
  uint8_t lo = SPI1.transfer(0);
  digitalWriteFast(PIN_CS_POT, HIGH);
  SPI1.endTransaction();
  return ((hi & 0x0F) << 8) | lo;
}

static uint8_t gate_ins() {
  uint8_t g = 0;
  for (int i = 0; i < 4; i++) g |= digitalRead(PIN_GATE_IN[i]) << i;
  return g;
}

// ---- audio
static void audio_start() {
  if (audio_ready) return;
  AudioMemory(60);
  wave = new AudioSynthWaveform();
  // each I2S object starts the SAI as it is made: MCLK on 23, BCK 21, LRCK 20, out on 7, in on 8
  AudioOutputI2S *out = new AudioOutputI2S();
  AudioInputI2S *in = new AudioInputI2S();
  new AudioConnection(*wave, 0, *out, 0);
  new AudioConnection(*wave, 0, *out, 1);
  for (int i = 0; i < 2; i++) {
    rec[i] = new AudioRecordQueue();
    new AudioConnection(*in, i, *rec[i], 0);
  }
  wave->begin(0.0f, 440, WAVEFORM_SINE);
  audio_ready = true;
}

static void capture(int i, int blocks, int &mn, int &mx) {  // the extremes of `blocks` x 128 samples
  rec[i]->clear();
  rec[i]->begin();
  mn = 32767;
  mx = -32768;
  for (uint32_t t = millis(); blocks > 0 && millis() - t < 2000;) {
    if (!rec[i]->available()) continue;
    int16_t *b = rec[i]->readBuffer();
    for (int k = 0; k < AUDIO_BLOCK_SAMPLES; k++) {
      if (b[k] < mn) mn = b[k];
      if (b[k] > mx) mx = b[k];
    }
    rec[i]->freeBuffer();
    blocks--;
  }
  rec[i]->end();
  rec[i]->clear();
}

// ---- blocks
static void block_i2c() {
  Serial.println("Block 1, I2C: scanning 0x08-0x77 at 400 kHz");
  bool tca = false, ee = false;
  for (uint8_t a = 0x08; a < 0x78; a++) {
    if (!i2c_present(a)) continue;
    Serial.printf("  0x%02X  %s\n", a,
                  a == ADDR_TCA ? "TCA9555 expander" : a == ADDR_EE ? "M24C64 EEPROM" : (a == 0x3C || a == 0x3D) ? "an OLED?" : "");
    tca |= a == ADDR_TCA;
    ee |= a == ADDR_EE;
  }
  powered = ee;
  verdict(tca && ee, "0x20 (TCA9555) and 0x50 (M24C64) answer");
}

static void block_eeprom() {
  Serial.println("Block 2, EEPROM: flip every bit of the last page (0x1FE0), read it back, then restore it");
  uint8_t old[32], pat[32], got[32];
  if (!ee_read(EE_TEST, old, 16) || !ee_read(EE_TEST + 16, old + 16, 16)) {
    verdict(false, "the M24C64 did not answer a read");
    return;
  }
  for (int i = 0; i < 32; i++) pat[i] = ~old[i];
  bool ok = ee_write(EE_TEST, pat, 16) && ee_write(EE_TEST + 16, pat + 16, 16) && ee_read(EE_TEST, got, 16) &&
            ee_read(EE_TEST + 16, got + 16, 16);
  int bad = 0;
  for (int i = 0; i < 32; i++) bad += got[i] != pat[i];
  bool back = ee_write(EE_TEST, old, 16) && ee_write(EE_TEST + 16, old + 16, 16) && ee_read(EE_TEST, got, 16) &&
              ee_read(EE_TEST + 16, got + 16, 16) && memcmp(got, old, 32) == 0;
  Serial.printf("  32 bytes written, %d read back wrong; the old bytes %s\n", ok ? bad : 32, back ? "restored" : "NOT restored");
  verdict(ok && bad == 0 && back, "the same bytes come back");
}

static void block_expander() {
  Serial.println("Block 3, expander: switches off and gate outputs disabled, then read both ports");
  if (!expander_start()) return;
  uint8_t out0 = 0, cfg0 = 0, cfg1 = 0, in0 = 0, in1 = 0;
  bool regs = tca_read(TCA_OUT0, out0) && tca_read(TCA_CFG0, cfg0) && tca_read(TCA_CFG1, cfg1);
  Serial.printf("  Output port 0 %02X, config %02X %02X (want %02X, 80 FF)\n", out0, cfg0, cfg1, port0);
  regs = regs && out0 == port0 && cfg0 == 0x80 && cfg1 == 0xFF;
  for (int i = 0; i < 2; i++) regs = regs && tca_read(TCA_IN0, in0) && tca_read(TCA_IN1, in1);  // a read clears INT
  delay(1);
  int irq = digitalRead(PIN_EXP_INT);
  Serial.printf("  Switch enables %s, GATE_OE_N %s, EXP_INT %s\n", (in0 & SW_ALL) ? "SOME ON" : "all off",
                (in0 & OE_N) ? "high" : "LOW", irq ? "high" : "LOW");
  uint16_t btn = in1 | ((in0 & 0x80) << 1);  // bit n = SW(n+1), 1 = released
  Serial.print("  Buttons pressed:");
  for (int i = 0; i < 9; i++)
    if (!(btn & (1 << i))) Serial.printf(" SW%d", i + 1);
  Serial.println(btn == 0x1FF ? " none" : "  (with nothing wired, a pressed line is a short to ground)");
  verdict(regs && (in0 & (SW_ALL | OE_N)) == (port0 & (SW_ALL | OE_N)) && irq, "the expander reads back what it was given, INT idles high");
}

static void block_adc() {
  Serial.println("Block 4, ADC: ADS8688 registers, then the eight inputs on ±10.24 V");
  bool regs = adc_start(true);
  verdict(regs, "the ADS8688 echoes its registers");
  if (!regs) {
    Serial.println("  Look at SPI-A: TP401 SCK, TP402 MOSI, TP403 MISO, TP404 CS_ADC, and +5VA, +3V3D at the chip.");
    return;
  }
  bool ok = true;
  for (uint8_t ch = 0; ch < 8; ch++) {
    float v = adc_read(ch, 64);
    bool tied = ch >= 6;  // AIN_6 and AIN_7 go to ground on this board
    bool good = tied ? fabsf(v) < 0.02f : (v > 0.1f && v < 0.3f);
    ok &= good;
    if (tied)
      Serial.printf("  AIN%u %+.3f V  tied to ground: 0 V\n", ch, v);
    else
      Serial.printf("  CV%u  %+.3f V  open: about %+.2f V (the ADC's bias against 100 kOhm)%s\n", ch + 1, v, VBIAS,
                    good ? "" : "  <- patched, or a fault");
  }
  verdict(ok, "open inputs read +0.1 to +0.3 V, the two grounded ones within 20 mV of 0");
}

static void block_dac() {
  Serial.println("Block 5, DAC to ADC: each of CV1-6 out through its jack switch and back into the ADC");
  if (!wait_enter("Nothing patched into CV1-6?")) return;
  if (!adc_start() || !dac_start()) return;
  const uint16_t codes[] = {0, 8192, 16384, 24576, DAC_ZERO, 40960, 49152, 57344, 65535};
  bool all = true;
  for (uint8_t ch = 0; ch < 6; ch++) {
    dac_write(ch, 65535);  // switch off: full scale must not reach the jack
    delay(3);
    float off = adc_read(ch, 32);
    dac_write(ch, DAC_ZERO);  // the channel holds 0 V before its switch closes (requirement 3.6)
    delay(3);
    set_port0(port0 | (1 << ch));
    delay(5);
    float worst = 0, lo = 0, zero = 0, hi = 0, prev = -100;
    bool rising = true;
    for (uint16_t c : codes) {
      dac_write(ch, c);
      delay(3);
      float v = adc_read(ch, 32), err = v - cv_read_expected(cv_out_volts(c));
      if (fabsf(err) > fabsf(worst)) worst = err;
      rising &= v > prev;
      prev = v;
      if (c == 0) lo = v;
      if (c == DAC_ZERO) zero = v;
      if (c == 65535) hi = v;
    }
    dac_write(ch, DAC_ZERO);
    delay(3);
    set_port0(port0 & ~(1 << ch));
    bool ok = rising && fabsf(worst) < 0.2f && fabsf(off - VBIAS) < 0.1f;
    all &= ok;
    Serial.printf("  CV%u  %+.3f V at code 0, %+.3f V at the 0 V code, %+.3f V at 65535; worst error %+4.0f mV; "
                  "switch off %+.3f V  %s\n", ch + 1, lo, zero, hi, worst * 1000, off, ok ? "PASS" : "FAIL");
  }
  Serial.printf("  Design: %+.2f to %+.2f V from the op-amp, read about 2%% low through the 2 kOhm to the ADC.\n",
                cv_out_volts(0), cv_out_volts(65535));
  verdict(all, "every channel rises with the code, within 0.2 V of the design, and is cut off by its switch");
}

static void block_codec() {
  Serial.println("Block 6, codec clocks: I2S at 44.1 kHz, the Teensy Audio library's rate");
  audio_start();
  Serial.println("  Running: MCLK 11.29 MHz, BCK 2.82 MHz, LRCK 44.1 kHz.");
  Serial.println("  On DC volts TP301 (MCLK), TP302 (BCK) and TP303 (LRCK) each read about 1.65 V;");
  Serial.println("  a meter that counts Hz shows the rate instead.");
  int mn[2], mx[2];
  for (int i = 0; i < 2; i++) capture(i, 40, mn[i], mx[i]);
  Serial.printf("  0.1 s from the codec's ADC: AIN1 %d to %d, AIN2 %d to %d (16-bit codes)\n", mn[0], mx[0], mn[1], mx[1]);
  bool alive = mn[0] || mx[0] || mn[1] || mx[1];
  Serial.println(alive ? "  The codec is sending samples."
                       : "  Every sample is exactly 0: the codec may not be running (MCLK, RST, +5VA and +3V3D at U301).");
}

static void block_gate_outs() {
  Serial.println("Block 7, gate outs: shift and latch a word, then GATE_OE_N low");
  if (!expander_start()) return;
  spib_start();
  gates_write(0);  // a whole word latched before the outputs turn on (requirement 4)
  set_port0(port0 & ~OE_N);
  const uint8_t words[] = {0x5, 0xA, 0xF, 0x0};
  for (uint8_t w : words) {
    gates_write(w);
    delay(2);
    Serial.print("  Now:");
    for (int i = 0; i < 4; i++) Serial.printf("  GOUT%d %s", i + 1, (w >> i) & 1 ? "5 V" : "0 V");
    uint8_t g = gate_ins();
    Serial.printf("   (gate ins read %d%d%d%d%s)\n", g & 1, (g >> 1) & 1, (g >> 2) & 1, (g >> 3) & 1,
                  g == w ? ": the same, if GOUT1-4 are wired to GIN1-4" : "");
    if (!wait_enter("Measure at the gate-out holes, then")) break;
  }
  gates_write(0);
  set_port0(port0 | OE_N);
  Serial.println("  Gate outputs low and disabled again.");
}

static volatile uint32_t gate_rises[4];
static void rise0() { gate_rises[0]++; }
static void rise1() { gate_rises[1]++; }
static void rise2() { gate_rises[2]++; }
static void rise3() { gate_rises[3]++; }

static void block_gate_ins() {
  Serial.println("Block 8, gate ins: live state and rising edges, Enter to stop");
  if (enc_ready) Serial.println("  The encoder (block 12) holds gate ins 3-4 until a restart.");
  void (*isr[4])() = {rise0, rise1, rise2, rise3};
  for (int i = 0; i < 4; i++) {
    gate_rises[i] = 0;
    attachInterrupt(digitalPinToInterrupt(PIN_GATE_IN[i]), isr[i], RISING);
  }
  drain();
  while (!enter_pressed()) {
    Serial.print("\r ");
    for (int i = 0; i < 4; i++) Serial.printf("  GIN%d %s %6lu", i + 1, digitalRead(PIN_GATE_IN[i]) ? "HIGH" : "low ", gate_rises[i]);
    delay(100);
  }
  for (int i = 0; i < 4; i++) detachInterrupt(digitalPinToInterrupt(PIN_GATE_IN[i]));
  Serial.println();
}

static void block_gate_threshold(int n) {
  Serial.printf("Block 8t, gate in %d threshold: sweep CV1 0 to 3 V and back, wired to GIN%d\n", n, n);
  if (n < 1 || n > 4) {
    Serial.println("  Which gate in? 8t 1 to 8t 4.");
    return;
  }
  if (!wait_enter("Wire from the CV1 hole to the gate-in hole, nothing else on CV1. Ready?")) return;
  if (!adc_start() || !dac_start()) return;
  uint8_t pin = PIN_GATE_IN[n - 1];
  const uint16_t top = DAC_ZERO + 3.0f / (4.3f * 2.5f) * 65536;
  dac_write(0, DAC_ZERO);
  set_port0(port0 | 0x01);
  delay(5);
  float up = NAN, down = NAN;
  for (uint32_t c = DAC_ZERO; c <= top && isnan(up); c += 24) {  // 24 codes: about 4 mV at the jack
    dac_write(0, c);
    delayMicroseconds(300);
    if (digitalRead(pin)) up = jack_from_adc(adc_read(0, 8));
  }
  dac_write(0, top);
  delay(3);
  for (int32_t c = top; c >= DAC_ZERO && isnan(down); c -= 24) {
    dac_write(0, c);
    delayMicroseconds(300);
    if (!digitalRead(pin)) down = jack_from_adc(adc_read(0, 8));
  }
  dac_write(0, DAC_ZERO);
  delay(3);
  set_port0(port0 & ~0x01);
  Serial.printf("  GIN%d goes high at %.2f V rising and low at %.2f V falling (design 1.98 and 1.67)\n", n, up, down);
  verdict(fabsf(up - 1.98f) < 0.15f && fabsf(down - 1.67f) < 0.15f, "both within 0.15 V of the design");
}

static void block_pots() {
  Serial.println("Block 9, pots: MCP3208 CH0-5 = POT1-6, CH6-7 tied to ground. Enter to stop");
  spib_start();
  drain();
  while (!enter_pressed()) {
    Serial.print("\r ");
    for (int ch = 0; ch < 8; ch++) Serial.printf(" %s%d %4u", ch < 6 ? "POT" : "CH", ch < 6 ? ch + 1 : ch, pot_read(ch));
    delay(100);
  }
  Serial.println("\n  Each pot should sweep 0 to 4095; an unwired one reads 0, a wire from POT_REF reads 4095.");
}

static void block_audio() {
  Serial.println("Block 10, audio: a 440 Hz sine on AOUT1 and AOUT2 at about 10 Vpp, half the 20 Vpp full scale");
  audio_start();
  wave->begin(0.5f, 440, WAVEFORM_SINE);
  Serial.println("  On AC volts AOUT1 and AOUT2 read about 3.5 V. Listen through the rack, or record it on the ES-10.");
  if (!wait_enter("For the inputs, wire AOUT1 to AIN1 and AOUT2 to AIN2, then")) return;
  bool level = true, inverted = true;
  for (int i = 0; i < 2; i++) {
    int mn, mx;
    capture(i, 40, mn, mx);
    float vpp = (mx - mn) / 65536.0f * 22;  // input full scale about 22 Vpp (gain -0.136 into 3 Vpp)
    level &= vpp > 8 && vpp < 12;
    Serial.printf("  AIN%d: %.1f Vpp of the 10 sent\n", i + 1, vpp);
  }
  // the inputs invert (requirement 6): a narrow pulse, made lopsided by the AC coupling, shows which way
  wave->pulseWidth(0.1f);
  wave->begin(0.25f, 100, WAVEFORM_PULSE);
  delay(600);  // the coupling capacitors settle
  for (int i = 0; i < 2; i++) {
    int mn, mx;
    capture(i, 40, mn, mx);
    bool inv = -mn > mx;
    inverted &= inv;
    Serial.printf("  AIN%d with a 10%% pulse: peaks %+d and %+d: %s\n", i + 1, mx, mn, inv ? "inverted" : "not inverted");
  }
  wave->begin(0.5f, 440, WAVEFORM_SINE);
  verdict(level, "the inputs read 8 to 12 Vpp of the 10 Vpp sent");
  verdict(inverted, "the loop inverts, as designed: firmware negates the input samples");
  Serial.println("  The sine stays on until 0.");
}

static void block_leds() {
  Serial.println("Block 11, LEDs: WS2812 on the LED holes, at about a tenth of full brightness");
  if (!leds_ready) leds_ready = leds.begin();
  const uint32_t colours[] = {0x180000, 0x001800, 0x000018, 0x101010};  // about 3 mA a LED at most (requirement 15)
  const char *names[] = {"red", "green", "blue", "white"};
  for (int k = 0; k < 4; k++) {
    for (int i = 0; i < NUM_LEDS; i++) leds.setPixel(i, colours[k]);
    leds.show();
    Serial.printf("  All %s\n", names[k]);
    delay(1000);
  }
  Serial.println("  One dot running along the chain, Enter to stop");
  drain();
  for (int i = 0; !enter_pressed(); i = (i + 1) % NUM_LEDS) {
    for (int j = 0; j < NUM_LEDS; j++) leds.setPixel(j, j == i ? 0x101010 : 0);
    leds.show();
    delay(150);
  }
  for (int j = 0; j < NUM_LEDS; j++) leds.setPixel(j, 0);
  leds.show();
}

static void block_encoder() {
  Serial.println("Block 12, encoder: A on GIN3, B on GIN4 (QuadEncoder), common to +3V3D; push on a button hole");
  if (!enc_ready) {
    enc = new QuadEncoder(1, PIN_GATE_IN[2], PIN_GATE_IN[3], 0);  // no internal pull-ups: the LM393s have theirs
    enc->setInitConfig();
    enc->EncConfig.filterCount = 7;  // the longest input filter, against contact bounce
    enc->EncConfig.filterSamplePeriod = 255;
    enc->init();
    enc_ready = true;
    Serial.println("  Gate ins 3-4 now belong to the encoder until a restart.");
  }
  if (!expander_start()) return;
  Serial.println("  Turn it both ways and press it. Enter to stop");
  drain();
  int32_t last = 0x7FFFFFFF;
  uint16_t last_btn = 0x1FF;
  while (!enter_pressed()) {
    int32_t c = enc->read();
    uint8_t in0 = 0xFF, in1 = 0xFF;
    tca_read(TCA_IN0, in0);
    tca_read(TCA_IN1, in1);
    uint16_t btn = in1 | ((in0 & 0x80) << 1);
    if (c != last || btn != last_btn) {
      Serial.printf("  count %ld (%ld detents)", c, c / 4);
      for (int i = 0; i < 9; i++)
        if (!(btn & (1 << i))) Serial.printf("  SW%d pressed", i + 1);
      Serial.println();
      last = c;
      last_btn = btn;
    }
    delay(20);  // polled, as the TCA9555 INT is only a backstop (requirement 13)
  }
}

static void block_midi() {
  Serial.println("Block 13, MIDI: Serial1 at 31 250 baud (after stage 7: H11L1 fitted, J101 links in)");
  if (!midi_ready) {
    Serial1.begin(31250);
    midi_ready = true;
  }
  while (Serial1.available()) Serial1.read();
  const uint8_t msg[] = {0x90, 0x3C, 0x64, 0x80, 0x3C, 0x00, 0xB0, 0x07, 0x55, 0xF8};
  int good = 0;
  for (uint8_t b : msg) {
    Serial1.write(b);
    uint32_t t = millis();
    while (!Serial1.available() && millis() - t < 10) {
    }
    good += Serial1.available() && Serial1.read() == b;
  }
  Serial.printf("  Loop test: %d of %d bytes came back\n", good, (int)sizeof(msg));
  verdict(good == (int)sizeof(msg), "bytes in = bytes out, with a TRS cable from OUT to IN");
  Serial.println("  Now showing whatever arrives at IN; play some notes. Enter to stop");
  drain();
  int n = 0;
  while (!enter_pressed()) {
    while (Serial1.available()) {
      uint8_t b = Serial1.read();
      if (b >= 0x80 && n) Serial.println(), n = 0;
      Serial.printf(" %02X", b);
      n++;
    }
  }
  Serial.println();
}

static void safe() {
  if (audio_ready) wave->amplitude(0);
  if (leds_ready) {
    for (int j = 0; j < NUM_LEDS; j++) leds.setPixel(j, 0);
    leds.show();
  }
  if (spib_ready) gates_write(0);
  if (exp_ready) set_port0((port0 & ~SW_ALL) | OE_N);
  if (dac_ready)
    for (uint8_t ch = 0; ch < 8; ch++) dac_write(ch, DAC_ZERO);
  Serial.println("Safe: jack switches off, gate outs low and disabled, DAC at 0 V, audio and LEDs off.");
}

static void status() {
  Serial.printf("Board %s. Running: expander %s, ADC %s, DAC %s, panel bus %s, audio %s, LEDs %s, encoder %s, MIDI %s\n",
                powered ? "powered (the EEPROM answers)" : "NOT answering", exp_ready ? "yes" : "no", adc_ready ? "yes" : "no",
                dac_ready ? "yes" : "no", spib_ready ? "yes" : "no", audio_ready ? "yes" : "no", leds_ready ? "yes" : "no",
                enc_ready ? "yes" : "no", midi_ready ? "yes" : "no");
  if (exp_ready)
    Serial.printf("  Jack switches %02X (bit 0 = CV1), gate outputs %s\n", port0 & SW_ALL, port0 & OE_N ? "disabled" : "enabled");
}

static void help() {
  Serial.println();
  Serial.println("Analogue board Rev A test (Teensy 4.1). Type a command and Enter.");
  Serial.println("  1    I2C scan                    no deck");
  Serial.println("  2    EEPROM                      no deck");
  Serial.println("  3    expander                    no deck");
  Serial.println("  4    ADC                         no deck");
  Serial.println("  5    DAC to ADC, CV1-6           no deck; nothing patched into CV1-6");
  Serial.println("  6    codec clocks                no deck; meter on TP301-TP303");
  Serial.println("  7    gate outs                   no deck; meter on the gate-out holes");
  Serial.println("  8    gate ins, live              a rack gate or a wire into GIN1-4");
  Serial.println("  8t N gate in N threshold         a wire from CV1 to GIN N");
  Serial.println("  9    pots, live                  deck, or a wire from POT_REF to a pot hole");
  Serial.println("  10   audio                       sine out; AOUT1-2 wired to AIN1-2 for the input checks");
  Serial.println("  11   LEDs                        a WS2812 chain on the LED holes");
  Serial.println("  12   encoder, live               A, B on GIN3-4, common to +3V3D; push on a button hole");
  Serial.println("  13   MIDI                        after stage 7; a TRS cable from OUT to IN");
  Serial.println("  0    safe: switches off, gate outs off, DAC at 0 V, audio and LEDs off");
  Serial.println("  s    status        h  this list");
}

static void run(char *cmd) {
  int n = atoi(cmd);
  if (cmd[0] == 'h' || cmd[0] == '?') return help();
  if (cmd[0] == 's') return status();
  if (!powered && n != 1) {
    Serial.println("The EEPROM at 0x50 does not answer, so the board looks unpowered: only 1 (rescan) runs.");
    return;
  }
  if (strchr(cmd, 't') && n == 8) return block_gate_threshold(atoi(strchr(cmd, 't') + 1));
  switch (n) {
    case 0: return safe();
    case 1: return block_i2c();
    case 2: return block_eeprom();
    case 3: return block_expander();
    case 4: return block_adc();
    case 5: return block_dac();
    case 6: return block_codec();
    case 7: return block_gate_outs();
    case 8: return block_gate_ins();
    case 9: return block_pots();
    case 10: return block_audio();
    case 11: return block_leds();
    case 12: return block_encoder();
    case 13: return block_midi();
  }
  Serial.printf("Not a command: %s (h for the list)\n", cmd);
}

void setup() {
  for (uint8_t p : BOARD_PINS) pinMode(p, INPUT);
  Serial.begin(115200);
  while (!Serial && millis() < 4000) {
  }
  Wire.begin();
  Wire.setClock(400000);
  powered = i2c_present(ADDR_EE);
  help();
  if (!powered)
    Serial.println("\nThe EEPROM at 0x50 does not answer: is the rack on? Every other bus stays off (requirement 1).");
  Serial.print("\n> ");
}

void loop() {
  if (!read_line()) return;
  if (line[0]) {
    run(line);
    Serial.print("\n> ");
  }
}
