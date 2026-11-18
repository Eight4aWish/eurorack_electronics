// Analogue board Rev B with the Waveshare ESP32-P4-WIFI6: the stage 6 bring-up test of
// docs/analogue_board_revb_bringup.md. A port of firmware/analogue_board_test (Rev A, Teensy 4.1):
// the same serial menu and the same block numbers, against Rev B's pin map
// (docs/analogue_board_esp32p4.md, Pin table) and netlist
// (hardware/analogue_board/pico_revb/output/analogue_board_pico_revb.net).
//
// The first act is the LDO. The P4's GPIO46-48 (SPIA_SCK, CS_ADC, CS_DAC) sit in the I/O bank that
// LDO channel 4 powers, and the converter bus works only once it is at 3.3 V. After that, nothing
// on the board is driven until its block is asked for: at boot only I2C runs, and the M24C64 must
// answer before any other bus starts (spec §15, firmware requirement 1).
//
// What differs from Rev A:
// - no EXP_INT: the expander is polled;
// - six buttons, SW1-6 on the expander's port 1;
// - the CV outputs swing ±10 V (Rev B §8), and CVO7 and CVI7 are a fixed CV out and in;
// - the codec at 48 kHz with its MCLK from the APLL;
// - beside each channel, the jack or control it is wired to on Health's panel (stage 7).

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "driver/i2s_std.h"
#include "driver/pulse_cnt.h"
#include "driver/rmt_encoder.h"
#include "driver/rmt_tx.h"
#include "driver/spi_master.h"
#include "driver/uart.h"
#include "driver/uart_vfs.h"
#include "esp_ldo_regulator.h"
#include "esp_log.h"
#include "esp_rom_sys.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

// ---- pins: P4 GPIO, with the module's header pin (Pico numbering) in the comment
constexpr gpio_num_t PIN_SDA = GPIO_NUM_31, PIN_SCL = GPIO_NUM_30;                                       // 4, 5
constexpr gpio_num_t PIN_SPIA_SCK = GPIO_NUM_46, PIN_SPIA_MOSI = GPIO_NUM_33, PIN_SPIA_MISO = GPIO_NUM_32;  // 24, 25, 26
constexpr gpio_num_t PIN_CS_ADC = GPIO_NUM_47, PIN_CS_DAC = GPIO_NUM_48;                                 // 22, 21
constexpr gpio_num_t PIN_SPIB_SCK = GPIO_NUM_3, PIN_SPIB_MOSI = GPIO_NUM_2, PIN_SPIB_MISO = GPIO_NUM_5;  // 14, 15, 11
constexpr gpio_num_t PIN_CS_POT = GPIO_NUM_24, PIN_CS_595 = GPIO_NUM_25;                                 // 19, 20
constexpr gpio_num_t PIN_GATE_IN[4] = {GPIO_NUM_50, GPIO_NUM_49, GPIO_NUM_29, GPIO_NUM_4};               // 9, 10, 6, 12
constexpr gpio_num_t PIN_LED_DATA = GPIO_NUM_28;                                                         // 7
constexpr gpio_num_t PIN_MCLK = GPIO_NUM_27, PIN_BCK = GPIO_NUM_23, PIN_LRCK = GPIO_NUM_22;             // 27, 31, 32
constexpr gpio_num_t PIN_I2S_DOUT = GPIO_NUM_21, PIN_I2S_DIN = GPIO_NUM_26;  // 34, 29: to the codec, from it
constexpr gpio_num_t PIN_MIDI_TX = GPIO_NUM_52, PIN_MIDI_RX = GPIO_NUM_51;   // 1, 2
// every board net on the module except SDA and SCL: inputs at boot
constexpr gpio_num_t BOARD_PINS[] = {PIN_SPIA_SCK, PIN_SPIA_MOSI, PIN_SPIA_MISO, PIN_CS_ADC, PIN_CS_DAC, PIN_SPIB_SCK,
                                     PIN_SPIB_MOSI, PIN_SPIB_MISO, PIN_CS_POT, PIN_CS_595, PIN_GATE_IN[0], PIN_GATE_IN[1],
                                     PIN_GATE_IN[2], PIN_GATE_IN[3], PIN_LED_DATA, PIN_MCLK, PIN_BCK, PIN_LRCK,
                                     PIN_I2S_DOUT, PIN_I2S_DIN, PIN_MIDI_TX, PIN_MIDI_RX};

// ---- Health's panel, as wired on 2026-11-17 (bring-up stage 7): what each board channel is on its front
static const char *const CV_NAME[6] = {"X1", "Y2", "X2", "Z1", "Y1", "Z2"};
static const char *const GIN_NAME[4] = {"MENU A", "MENU B", "RST", "CLK"};
static const char *const POT_NAME[6] = {"-", "Y", "-", "X", "-", "Z"};
static const char *const SW_NAME[6] = {"-", "-", "BTN2", "-", "BTN1", "MENU push"};
static const char *const AIN_NAME[2] = {"IN-L", "IN-R"};
static const char *const AOUT_NAME[2] = {"OUT-L", "OUT-R"};

// ---- I2C
constexpr uint8_t ADDR_TCA = 0x20, ADDR_EE = 0x50, ADDR_OLED = 0x3C;
enum : uint8_t { TCA_IN0, TCA_IN1, TCA_OUT0, TCA_OUT1, TCA_POL0, TCA_POL1, TCA_CFG0, TCA_CFG1 };
// TCA9555 port 0: P00-P05 the CV1-6 jack switches (1 = on), P06 GATE_OE_N, P07 unconnected (an input).
// Port 1: P10-P15 the button lines SW1-6, each idling high and reading 0 when pressed; P16 and P17
// unconnected. No INT line on Rev B.
constexpr uint8_t SW_ALL = 0x3F, OE_N = 0x40, BTN_ALL = 0x3F;
constexpr uint16_t EE_TEST = 0x1FE0;  // the last 32-byte page; calibration will start at the bottom

// ---- converters
constexpr int SPI_CONV_HZ = 4000000;   // ADS8688 and DAC8568, mode 1: both latch on falling edges; 17 MHz allowed
constexpr int SPI_PANEL_HZ = 1000000;  // MCP3208 at 3.3 V: 1 MHz at most (requirement 14), mode 0
// CV out stage, the ±10 V variant (Rev B §8): Vout = 8.5 Vdac - 7.5 OFFSET_REF, OFFSET_REF = 2.5 V x 20k / 35k
constexpr float DAC_GAIN = 8.5f, DAC_OFFSET = 7.5f * 2.5f * 20 / 35;  // 10.714 V
static float cv_out_volts(float code) { return DAC_GAIN * 2.5f * code / 65536 - DAC_OFFSET; }
static uint16_t cv_code(float v) {
  long c = lroundf((v + DAC_OFFSET) * 65536 / (DAC_GAIN * 2.5f));
  return c < 0 ? 0 : c > 65535 ? 65535 : (uint16_t)c;
}
static const uint16_t DAC_ZERO = cv_code(0);         // 33043: the code for 0 V at the jack
constexpr float VBIAS = 2.25f * 100 / 1100;           // an open CV input: 1 MΩ to the ADS8688's 2.25 V against 100 kΩ
constexpr float RLOAD = 100.0f * 1000 / 1100;         // ...and the same pair as a load, kΩ
// what ADC channel n reads with its switch on and nothing patched: the op-amp through the switch's
// 25 Ω, 1 kΩ to the jack and 1 kΩ to the ADC pin, into 100 kΩ to ground and the ADC's 1 MΩ to its bias
static float cv_read_expected(float v) { return VBIAS + (v - VBIAS) * RLOAD / (RLOAD + 2.025f); }
// CVO7 takes its feedback from the jack side of its 1 kΩ, so CVI7 sees it through CVI7's 1 kΩ alone
static float cv7_read_expected(float v) { return VBIAS + (v - VBIAS) * RLOAD / (RLOAD + 1.0f); }
// the jack itself, from the ADC reading: add back the drop across the 1 kΩ on the ADC side
static float jack_from_adc(float v) { return v + (v - VBIAS) / RLOAD; }

// ---- audio: the PCM3060 as an I2S slave (hardware mode, 24-bit I2S), 48 kHz, MCLK 256 fs from the APLL
constexpr uint32_t RATE = 48000, FRAMES = 240;  // 5 ms a DMA block
constexpr float OUT_VOLTS = 9.72f;              // a sample of 1.0 at the jack: Rev A's outs read +4.86 V for 0.5
constexpr float IN_VPP = 22.0f;                 // the inputs' full scale at the jack, about 22 Vpp (and inverted)

// ---- state
static bool powered, exp_ready, adc_ready, dac_ready, spia_ready, spib_ready, audio_ready, leds_ready, midi_ready;
static uint8_t port0 = OE_N;  // TCA9555 output port 0: switches off, gate outputs disabled

static i2c_master_bus_handle_t i2c_bus;
static i2c_master_dev_handle_t dev_tca, dev_ee, dev_oled;
static spi_device_handle_t spi_conv, spi_panel;
static i2s_chan_handle_t i2s_tx, i2s_rx;
static rmt_channel_handle_t led_chan;
static rmt_encoder_handle_t led_enc;
constexpr int NUM_LEDS = 16;  // data for 16; a shorter chain shows the first few

static void delay_ms(uint32_t ms) { vTaskDelay(pdMS_TO_TICKS(ms ? ms : 1)); }
static uint32_t millis() { return (uint32_t)(esp_timer_get_time() / 1000); }

// ---- serial: UART0, the CH343 on the module's USB-C
static char line[48];

static bool read_line(uint32_t wait_ms = 10) {  // true once a whole line (possibly empty) is in `line`
  static uint8_t n = 0;
  uint8_t c;
  while (uart_read_bytes(UART_NUM_0, &c, 1, pdMS_TO_TICKS(wait_ms)) == 1) {
    wait_ms = 0;
    if (c == '\r' || c == '\n') {
      line[n] = 0;
      n = 0;
      return true;
    }
    if (c < 0x20 || c > 0x7E) continue;  // a stray byte from the USB bridge at reset is not a command
    if (n < sizeof(line) - 1) line[n++] = c;
  }
  return false;
}

static void drain() {
  delay_ms(5);
  uart_flush_input(UART_NUM_0);
}

static bool wait_enter(const char *prompt) {  // false if the answer starts with q
  drain();
  printf("  %s [Enter, or q to stop] ", prompt);
  while (!read_line()) {
  }
  printf("\n");
  return line[0] != 'q';
}

static bool enter_pressed() {
  size_t n = 0;
  uart_get_buffered_data_len(UART_NUM_0, &n);
  if (!n) return false;
  drain();
  return true;
}

static void verdict(bool ok, const char *what) { printf("  %s  %s\n", ok ? "PASS" : "FAIL", what); }

// ---- I2C devices
static bool i2c_present(uint8_t a) { return i2c_master_probe(i2c_bus, a, 10) == ESP_OK; }

static i2c_master_dev_handle_t i2c_dev(uint8_t a) {
  i2c_device_config_t c = {};
  c.dev_addr_length = I2C_ADDR_BIT_LEN_7;
  c.device_address = a;
  c.scl_speed_hz = 400000;
  i2c_master_dev_handle_t h = nullptr;
  i2c_master_bus_add_device(i2c_bus, &c, &h);
  return h;
}

static bool tca_write(uint8_t reg, uint8_t v) {
  const uint8_t b[2] = {reg, v};
  return i2c_master_transmit(dev_tca, b, 2, 20) == ESP_OK;
}

static bool tca_read(uint8_t reg, uint8_t &v) { return i2c_master_transmit_receive(dev_tca, &reg, 1, &v, 1, 20) == ESP_OK; }

static bool expander_start() {
  if (exp_ready) return true;
  // the output register first, so each pin comes up at that level as it turns into an output
  exp_ready = tca_write(TCA_OUT0, port0) && tca_write(TCA_CFG0, 0x80) && tca_write(TCA_CFG1, 0xFF);
  if (!exp_ready) printf("  The TCA9555 did not take its settings: run block 1.\n");
  return exp_ready;
}

static bool set_port0(uint8_t v) {
  port0 = v;
  return tca_write(TCA_OUT0, v);
}

static bool ee_write(uint16_t a, const uint8_t *d, uint8_t n) {  // n <= 16, inside one page
  uint8_t b[18] = {(uint8_t)(a >> 8), (uint8_t)(a & 0xFF)};
  memcpy(b + 2, d, n);
  if (i2c_master_transmit(dev_ee, b, n + 2, 20) != ESP_OK) return false;
  for (uint32_t t = millis(); millis() - t < 20;)  // no acknowledge until the write cycle (5 ms max) ends
    if (i2c_present(ADDR_EE)) return true;
  return false;
}

static bool ee_read(uint16_t a, uint8_t *d, uint8_t n) {
  const uint8_t b[2] = {(uint8_t)(a >> 8), (uint8_t)(a & 0xFF)};
  return i2c_master_transmit_receive(dev_ee, b, 2, d, n, 20) == ESP_OK;
}

// ---- SPI: chip selects driven by hand, as on Rev A (the 595's latch is a pulse after the word)
static void cs_output(gpio_num_t p) {
  gpio_set_level(p, 1);
  gpio_set_direction(p, GPIO_MODE_OUTPUT);
}

static spi_device_handle_t spi_start(spi_host_device_t host, gpio_num_t sck, gpio_num_t mosi, gpio_num_t miso, int hz,
                                     uint8_t mode) {
  spi_bus_config_t b = {};
  b.mosi_io_num = mosi;
  b.miso_io_num = miso;
  b.sclk_io_num = sck;
  b.quadwp_io_num = -1;
  b.quadhd_io_num = -1;
  b.max_transfer_sz = 4;
  spi_bus_initialize(host, &b, SPI_DMA_DISABLED);
  spi_device_interface_config_t d = {};
  d.mode = mode;
  d.clock_speed_hz = hz;
  d.spics_io_num = -1;
  d.queue_size = 1;
  spi_device_handle_t h = nullptr;
  spi_bus_add_device(host, &d, &h);
  return h;
}

static void spi_frame(spi_device_handle_t dev, gpio_num_t cs, const uint8_t *tx, uint8_t *rx, int bytes) {
  spi_transaction_t t = {};
  t.flags = SPI_TRANS_USE_TXDATA | SPI_TRANS_USE_RXDATA;
  t.length = bytes * 8;
  memcpy(t.tx_data, tx, bytes);
  if (cs != GPIO_NUM_NC) gpio_set_level(cs, 0);
  spi_device_polling_transmit(dev, &t);
  if (cs != GPIO_NUM_NC) gpio_set_level(cs, 1);
  if (rx) memcpy(rx, t.rx_data, bytes);
}

// ---- SPI-A: ADS8688 and DAC8568
static void spia_start() {
  if (spia_ready) return;
  cs_output(PIN_CS_ADC);
  cs_output(PIN_CS_DAC);
  spi_conv = spi_start(SPI2_HOST, PIN_SPIA_SCK, PIN_SPIA_MOSI, PIN_SPIA_MISO, SPI_CONV_HZ, 1);
  spia_ready = true;
}

// The ADS8688 changes SDO on SCLK's falling edge (datasheet §8.4.1.1.4), the edge a mode 1 master
// samples on, and holds the old bit for only 10 ns after it. The Teensy samples inside those 10 ns;
// the P4 samples after them, so it sees each bit one clock early, and the reply sits one bit higher
// in the frame than the datasheet draws it. Nothing is lost: the frame's last bit is spare. Block 4s
// checks the alignment at four clocks.
constexpr int ADC_EARLY = 1;

static uint32_t adc_raw(const uint8_t *tx, int bytes) {  // the whole frame as sampled, first bit highest
  uint8_t rx[4];
  spi_frame(spi_conv, PIN_CS_ADC, tx, rx, bytes);
  uint32_t w = 0;
  for (int i = 0; i < bytes; i++) w = (w << 8) | rx[i];
  return w;
}

static uint16_t adc_frame(uint16_t cmd) {  // 32 clocks: a command in, the previous frame's conversion out
  const uint8_t tx[4] = {(uint8_t)(cmd >> 8), (uint8_t)cmd, 0, 0};
  return (uint16_t)(adc_raw(tx, 4) >> ADC_EARLY);
}

static uint32_t adc_reg_raw(uint8_t reg, int val) {  // 24 clocks: read if val < 0; a write echoes the byte
  const uint16_t w = (reg << 9) | (val >= 0 ? 0x100 | val : 0);
  const uint8_t tx[3] = {(uint8_t)(w >> 8), (uint8_t)w, 0};
  return adc_raw(tx, 3);
}

static uint8_t adc_reg(uint8_t reg, int val = -1) { return (uint8_t)(adc_reg_raw(reg, val) >> ADC_EARLY); }

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
    printf("  Range register, channel 1: wrote 01, echoed %02X, read %02X; wrote 00, echoed %02X, read %02X\n", e1, r1,
           e0, r0);
  return e1 == 0x01 && r1 == 0x01 && e0 == 0x00 && r0 == 0x00;
}

static bool adc_start(bool print = false) {
  if (adc_ready && !print) return true;
  spia_start();
  bool ok = adc_echo(print);
  for (uint8_t ch = 0; ok && ch < 8; ch++) ok = adc_reg(0x05 + ch, 0x00) == 0x00 && adc_reg(0x05 + ch) == 0x00;  // ±10.24 V
  adc_ready = ok;
  if (!ok && !print) printf("  The ADS8688 is not answering: run block 4.\n");
  return ok;
}

static void dac_frame(uint32_t w) {
  const uint8_t tx[4] = {(uint8_t)(w >> 24), (uint8_t)(w >> 16), (uint8_t)(w >> 8), (uint8_t)w};
  spi_frame(spi_conv, PIN_CS_DAC, tx, nullptr, 4);
}

static void dac_write(uint8_t ch, uint16_t code) { dac_frame(0x03000000 | (ch << 20) | ((uint32_t)code << 4)); }  // write and update

static bool dac_start() {  // the start-up order of spec §15, firmware requirement 3
  if (dac_ready) return true;
  if (!expander_start() || !set_port0(port0 & ~SW_ALL)) return false;  // 1. every jack switch off
  spia_start();
  for (uint8_t ch = 0; ch < 8; ch++) dac_write(ch, DAC_ZERO);  // 2. 0 V codes while the reference is still off
  dac_frame(0x090A0000);                                       // 3. internal reference on: flexible mode, always on
  delay_ms(10);                                                // 4. settle
  dac_ready = true;  // 5 and 6 (targets, then switches) are each block's own; 7: never the software reset
  return true;
}

// ---- SPI-B: 74HCT595 and MCP3208
static void spib_start() {
  if (spib_ready) return;
  cs_output(PIN_CS_595);
  cs_output(PIN_CS_POT);
  spi_panel = spi_start(SPI3_HOST, PIN_SPIB_SCK, PIN_SPIB_MOSI, PIN_SPIB_MISO, SPI_PANEL_HZ, 0);
  spib_ready = true;
}

// the 595 shifts every panel-bus frame, so always a whole word before RCLK (requirement 14)
static void gates_write(uint8_t word) {  // bit 0 = gate out 1
  spi_frame(spi_panel, GPIO_NUM_NC, &word, nullptr, 1);
  gpio_set_level(PIN_CS_595, 0);  // RCLK: latches on the rising edge
  esp_rom_delay_us(1);
  gpio_set_level(PIN_CS_595, 1);
}

static uint16_t pot_read(uint8_t ch) {  // MCP3208, single-ended: start, SGL, D2-D0, then 12 bits
  const uint8_t tx[3] = {(uint8_t)(0x06 | (ch >> 2)), (uint8_t)((ch & 3) << 6), 0};
  uint8_t rx[3];
  spi_frame(spi_panel, PIN_CS_POT, tx, rx, 3);
  return ((rx[1] & 0x0F) << 8) | rx[2];
}

static uint8_t gate_ins() {
  uint8_t g = 0;
  for (int i = 0; i < 4; i++) g |= gpio_get_level(PIN_GATE_IN[i]) << i;
  return g;
}

// ---- audio: one task writes a block and reads a block, in step with the codec's frames
enum Shape { SINE, PULSE };
static volatile Shape wave_shape = SINE;
static volatile float wave_amp[2], wave_freq = 440, wave_width = 0.5f, wave_offset;
static volatile int cap_left;  // samples still to capture; the task counts it down
static volatile int cap_min[2], cap_max[2];

static void audio_task(void *) {
  static int32_t out[FRAMES * 2], in[FRAMES * 2];
  float phase = 0;
  for (;;) {
    const float inc = wave_freq / RATE;
    for (uint32_t i = 0; i < FRAMES; i++) {
      float s = wave_shape == SINE ? sinf(2 * (float)M_PI * phase) : (phase < wave_width ? 1.0f : -1.0f);
      for (int c = 0; c < 2; c++) {
        float v = wave_offset + wave_amp[c] * s;
        v = v > 0.999f ? 0.999f : v < -0.999f ? -0.999f : v;
        out[2 * i + c] = (int32_t)(v * 8388607) * 256;  // 24 bits at the top of the 32-bit slot
      }
      phase += inc;
      if (phase >= 1) phase -= 1;
    }
    size_t n = 0;
    i2s_channel_write(i2s_tx, out, sizeof(out), &n, portMAX_DELAY);
    i2s_channel_read(i2s_rx, in, sizeof(in), &n, portMAX_DELAY);
    int left = cap_left;
    if (left > 0) {
      for (uint32_t i = 0; i < n / 8 && left > 0; i++, left--)
        for (int c = 0; c < 2; c++) {
          int s = in[2 * i + c] >> 16;  // the top 16 of the codec's 24 bits
          if (s < cap_min[c]) cap_min[c] = s;
          if (s > cap_max[c]) cap_max[c] = s;
        }
      cap_left = left;
    }
  }
}

static void audio_start() {
  if (audio_ready) return;
  i2s_chan_config_t cc = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
  cc.dma_desc_num = 4;
  cc.dma_frame_num = FRAMES;
  cc.auto_clear = true;
  i2s_new_channel(&cc, &i2s_tx, &i2s_rx);
  i2s_std_config_t sc = {
      .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(RATE),
      .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_STEREO),
      .gpio_cfg = {.mclk = PIN_MCLK, .bclk = PIN_BCK, .ws = PIN_LRCK, .dout = PIN_I2S_DOUT, .din = PIN_I2S_DIN,
                   .invert_flags = {}},
  };
  sc.clk_cfg.clk_src = I2S_CLK_SRC_APLL;  // 12.288 MHz exactly; the APLL is then not free for video
  i2s_channel_init_std_mode(i2s_tx, &sc);
  i2s_channel_init_std_mode(i2s_rx, &sc);
  i2s_channel_enable(i2s_tx);
  i2s_channel_enable(i2s_rx);
  xTaskCreatePinnedToCore(audio_task, "audio", 4096, nullptr, 10, nullptr, 1);
  audio_ready = true;
}

static void capture(int samples, int mn[2], int mx[2]) {  // the extremes of each input over `samples` frames
  for (int c = 0; c < 2; c++) {
    cap_min[c] = 32767;
    cap_max[c] = -32768;
  }
  cap_left = samples;
  for (uint32_t t = millis(); cap_left > 0 && millis() - t < 2000;) delay_ms(5);
  cap_left = 0;
  for (int c = 0; c < 2; c++) {
    mn[c] = cap_min[c];
    mx[c] = cap_max[c];
  }
}

static void wave(Shape shape, float amp_l, float amp_r, float freq = 440, float width = 0.5f, float offset = 0) {
  wave_shape = shape;
  wave_freq = freq;
  wave_width = width;
  wave_offset = offset;
  wave_amp[0] = amp_l;
  wave_amp[1] = amp_r;
}

static float vpp(int mn, int mx) { return (mx - mn) / 65536.0f * IN_VPP; }

// ---- LEDs: WS2812 on RMT at 10 MHz
static void leds_start() {
  if (leds_ready) return;
  rmt_tx_channel_config_t tc = {};
  tc.gpio_num = PIN_LED_DATA;
  tc.clk_src = RMT_CLK_SRC_DEFAULT;
  tc.resolution_hz = 10000000;
  tc.mem_block_symbols = SOC_RMT_MEM_WORDS_PER_CHANNEL;
  tc.trans_queue_depth = 2;
  rmt_new_tx_channel(&tc, &led_chan);
  rmt_bytes_encoder_config_t ec = {};
  ec.bit0.level0 = 1, ec.bit0.duration0 = 3, ec.bit0.level1 = 0, ec.bit0.duration1 = 9;  // 0.3 µs high, 0.9 low
  ec.bit1.level0 = 1, ec.bit1.duration0 = 9, ec.bit1.level1 = 0, ec.bit1.duration1 = 3;  // 0.9 µs high, 0.3 low
  ec.flags.msb_first = 1;
  rmt_new_bytes_encoder(&ec, &led_enc);
  rmt_enable(led_chan);
  leds_ready = true;
}

static void leds_show(const uint32_t *rgb) {  // NUM_LEDS colours, 0xRRGGBB
  static uint8_t grb[NUM_LEDS * 3];
  for (int i = 0; i < NUM_LEDS; i++) {
    grb[3 * i] = rgb[i] >> 8, grb[3 * i + 1] = rgb[i] >> 16, grb[3 * i + 2] = rgb[i];
  }
  rmt_transmit_config_t t = {};
  rmt_transmit(led_chan, led_enc, grb, sizeof(grb), &t);
  rmt_tx_wait_all_done(led_chan, 100);
  esp_rom_delay_us(300);  // the latch: the line low for 280 µs or more
}

static void leds_fill(uint32_t rgb) {
  uint32_t c[NUM_LEDS];
  for (int i = 0; i < NUM_LEDS; i++) c[i] = rgb;
  leds_show(c);
}

// ---- blocks
static void block_i2c() {
  printf("Block 1, I2C: scanning 0x08-0x77 at 400 kHz (SDA GPIO31, SCL GPIO30)\n");
  bool tca = false, ee = false;
  for (uint8_t a = 0x08; a < 0x78; a++) {
    if (!i2c_present(a)) continue;
    printf("  0x%02X  %s\n", a,
           a == ADDR_TCA ? "TCA9555 expander" : a == ADDR_EE ? "M24C64 EEPROM" : (a == 0x3C || a == 0x3D) ? "an OLED?" : "");
    tca |= a == ADDR_TCA;
    ee |= a == ADDR_EE;
  }
  powered = ee;
  verdict(tca && ee, "0x20 (TCA9555) and 0x50 (M24C64) answer");
}

static void block_eeprom() {
  printf("Block 2, EEPROM: flip every bit of the last page (0x1FE0), read it back, then restore it\n");
  uint8_t old[32], pat[32], got[32];
  if (!ee_read(EE_TEST, old, 32)) {
    verdict(false, "the M24C64 did not answer a read");
    return;
  }
  for (int i = 0; i < 32; i++) pat[i] = ~old[i];
  bool ok = ee_write(EE_TEST, pat, 16) && ee_write(EE_TEST + 16, pat + 16, 16) && ee_read(EE_TEST, got, 32);
  int bad = 0;
  for (int i = 0; i < 32; i++) bad += got[i] != pat[i];
  bool back = ee_write(EE_TEST, old, 16) && ee_write(EE_TEST + 16, old + 16, 16) && ee_read(EE_TEST, got, 32) &&
              memcmp(got, old, 32) == 0;
  printf("  32 bytes written, %d read back wrong; the old bytes %s\n", ok ? bad : 32, back ? "restored" : "NOT restored");
  verdict(ok && bad == 0 && back, "the same bytes come back");
}

static void print_buttons(uint8_t in1) {
  bool any = false;
  for (int i = 0; i < 6; i++)
    if (!(in1 & (1 << i))) {
      if (SW_NAME[i][0] == '-')
        printf(" SW%d", i + 1);
      else
        printf(" SW%d (%s)", i + 1, SW_NAME[i]);
      any = true;
    }
  if (!any) printf(" none");
}

static void block_expander() {
  printf("Block 3, expander: switches off and gate outputs disabled, then read both ports\n");
  if (!expander_start()) return;
  uint8_t out0 = 0, cfg0 = 0, cfg1 = 0, in0 = 0, in1 = 0;
  bool regs = tca_read(TCA_OUT0, out0) && tca_read(TCA_CFG0, cfg0) && tca_read(TCA_CFG1, cfg1);
  printf("  Output port 0 %02X, config %02X %02X (want %02X, 80 FF)\n", out0, cfg0, cfg1, port0);
  regs = regs && out0 == port0 && cfg0 == 0x80 && cfg1 == 0xFF;
  regs = regs && tca_read(TCA_IN0, in0) && tca_read(TCA_IN1, in1);
  printf("  Switch enables %s, GATE_OE_N %s\n", (in0 & SW_ALL) ? "SOME ON" : "all off", (in0 & OE_N) ? "high" : "LOW");
  printf("  Buttons pressed now:");
  print_buttons(in1);
  printf("\n");
  verdict(regs && (in0 & (SW_ALL | OE_N)) == (port0 & (SW_ALL | OE_N)), "the expander reads back what it was given");
  printf("  Now live: press each button. Enter to stop\n");
  drain();
  uint8_t last = in1 & BTN_ALL;
  while (!enter_pressed()) {
    if (tca_read(TCA_IN1, in1) && (in1 & BTN_ALL) != last) {
      last = in1 & BTN_ALL;
      printf("  pressed:");
      print_buttons(in1);
      printf("\n");
    }
    delay_ms(20);  // polled: Rev B has no INT line
  }
}

static void block_adc() {
  printf("Block 4, ADC: ADS8688 registers, then the eight inputs on ±10.24 V\n");
  bool regs = adc_start(true);
  verdict(regs, "the ADS8688 echoes its registers");
  if (!regs) {
    printf("  Look at SPI-A (GPIO46 SCK, 33 MOSI, 32 MISO, 47 CS_ADC), LDO channel 4, and +5VA, +3V3D at the chip.\n");
    return;
  }
  bool ok = true;
  for (uint8_t ch = 0; ch < 8; ch++) {
    float v = adc_read(ch, 64);
    bool tied = ch == 7;  // AIN_7 goes to ground on this board
    bool good = tied ? fabsf(v) < 0.02f : (v > 0.1f && v < 0.3f);
    ok &= good;
    if (tied)
      printf("  AIN7 %+.3f V  tied to ground: 0 V\n", v);
    else if (ch == 6)
      printf("  CVI7 %+.3f V  open: about %+.2f V (the ADC's bias against 100 kOhm)%s\n", v, VBIAS, good ? "" : "  <- patched, or a fault");
    else
      printf("  CV%u (%s) %+.3f V  open: about %+.2f V%s\n", ch + 1, CV_NAME[ch], v, VBIAS, good ? "" : "  <- patched, or a fault");
  }
  verdict(ok, "open inputs read +0.1 to +0.3 V, the grounded one within 20 mV of 0");
}

static bool spi_conv_clock(int hz) {  // SPI-A's device again at another clock, mode 1
  spi_bus_remove_device(spi_conv);
  spi_device_interface_config_t d = {};
  d.mode = 1;
  d.clock_speed_hz = hz;
  d.spics_io_num = -1;
  d.queue_size = 1;
  return spi_bus_add_device(SPI2_HOST, &d, &spi_conv) == ESP_OK;
}

// how the ADS8688's reply lines up on the P4, at four clocks: 256 bytes written to AUTO_SEQ_EN and read
// back, counted both ways, and 256 conversions of the open CVI7, whose spread stays small only if every
// bit is sampled cleanly
static void block_adc_timing() {
  printf("Block 4s, ADC timing: 256 bytes through AUTO_SEQ_EN and 256 conversions of CVI7 at each clock\n");
  spia_start();
  const int clocks[] = {1000000, 4000000, 8000000, 16000000};
  for (int hz : clocks) {
    if (!spi_conv_clock(hz)) {
      printf("  %2d MHz: the driver refused this clock\n", hz / 1000000);
      continue;
    }
    int khz = 0;
    spi_device_get_actual_freq(spi_conv, &khz);
    int early_echo = 0, early_read = 0, drawn_echo = 0, drawn_read = 0;
    for (int p = 0; p < 256; p++) {
      const uint32_t e = adc_reg_raw(0x01, p), r = adc_reg_raw(0x01, -1);
      early_echo += ((e >> 1) & 0xFF) == (uint32_t)p;
      early_read += ((r >> 1) & 0xFF) == (uint32_t)p;
      drawn_echo += (e & 0xFF) == (uint32_t)p;
      drawn_read += (r & 0xFF) == (uint32_t)p;
    }
    adc_reg_raw(0x01, 0xFF);  // its default
    adc_frame(0xC000 | (6 << 10));  // CVI7
    adc_frame(0x0000);
    uint16_t lo = 0xFFFF, hi = 0;
    uint32_t sum = 0;
    for (int i = 0; i < 256; i++) {
      const uint16_t c = adc_frame(0x0000);
      lo = c < lo ? c : lo;
      hi = c > hi ? c : hi;
      sum += c;
    }
    printf("  %5.2f MHz: one bit early %3d/256 echoed, %3d/256 read; as drawn %3d, %3d. CVI7 %+.3f V, spread %u codes\n",
           khz / 1000.0f, early_echo, early_read, drawn_echo, drawn_read, ((float)sum / 256 - 32768) * 20.48f / 65536,
           hi - lo);
  }
  spi_conv_clock(SPI_CONV_HZ);
  printf("  Back at %d MHz.\n", SPI_CONV_HZ / 1000000);
}

// one channel out through the DAC and back in through the ADC, from -10 to +10 V in 2.5 V steps
static bool cv_sweep(uint8_t dac_ch, uint8_t adc_ch, bool switched, float (*expected)(float), float &lo, float &zero,
                     float &hi, float &worst, float &off) {
  off = NAN;
  if (switched) {
    dac_write(dac_ch, 65535);  // switch off: full scale must not reach the jack
    delay_ms(3);
    off = adc_read(adc_ch, 32);
    dac_write(dac_ch, DAC_ZERO);  // the channel holds 0 V before its switch closes (requirement 3.6)
    delay_ms(3);
    set_port0(port0 | (1 << dac_ch));
    delay_ms(5);
  }
  worst = 0;
  float prev = -100;
  bool rising = true;
  for (int k = -4; k <= 4; k++) {  // the ADS8688's ±10.24 V can't read the ends, -10.71 and +10.54 V
    const uint16_t c = cv_code(2.5f * k);
    dac_write(dac_ch, c);
    delay_ms(3);
    float v = adc_read(adc_ch, 32), err = v - expected(cv_out_volts(c));
    if (fabsf(err) > fabsf(worst)) worst = err;
    rising &= v > prev;
    prev = v;
    if (k == -4) lo = v;
    if (k == 0) zero = v;
    if (k == 4) hi = v;
  }
  dac_write(dac_ch, DAC_ZERO);
  delay_ms(3);
  if (switched) set_port0(port0 & ~(1 << dac_ch));
  return rising && fabsf(worst) < 0.2f && (!switched || fabsf(off - VBIAS) < 0.1f);
}

static void block_dac(const char *args) {
  const bool seven = atoi(args) == 7;
  float lo, zero, hi, worst, off;
  if (seven) {
    printf("Block 5 7, CVO7 into CVI7: the fixed CV out, read by the fixed CV in\n");
    if (!wait_enter("A wire from the CVO7 hole to the CVI7 hole?")) return;
    if (!adc_start() || !dac_start()) return;
    bool ok = cv_sweep(6, 6, false, cv7_read_expected, lo, zero, hi, worst, off);
    printf("  CVO7  %+.3f V at -10 V, %+.3f V at 0 V, %+.3f V at +10 V; worst error %+4.0f mV\n", lo, zero, hi, worst * 1000);
    verdict(ok, "it rises with the code, within 0.2 V of the design");
    return;
  }
  printf("Block 5, DAC to ADC: each of CV1-6 out through its jack switch and back into the ADC\n");
  if (!wait_enter("Nothing patched into X1-Z2 (CV1-6)?")) return;
  if (!adc_start() || !dac_start()) return;
  bool all = true;
  for (uint8_t ch = 0; ch < 6; ch++) {
    bool ok = cv_sweep(ch, ch, true, cv_read_expected, lo, zero, hi, worst, off);
    all &= ok;
    printf("  CV%u (%s)  %+.3f V at -10 V, %+.3f V at 0 V, %+.3f V at +10 V; worst error %+4.0f mV; switch off %+.3f V  %s\n",
           ch + 1, CV_NAME[ch], lo, zero, hi, worst * 1000, off, ok ? "PASS" : "FAIL");
  }
  printf("  Design: %+.2f to %+.2f V from the op-amp, 0 V at code %u, read about 2%% low through the 2 kOhm to the ADC.\n",
         cv_out_volts(0), cv_out_volts(65535), DAC_ZERO);
  verdict(all, "every channel rises with the code, within 0.2 V of the design, and is cut off by its switch");
}

static void block_codec() {
  printf("Block 6, codec clocks: I2S at 48 kHz, MCLK 256 fs from the APLL\n");
  audio_start();
  printf("  Running: MCLK 12.288 MHz on header pin 27, BCK 3.072 MHz on pin 31, LRCK 48 kHz on pin 32.\n");
  printf("  On DC volts each reads about 1.65 V at the module socket; a meter that counts Hz shows the rate instead.\n");
  int mn[2], mx[2];
  capture(RATE / 10, mn, mx);
  printf("  0.1 s from the codec's ADC: AIN1 %d to %d, AIN2 %d to %d (16-bit codes)\n", mn[0], mx[0], mn[1], mx[1]);
  bool alive = mn[0] || mx[0] || mn[1] || mx[1];
  printf(alive ? "  The codec is sending samples.\n"
               : "  Every sample is exactly 0: the codec may not be running (MCLK, CODEC_RST, +5VA and +3V3D at U301).\n");
}

static void block_gate_outs() {
  printf("Block 7, gate outs: shift and latch a word, then GATE_OE_N low\n");
  if (!expander_start()) return;
  spib_start();
  gates_write(0);  // a whole word latched before the outputs turn on (requirement 4)
  set_port0(port0 & ~OE_N);
  const uint8_t words[] = {0x5, 0xA, 0xF, 0x0};
  for (uint8_t w : words) {
    gates_write(w);
    delay_ms(2);
    printf("  Now:");
    for (int i = 0; i < 4; i++) printf("  GOUT%d %s", i + 1, (w >> i) & 1 ? "5 V" : "0 V");
    uint8_t g = gate_ins();
    printf("   (gate ins read %d%d%d%d%s)\n", g & 1, (g >> 1) & 1, (g >> 2) & 1, (g >> 3) & 1,
           g == w ? ": the same, if GOUT1-4 are wired to GIN1-4" : "");
    if (!wait_enter("Measure at the gate-out holes, then")) break;
  }
  gates_write(0);
  set_port0(port0 | OE_N);
  printf("  Gate outputs low and disabled again.\n");
}

static volatile uint32_t gate_rises[4];
static void IRAM_ATTR gate_isr(void *arg) {
  const int i = (int)(intptr_t)arg;
  gate_rises[i] = gate_rises[i] + 1;
}

static void block_gate_ins() {
  printf("Block 8, gate ins: live state and rising edges, Enter to stop\n");
  printf(" ");
  for (int i = 0; i < 4; i++) printf("  GIN%d %-13s", i + 1, GIN_NAME[i]);
  printf("\n");
  static bool isr_service;
  if (!isr_service) isr_service = gpio_install_isr_service(0) == ESP_OK;
  for (int i = 0; i < 4; i++) {
    gate_rises[i] = 0;
    gpio_set_intr_type(PIN_GATE_IN[i], GPIO_INTR_POSEDGE);
    gpio_isr_handler_add(PIN_GATE_IN[i], gate_isr, (void *)(intptr_t)i);
    gpio_intr_enable(PIN_GATE_IN[i]);
  }
  drain();
  while (!enter_pressed()) {
    printf("\r ");
    for (int i = 0; i < 4; i++)
      printf("  GIN%d %s %8lu", i + 1, gpio_get_level(PIN_GATE_IN[i]) ? "HIGH" : "low ", (unsigned long)gate_rises[i]);
    delay_ms(100);
  }
  for (int i = 0; i < 4; i++) {
    gpio_isr_handler_remove(PIN_GATE_IN[i]);
    gpio_set_intr_type(PIN_GATE_IN[i], GPIO_INTR_DISABLE);
  }
  printf("\n");
}

static void block_gate_threshold(int n) {
  printf("Block 8t, gate in %d threshold: sweep CV1 0 to 3 V and back into GIN%d\n", n, n);
  if (n < 1 || n > 4) {
    printf("  Which gate in? 8t 1 to 8t 4.\n");
    return;
  }
  printf("  Patch X1 (CV1) into the gate in's jack (GIN3 is RST, GIN4 CLK), or wire the CV1 hole to GIN%d.\n", n);
  if (!wait_enter("Nothing else on CV1. Ready?")) return;
  if (!adc_start() || !dac_start()) return;
  const gpio_num_t pin = PIN_GATE_IN[n - 1];
  const uint16_t top = cv_code(3.0f);
  dac_write(0, DAC_ZERO);
  set_port0(port0 | 0x01);
  delay_ms(5);
  float up = NAN, down = NAN;
  for (uint32_t c = DAC_ZERO; c <= top && isnan(up); c += 12) {  // 12 codes: about 4 mV at the jack
    dac_write(0, c);
    esp_rom_delay_us(300);
    if (gpio_get_level(pin)) up = jack_from_adc(adc_read(0, 8));
  }
  dac_write(0, top);
  delay_ms(3);
  for (int32_t c = top; c >= DAC_ZERO && isnan(down); c -= 12) {
    dac_write(0, c);
    esp_rom_delay_us(300);
    if (!gpio_get_level(pin)) down = jack_from_adc(adc_read(0, 8));
  }
  dac_write(0, DAC_ZERO);
  delay_ms(3);
  set_port0(port0 & ~0x01);
  printf("  GIN%d goes high at %.2f V rising and low at %.2f V falling (design 1.98 and 1.67)\n", n, up, down);
  verdict(fabsf(up - 1.98f) < 0.15f && fabsf(down - 1.67f) < 0.15f, "both within 0.15 V of the design");
}

static void block_pots() {
  printf("Block 9, pots: MCP3208 CH0-5 = POT1-6, CH6-7 tied to ground. Enter to stop\n");
  printf("  On Health: X on POT4, Y on POT2, Z on POT6\n");
  spib_start();
  drain();
  while (!enter_pressed()) {
    printf("\r ");
    for (int ch = 0; ch < 8; ch++) printf(" %s%d %4u", ch < 6 ? "POT" : "CH", ch < 6 ? ch + 1 : ch, pot_read(ch));
    delay_ms(100);
  }
  printf("\n  Each pot should sweep 0 to 4095; an unwired one reads near 0, a wire from POT_REF reads 4095.\n");
}

static void block_audio() {
  printf("Block 10, audio: a 440 Hz sine on AOUT1 (OUT-L) and AOUT2 (OUT-R) at about 10 Vpp, half the 20 Vpp full scale\n");
  audio_start();
  wave(SINE, 0.5f, 0.5f);
  printf("  On AC volts AOUT1 and AOUT2 read about 3.4 V. Listen through the rack, or record it on the ES-10.\n");
  if (!wait_enter("For the inputs, patch OUT-L into IN-L and OUT-R into IN-R (AOUT1-2 to AIN1-2), then")) return;
  bool level = true, inverted = true;
  int mn[2], mx[2];
  capture(RATE / 10, mn, mx);
  for (int i = 0; i < 2; i++) {
    float v = vpp(mn[i], mx[i]);
    level &= v > 8 && v < 12;
    printf("  AIN%d (%s): %.1f Vpp of the 10 sent\n", i + 1, AIN_NAME[i], v);
  }
  // the inputs invert (requirement 6): a narrow pulse, made lopsided by the AC coupling, shows which way
  wave(PULSE, 0.25f, 0.25f, 100, 0.1f);
  delay_ms(600);  // the coupling capacitors settle
  capture(RATE / 10, mn, mx);
  for (int i = 0; i < 2; i++) {
    bool inv = -mn[i] > mx[i];
    inverted &= inv;
    printf("  AIN%d with a 10%% pulse: peaks %+d and %+d: %s\n", i + 1, mx[i], mn[i], inv ? "inverted" : "not inverted");
  }
  wave(SINE, 0.5f, 0.5f);
  verdict(level, "the inputs read 8 to 12 Vpp of the 10 Vpp sent");
  verdict(inverted, "the loop inverts, as designed: firmware negates the input samples");

  // Health's deck normals IN-R from IN-L: one cable into IN-L feeds both, until a plug goes into IN-R
  if (wait_enter("IN-R's normal: patch OUT-L into IN-L alone, nothing in IN-R, then")) {
    wave(SINE, 0.5f, 0);  // the sine on OUT-L only; OUT-R silent
    delay_ms(50);
    capture(RATE / 10, mn, mx);
    float l = vpp(mn[0], mx[0]), r = vpp(mn[1], mx[1]);
    printf("  IN-L %.1f Vpp, IN-R %.1f Vpp\n", l, r);
    verdict(l > 8 && r > 8, "IN-R hears IN-L's cable through the normal");
    if (wait_enter("Now patch the silent OUT-R into IN-R, then")) {
      capture(RATE / 10, mn, mx);
      l = vpp(mn[0], mx[0]), r = vpp(mn[1], mx[1]);
      printf("  IN-L %.1f Vpp, IN-R %.1f Vpp\n", l, r);
      verdict(l > 8 && r < 0.5f, "the plug in IN-R lifts the normal: IN-R hears only its own cable");
    }
    wave(SINE, 0.5f, 0.5f);
  }
  printf("  The sine stays on until 0.\n");
}

static void block_leds() {
  printf("Block 11, LEDs: WS2812 on the LED holes, at about a tenth of full brightness\n");
  leds_start();
  const uint32_t colours[] = {0x180000, 0x001800, 0x000018, 0x101010};  // about 3 mA a LED at most (requirement 15)
  const char *names[] = {"red", "green", "blue", "white"};
  for (int k = 0; k < 4; k++) {
    leds_fill(colours[k]);
    printf("  All %s\n", names[k]);
    delay_ms(1000);
  }
  printf("  One dot running along the chain, Enter to stop\n");
  drain();
  uint32_t c[NUM_LEDS];
  for (int i = 0; !enter_pressed(); i = (i + 1) % NUM_LEDS) {
    for (int j = 0; j < NUM_LEDS; j++) c[j] = j == i ? 0x101010 : 0;
    leds_show(c);
    delay_ms(150);
  }
  leds_fill(0);
}

static void block_encoder(const char *args) {
  int a = 1, b = 2;  // Health: MENU A on GIN1, B on GIN2, its common on +3V3D, the push on SW6
  if (sscanf(args, "%d %d", &a, &b) != 2) a = 1, b = 2;
  if (a < 1 || a > 4 || b < 1 || b > 4 || a == b) {
    printf("  Which gate ins? 12 1 2 puts A on GIN1 and B on GIN2.\n");
    return;
  }
  printf("Block 12, encoder: A on GIN%d, B on GIN%d (PCNT, quadrature), common to +3V3D; buttons polled\n", a, b);
  if (!expander_start()) return;
  pcnt_unit_config_t uc = {};
  uc.low_limit = -30000;
  uc.high_limit = 30000;
  pcnt_unit_handle_t unit = nullptr;
  pcnt_new_unit(&uc, &unit);
  pcnt_glitch_filter_config_t fc = {};
  fc.max_glitch_ns = 1000;  // against contact bounce; the LM393s' hysteresis does most of it
  pcnt_unit_set_glitch_filter(unit, &fc);
  pcnt_chan_config_t ca = {}, cb = {};
  ca.edge_gpio_num = PIN_GATE_IN[a - 1], ca.level_gpio_num = PIN_GATE_IN[b - 1];
  cb.edge_gpio_num = PIN_GATE_IN[b - 1], cb.level_gpio_num = PIN_GATE_IN[a - 1];
  pcnt_channel_handle_t cha = nullptr, chb = nullptr;
  pcnt_new_channel(unit, &ca, &cha);
  pcnt_new_channel(unit, &cb, &chb);
  pcnt_channel_set_edge_action(cha, PCNT_CHANNEL_EDGE_ACTION_DECREASE, PCNT_CHANNEL_EDGE_ACTION_INCREASE);
  pcnt_channel_set_level_action(cha, PCNT_CHANNEL_LEVEL_ACTION_KEEP, PCNT_CHANNEL_LEVEL_ACTION_INVERSE);
  pcnt_channel_set_edge_action(chb, PCNT_CHANNEL_EDGE_ACTION_INCREASE, PCNT_CHANNEL_EDGE_ACTION_DECREASE);
  pcnt_channel_set_level_action(chb, PCNT_CHANNEL_LEVEL_ACTION_KEEP, PCNT_CHANNEL_LEVEL_ACTION_INVERSE);
  pcnt_unit_enable(unit);
  pcnt_unit_clear_count(unit);
  pcnt_unit_start(unit);
  printf("  Turn it both ways and press it. Enter to stop\n");
  drain();
  int last = 0x7FFFFFFF;
  uint8_t last_btn = BTN_ALL;
  while (!enter_pressed()) {
    int c = 0;
    pcnt_unit_get_count(unit, &c);
    uint8_t in1 = 0xFF;
    tca_read(TCA_IN1, in1);
    in1 &= BTN_ALL;
    if (c != last || in1 != last_btn) {
      printf("  count %d (%d detents)", c, c / 4);
      if (in1 != BTN_ALL) {
        printf("  pressed:");
        print_buttons(in1);
      }
      printf("\n");
      last = c;
      last_btn = in1;
    }
    delay_ms(20);  // polled: Rev B has no INT line (requirement 13)
  }
  pcnt_unit_stop(unit);
  pcnt_unit_disable(unit);
  pcnt_del_channel(cha);
  pcnt_del_channel(chb);
  pcnt_del_unit(unit);
}

static void block_midi() {
  printf("Block 13, MIDI: UART1 at 31 250 baud, TX GPIO52 (pin 1), RX GPIO51 (pin 2); Health has no MIDI jack\n");
  if (!midi_ready) {
    uart_config_t c = {};
    c.baud_rate = 31250;
    c.data_bits = UART_DATA_8_BITS;
    c.parity = UART_PARITY_DISABLE;
    c.stop_bits = UART_STOP_BITS_1;
    c.flow_ctrl = UART_HW_FLOWCTRL_DISABLE;
    c.source_clk = UART_SCLK_DEFAULT;
    uart_driver_install(UART_NUM_1, 256, 0, 0, nullptr, 0);
    uart_param_config(UART_NUM_1, &c);
    uart_set_pin(UART_NUM_1, PIN_MIDI_TX, PIN_MIDI_RX, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    midi_ready = true;
  }
  uart_flush_input(UART_NUM_1);
  const uint8_t msg[] = {0x90, 0x3C, 0x64, 0x80, 0x3C, 0x00, 0xB0, 0x07, 0x55, 0xF8};
  int good = 0;
  for (uint8_t b : msg) {
    uart_write_bytes(UART_NUM_1, &b, 1);
    uint8_t r;
    good += uart_read_bytes(UART_NUM_1, &r, 1, pdMS_TO_TICKS(10)) == 1 && r == b;
  }
  printf("  Loop test: %d of %d bytes came back\n", good, (int)sizeof(msg));
  verdict(good == (int)sizeof(msg), "bytes in = bytes out, with a TRS cable from OUT to IN");
  printf("  Now showing whatever arrives at IN; play some notes. Enter to stop\n");
  drain();
  int n = 0;
  while (!enter_pressed()) {
    uint8_t b;
    while (uart_read_bytes(UART_NUM_1, &b, 1, pdMS_TO_TICKS(10)) == 1) {
      if (b >= 0x80 && n) printf("\n"), n = 0;
      printf(" %02X", b);
      n++;
    }
  }
  printf("\n");
}

// ---- the screen: an I2C OLED at 0x3C on the board's I2C. Boy's is a 128x32 SSD1306, so that is the
// default, set up with the Adafruit library's values. Page addressing also suits an SH1106, whose RAM
// is 132 columns wide, so its glass starts at column 2
static bool oled_cmds(const uint8_t *c, size_t n) {
  uint8_t b[32] = {0x00};  // control byte: commands follow
  memcpy(b + 1, c, n);
  return i2c_master_transmit(dev_oled, b, n + 1, 50) == ESP_OK;
}

static bool oled_page(uint8_t page, uint8_t col0, const uint8_t *row) {  // 8 pixel rows by 128 columns
  const uint8_t at[] = {(uint8_t)(0xB0 | page), (uint8_t)(col0 & 0x0F), (uint8_t)(0x10 | (col0 >> 4))};
  if (!oled_cmds(at, sizeof(at))) return false;
  uint8_t b[129] = {0x40};  // control byte: data follows
  memcpy(b + 1, row, 128);
  return i2c_master_transmit(dev_oled, b, sizeof(b), 50) == ESP_OK;
}

static void block_screen(bool sh1106, uint8_t rows) {
  printf("Block 14, screen: 128x%d OLED at 0x3C, driven as an %s\n", rows, sh1106 ? "SH1106" : "SSD1306");
  if (!i2c_present(ADDR_OLED)) {
    printf("  Nothing answers at 0x3C: check SDA, SCL and 3V3 to the screen, and its GND to D.\n");
    return;
  }
  const bool tall = rows == 64;
  const uint8_t init[] = {
      0xAE,                                   // display off
      0xD5, 0x80, 0xA8, (uint8_t)(rows - 1),  // clock; rows
      0xD3, 0x00, 0x40,                       // no offset; start line 0
      sh1106 ? (uint8_t)0xAD : (uint8_t)0x8D, sh1106 ? (uint8_t)0x8B : (uint8_t)0x14,  // its own DC-DC or charge pump on
      0xA1, 0xC8,                             // the library's orientation
      0xDA, (uint8_t)(tall ? 0x12 : 0x02),    // COM pins: alternate for 64 rows, sequential for 32
      0x81, (uint8_t)(tall ? 0xCF : 0x8F), 0xD9, 0xF1, 0xDB, 0x40,  // contrast, pre-charge, VCOMH, as the library sets them
      0xA6, 0xA5, 0xAF};                      // not inverted; every pixel on, whatever the RAM holds; display on
  const uint8_t ssd1306_only[] = {0x20, 0x02, 0x2E};  // page addressing; scrolling off
  if (!oled_cmds(init, sizeof(init)) || (!sh1106 && !oled_cmds(ssd1306_only, sizeof(ssd1306_only)))) {
    printf("  The screen stopped answering during set-up.\n");
    return;
  }
  printf("  Every pixel on for 3 s: any dark spot or line is a fault in the panel.\n");
  delay_ms(3000);
  // a border round the edge and a filled square at the left, the header pins' end
  const uint8_t col0 = sh1106 ? 2 : 0, pages = rows / 8;
  uint8_t row[128];
  bool ok = true;
  for (uint8_t p = 0; p < pages && ok; p++) {
    for (int x = 0; x < 128; x++) {
      uint8_t b = (p == 0 ? 0x01 : 0) | (p == pages - 1 ? 0x80 : 0);  // top and bottom edges
      if (x == 0 || x == 127) b = 0xFF;                                 // left and right edges
      if (p >= 1 && p <= 2 && x >= 8 && x < 24) b = 0xFF;              // the square: 16 x 16
      row[x] = b;
    }
    ok = oled_page(p, col0, row);
  }
  const uint8_t show_ram = 0xA4;
  ok = ok && oled_cmds(&show_ram, 1);
  printf(ok ? "  Now a border round the edge and a filled square at the left. It stays until a restart.\n"
            : "  The screen stopped answering while the pattern was sent.\n");
  if (ok)
    printf("  Every other row missing or the picture stretched? Try %s. Left edge missing? Try 14 sh.\n",
           tall ? "14 (128x32)" : "14 64 (128x64)");
}

// ---- camera and display: their ribbons carry 3V3, ground and the P4 board's own I2C (GPIO7 SDA, GPIO8 SCL,
// 2.2 kΩ pull-ups on the board), which the analogue board leaves alone (P4_SCL and P4_SDA go only to two
// holes). So each chip answering there shows its ribbon's power, ground and I2C conductors work; the MIPI
// lanes are not tested. Nothing is configured and no video is sent: the bridge stays as it powered up.
constexpr uint8_t ADDR_CODEC = 0x18, ADDR_CAM = 0x36, ADDR_LT_MAIN = 0x48, ADDR_LT_CEC = 0x49, ADDR_LT_AVI = 0x4A,
                  ADDR_EDID = 0x50;
static i2c_master_bus_handle_t p4_bus;

static i2c_master_dev_handle_t p4_dev(uint8_t a) {
  i2c_device_config_t c = {};
  c.dev_addr_length = I2C_ADDR_BIT_LEN_7;
  c.device_address = a;
  c.scl_speed_hz = 100000;  // DDC's speed; the EDID is reached through the Olimex's level shifter
  i2c_master_dev_handle_t h = nullptr;
  i2c_master_bus_add_device(p4_bus, &c, &h);
  return h;
}

static bool p4_read(i2c_master_dev_handle_t d, const uint8_t *reg, size_t reg_len, uint8_t *v, size_t n) {
  return d && i2c_master_transmit_receive(d, reg, reg_len, v, n, 50) == ESP_OK;
}

static void block_camera_display() {
  printf("Block 15, camera and display: the P4 board's own I2C (SDA GPIO7, SCL GPIO8) at 100 kHz, on both ribbons\n");
  if (!p4_bus) {
    i2c_master_bus_config_t bc = {};
    bc.i2c_port = -1;
    bc.sda_io_num = GPIO_NUM_7;
    bc.scl_io_num = GPIO_NUM_8;
    bc.clk_source = I2C_CLK_SRC_DEFAULT;
    bc.glitch_ignore_cnt = 7;
    if (i2c_new_master_bus(&bc, &p4_bus) != ESP_OK) {
      verdict(false, "the second I2C bus would not start");
      return;
    }
  }
  bool seen[0x78] = {};
  for (uint8_t a = 0x08; a < 0x78; a++) {
    if (i2c_master_probe(p4_bus, a, 20) != ESP_OK) continue;
    seen[a] = true;
    printf("  0x%02X  %s\n", a,
           a == ADDR_CODEC ? "ES8311 codec, on the P4 board"
           : a == ADDR_CAM ? "OV5647 camera?"
           : (a >= ADDR_LT_MAIN && a <= ADDR_LT_AVI) ? "LT8912B, the Olimex MIPI-HDMI bridge?"
           : a == ADDR_EDID ? "a screen's EDID, through the Olimex's HDMI lead?"
                            : "");
  }

  // the camera: OV5647 chip ID in registers 0x300A and 0x300B
  uint8_t id[2] = {};
  const uint8_t r_hi[2] = {0x30, 0x0A}, r_lo[2] = {0x30, 0x0B};
  bool cam = false;
  if (seen[ADDR_CAM]) {
    i2c_master_dev_handle_t d = p4_dev(ADDR_CAM);
    cam = p4_read(d, r_hi, 2, &id[0], 1) && p4_read(d, r_lo, 2, &id[1], 1);
    printf("  Camera: chip ID %02X %02X (an OV5647 reads 56 47)\n", id[0], id[1]);
    cam = cam && id[0] == 0x56 && id[1] == 0x47;
    i2c_master_bus_rm_device(d);
  }
  verdict(cam, seen[ADDR_CAM] ? "the camera answers on its ribbon" : "nothing at 0x36: is the camera ribbon in, both ends, contacts the right way?");

  // the bridge: LT8912B chip ID in the main page's registers 0x00 and 0x01
  bool lt = false;
  if (seen[ADDR_LT_MAIN]) {
    i2c_master_dev_handle_t d = p4_dev(ADDR_LT_MAIN);
    const uint8_t r0 = 0x00, r1 = 0x01;
    lt = p4_read(d, &r0, 1, &id[0], 1) && p4_read(d, &r1, 1, &id[1], 1);
    printf("  Bridge: chip ID %02X %02X (an LT8912B reads 12 B2); %d of its 3 addresses answer\n", id[0], id[1],
           seen[ADDR_LT_MAIN] + seen[ADDR_LT_CEC] + seen[ADDR_LT_AVI]);
    lt = lt && id[0] == 0x12 && id[1] == 0xB2 && seen[ADDR_LT_CEC] && seen[ADDR_LT_AVI];
    i2c_master_bus_rm_device(d);
  }
  verdict(lt, seen[ADDR_LT_MAIN] ? "the Olimex bridge answers on the display ribbon"
                                 : "nothing at 0x48: is the display ribbon in, both ends, the DISPLAY cable?");

  // the screen: its EDID's first block, through the bridge board's DDC (needs the Olimex's HDMI 5 V)
  if (!seen[ADDR_EDID]) {
    printf("  No EDID at 0x50: no screen on the HDMI lead, or it is not powered (not a fault of the ribbon)\n");
    return;
  }
  uint8_t e[128] = {};
  i2c_master_dev_handle_t d = p4_dev(ADDR_EDID);
  const uint8_t r0 = 0x00;
  bool ok = p4_read(d, &r0, 1, e, sizeof(e));
  i2c_master_bus_rm_device(d);
  static const uint8_t HEADER[8] = {0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00};
  uint8_t sum = 0;
  for (uint8_t b : e) sum += b;
  ok = ok && memcmp(e, HEADER, 8) == 0 && sum == 0;
  if (ok) {
    const uint16_t m = (e[8] << 8) | e[9];
    const char maker[4] = {(char)('@' + ((m >> 10) & 31)), (char)('@' + ((m >> 5) & 31)), (char)('@' + (m & 31)), 0};
    char name[14] = "";
    for (int o = 72; o <= 108; o += 18)  // the display-name descriptor, if it has one
      if (e[o] == 0 && e[o + 1] == 0 && e[o + 3] == 0xFC) {
        for (int i = 0; i < 13 && e[o + 5 + i] != 0x0A; i++) name[i] = e[o + 5 + i], name[i + 1] = 0;
      }
    const uint8_t *t = e + 54;  // the preferred timing
    const unsigned clk = t[0] | (t[1] << 8), ha = t[2] | ((t[4] >> 4) << 8), hb = t[3] | ((t[4] & 15) << 8);
    const unsigned va = t[5] | ((t[7] >> 4) << 8), vb = t[6] | ((t[7] & 15) << 8);
    printf("  Screen: maker %s, product %04X%s%s; preferred %ux%u, %ux%u total, %.2f MHz\n", maker, e[10] | (e[11] << 8),
           name[0] ? ", " : "", name, ha, va, ha + hb, va + vb, clk / 100.0f);
  }
  verdict(ok, "a screen's EDID reads back whole (header and checksum)");
}

// c N V: hold CV N (1-6, or 7 for CVO7) at V volts, its switch closed, for a meter on the jack or a module
static void hold_cv(const char *args) {
  char *end, *vend;
  int ch = strtol(args, &end, 10) - 1;  // the jack, then the volts after it: "c 4 2.5" and "c4 2.5" alike
  float v = strtof(end, &vend);
  if (vend == end) v = NAN;  // no voltage given
  const float lo = cv_out_volts(0), hi = cv_out_volts(65535);
  if (ch < 0 || ch > 6 || isnan(v)) {
    printf("  Which jack and what voltage? c 1 2.5 holds CV1 (X1) at +2.5 V, c 1 -1 at -1 V; c 7 is CVO7.\n");
    return;
  }
  if (v < lo || v > hi) {
    printf("  %+.2f V is outside the DAC's range, %+.2f to %+.2f V.\n", v, lo, hi);
    return;
  }
  if (!adc_start() || !dac_start()) return;
  const uint16_t code = cv_code(v);
  dac_write(ch, code);  // the channel holds its value before its switch closes (requirement 3.6)
  delay_ms(3);
  if (ch < 6) {
    set_port0(port0 | (1 << ch));
    delay_ms(5);
    printf("Holding CV%d (%s) at %+.3f V (code %u), switch closed: meter its jack's tip, or patch it.\n", ch + 1,
           CV_NAME[ch], cv_out_volts(code), code);
    printf("  The ADC reads %+.3f V at the jack. 0 releases every jack.\n", jack_from_adc(adc_read(ch, 32)));
  } else {
    printf("Holding CVO7 at %+.3f V (code %u): meter the CVO7 hole. 0 sets it back to 0 V.\n", cv_out_volts(code), code);
  }
}

// a V: hold both audio outs at V volts DC, for a meter on DC volts: the outputs are DC-coupled, full scale ±10 V
static void hold_audio(const char *args) {
  char *end;
  float v = strtof(args, &end);
  if (end == args || fabsf(v) > 9.5f) {
    printf("  What voltage? a 5 holds both audio outs at +5 V, a -5 at -5 V; up to 9.5 V either way.\n");
    return;
  }
  audio_start();
  wave(SINE, 0, 0, 440, 0.5f, v / OUT_VOLTS);
  printf("Holding AOUT1 and AOUT2 (OUT-L, OUT-R) at %+.2f V DC: meter the AOUT holes or the jacks on DC volts. 0 stops it.\n", v);
}

static void safe() {
  if (audio_ready) wave(SINE, 0, 0);
  if (leds_ready) leds_fill(0);
  if (spib_ready) gates_write(0);
  if (exp_ready) set_port0((port0 & ~SW_ALL) | OE_N);
  if (dac_ready)
    for (uint8_t ch = 0; ch < 8; ch++) dac_write(ch, DAC_ZERO);
  printf("Safe: jack switches off, gate outs low and disabled, DAC at 0 V, audio and LEDs off.\n");
}

static void status() {
  printf("Board %s. Running: expander %s, ADC %s, DAC %s, panel bus %s, audio %s, LEDs %s, MIDI %s\n",
         powered ? "powered (the EEPROM answers)" : "NOT answering", exp_ready ? "yes" : "no", adc_ready ? "yes" : "no",
         dac_ready ? "yes" : "no", spib_ready ? "yes" : "no", audio_ready ? "yes" : "no", leds_ready ? "yes" : "no",
         midi_ready ? "yes" : "no");
  if (exp_ready)
    printf("  Jack switches %02X (bit 0 = CV1), gate outputs %s\n", port0 & SW_ALL, port0 & OE_N ? "disabled" : "enabled");
}

static void help() {
  printf("\n");
  printf("Analogue board Rev B test (ESP32-P4). Type a command and Enter. Health's panel names in brackets.\n");
  printf("  1    I2C scan                    no deck\n");
  printf("  2    EEPROM                      no deck\n");
  printf("  3    expander, then buttons live SW3 (BTN2), SW5 (BTN1), SW6 (MENU push)\n");
  printf("  4    ADC                         nothing patched into the CV jacks\n");
  printf("  4s   ADC timing on the P4        how its reply lines up, at 1, 4, 8 and 16 MHz\n");
  printf("  5    DAC to ADC, CV1-6           nothing patched into X1-Z2\n");
  printf("  5 7  CVO7 into CVI7              a wire from the CVO7 hole to CVI7\n");
  printf("  6    codec clocks                meter on the module's pins 27, 31, 32\n");
  printf("  7    gate outs                   meter on the gate-out holes\n");
  printf("  8    gate ins, live              GIN1-2 (MENU A, B), GIN3 (RST), GIN4 (CLK): a rack clock, or turn MENU\n");
  printf("  8t N gate in N threshold         X1 (CV1) patched into RST or CLK, or a wire from CV1 to GIN N\n");
  printf("  9    pots, live                  X on POT4, Y on POT2, Z on POT6\n");
  printf("  10   audio                       sine out; OUT-L/R into IN-L/R for the input checks; then IN-R's normal\n");
  printf("  11   LEDs                        a WS2812 chain on the LED holes\n");
  printf("  12   encoder, live               MENU: A on GIN1, B on GIN2 (12 A B for others); push on SW6\n");
  printf("  13   MIDI                        a TRS cable from OUT to IN (not on Health)\n");
  printf("  14   screen                      a 128x32 OLED on the I2C holes; 14 64 for a 128x64, 14 sh for an SH1106\n");
  printf("  15   camera and display I2C      the ribbons on the P4's CAMERA and DISPLAY sockets; no video sent\n");
  printf("  c N V  hold CV N at V volts      e.g. c 1 2.5 holds X1; meter on its jack's tip; c 7 is CVO7; 0 releases it\n");
  printf("  a V    hold the audio outs at V  e.g. a 5; DC volts on OUT-L and OUT-R; 0 stops it\n");
  printf("  0    safe: switches off, gate outs off, DAC at 0 V, audio and LEDs off\n");
  printf("  s    status        h  this list\n");
}

static void run(char *cmd) {
  int n = atoi(cmd);
  if (cmd[0] == 'h' || cmd[0] == '?') return help();
  if (cmd[0] == 's') return status();
  if (!powered && n != 1 && n != 15) {  // 15 is on the P4 board alone
    printf("The EEPROM at 0x50 does not answer, so the board looks unpowered: only 1 (rescan) runs.\n");
    return;
  }
  const char *rest = cmd;  // what follows the block number
  while (*rest == ' ') rest++;
  while (*rest >= '0' && *rest <= '9') rest++;
  if (n == 8 && strchr(cmd, 't')) return block_gate_threshold(atoi(strchr(cmd, 't') + 1));
  if (n == 4 && strchr(cmd, 's')) return block_adc_timing();
  if (cmd[0] == 'c') return hold_cv(cmd + 1);
  if (cmd[0] == 'a') return hold_audio(cmd + 1);
  switch (n) {
    case 0: return safe();
    case 1: return block_i2c();
    case 2: return block_eeprom();
    case 3: return block_expander();
    case 4: return block_adc();
    case 5: return block_dac(rest);
    case 6: return block_codec();
    case 7: return block_gate_outs();
    case 8: return block_gate_ins();
    case 9: return block_pots();
    case 10: return block_audio();
    case 11: return block_leds();
    case 12: return block_encoder(rest);
    case 13: return block_midi();
    case 14: return block_screen(strstr(cmd, "sh") != nullptr, strstr(cmd, "64") ? 64 : 32);
    case 15: return block_camera_display();
  }
  printf("Not a command: %s (h for the list)\n", cmd);
}

extern "C" void app_main() {
  // 1. The converter bus's bank (GPIO39-48, VDD_IO_5) to 3.3 V: LDO channel 4, passed through
  esp_ldo_channel_config_t ldo = {};
  ldo.chan_id = 4;
  ldo.voltage_mv = 3300;
  esp_ldo_channel_handle_t ldo4 = nullptr;
  const esp_err_t ldo_err = esp_ldo_acquire_channel(&ldo, &ldo4);

  // 2. Every board pin an input, as from reset; this also takes GPIO24 and 25 from the USB PHY
  gpio_config_t g = {};
  for (gpio_num_t p : BOARD_PINS) g.pin_bit_mask |= 1ULL << p;
  g.mode = GPIO_MODE_INPUT;
  gpio_config(&g);

  // 3. The console through the UART driver, so a block can poll for Enter
  uart_driver_install(UART_NUM_0, 256, 0, 0, nullptr, 0);
  uart_vfs_dev_use_driver(UART_NUM_0);
  setvbuf(stdout, nullptr, _IONBF, 0);
  esp_log_level_set("i2c.master", ESP_LOG_NONE);  // a missing device is a test result, printed as one

  // 4. I2C, and the EEPROM's answer before anything else (requirement 1)
  i2c_master_bus_config_t bc = {};
  bc.i2c_port = -1;
  bc.sda_io_num = PIN_SDA;
  bc.scl_io_num = PIN_SCL;
  bc.clk_source = I2C_CLK_SRC_DEFAULT;
  bc.glitch_ignore_cnt = 7;
  bc.flags.enable_internal_pullup = true;  // beside the board's own pull-ups; it quiets the driver's warning
  i2c_new_master_bus(&bc, &i2c_bus);
  dev_tca = i2c_dev(ADDR_TCA);
  dev_ee = i2c_dev(ADDR_EE);
  dev_oled = i2c_dev(ADDR_OLED);
  powered = i2c_present(ADDR_EE);

  help();
  if (ldo_err != ESP_OK)
    printf("\nLDO channel 4 did not take 3.3 V (%s): the ADC and DAC will not answer.\n", esp_err_to_name(ldo_err));
  if (!powered)
    printf("\nThe EEPROM at 0x50 does not answer: is the rack on? Every other bus stays off (requirement 1).\n");
  printf("\n> ");
  uart_flush_input(UART_NUM_0);
  for (;;) {
    if (!read_line(50)) continue;
    if (line[0]) {
      run(line);
      printf("\n> ");
    }
  }
}
