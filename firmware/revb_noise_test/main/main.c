/*
 * The noise test (docs/noise_test.md) on Health: the analogue board Rev B with the Waveshare ESP32-P4-WIFI6 in its
 * Pico 2 socket (ESP-IDF 5.5.4). Built on firmware/p4_gesture: the same screen, camera, detector and CV code, with
 * the codec and the 11 Nov schedule added.
 *
 * The 11 Nov boards cycled their screen states inside every take. Health's can only be added (once started, the
 * camera and screen have no safe way off: a stopped DSI leaves the bridge sending a blank signal, and the screen
 * flashes), so the states come one after another, each with three takes of the one-state layout:
 *
 *   30 s silence (power-up, the ES-10 relocks)
 *   idle:    three takes   the P4 runs the codec and the CV outs only; no camera, the bridge's HDMI output off
 *   52 s silence, while the camera and screen start (the EDID gate first, as in p4_gesture: 720x720p60r2 or nothing)
 *   screen:  three takes   the camera picture on the TLQ-SCREEN, about 43 frames a second
 *   52 s silence, while the hand detector loads
 *   detect:  three takes   the camera, the screen and the detector, about 11 pictures a second
 *
 *   each take, 52 s: sync 0.25 s (1500 Hz, -6 dBFS), gap 1.75 s, zero 20 s (silence out, input ignored), tone 10 s
 *   (997 Hz, -6 dBFS), through 20 s (input copied to output, unity)
 *
 * About 10 minutes in all; record.py health records it, analyse.py --health reads it. The codec runs at 48 076.9 Hz
 * (its MCLK is the 160 MHz PLL / 13, so the APLL is free for the screen's pixel clock), and segment lengths and tones
 * are counted at that rate, so they come out at the 11 Nov lengths and pitches. 48-frame blocks, as on 11 Nov.
 *
 * The CV outs run as in p4_gesture: CV1 and CV3 switched on at 0 V, and moved only by a hand the detector sees.
 * Nobody in view during the run, so they hold 0 V.
 */
#include <fcntl.h>
#include <inttypes.h>
#include <math.h>
#include <stdbool.h>
#include <string.h>
#include <sys/ioctl.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_check.h"
#include "esp_timer.h"
#include "esp_cache.h"
#include "esp_private/esp_cache_private.h"
#include "esp_heap_caps.h"
#include "esp_ldo_regulator.h"
#include "clk_ctrl_os.h"
#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "driver/spi_master.h"
#include "driver/ppa.h"
#include "driver/i2s_std.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_mipi_dsi.h"
#include "esp_lcd_lt8912b.h"
#include "linux/videodev2.h"
#include "esp_video_init.h"
#include "esp_video_device.h"
#include "detect.h"

static const char *TAG = "noise";

// ---- the lanes
#define LANE_CH_LEFT    0           // CV1, X1 on the panel: the hand on the screen's left
#define LANE_CH_RIGHT   2           // CV3, X2 on the panel: the hand on the screen's right
#define END_STOP        0.1f        // the bottom and top tenth of the picture: 0 V and 10 V
#define LANE_VOLTS      10.0f
#define SLEW_MS         50.0f       // the CV's glide between detections (a one-pole time constant)
#define CV_TICK_MS      2

// ---- the screen and camera, as in firmware/p4_camera_screen
#define I2C_SDA     7
#define I2C_SCL     8
#define ADDR_EDID   0x50

// Tiliqua's 720x720p60r2, which the TLQ-SCREEN's EDID gives
#define H_RES       720
#define V_RES       720
#define HFP         40
#define HS          8
#define HBP         44                      // 812 - 768
#define VFP         50
#define VS          16
#define VBP         16                      // 802 - 786
#define H_TOTAL     (H_RES + HFP + HS + HBP)
#define V_TOTAL     (V_RES + VFP + VS + VBP)
#define PCLK_HZ     39070000

#define NUM_FBS     3                       // one shown, one queued, one being filled
#define CAM_BUFS    2
#define FB_BYTES    (H_RES * V_RES * 2)     // RGB565
#define SQUARE      960                     // the camera's middle square, scaled by 0.75 to the screen
#define DET         320                     // ...and by a third for the detectors
#define BARS_MS     3000

// ---- the analogue board (pins and codes from firmware/analogue_board_revb_test)
#define PIN_ASDA        31
#define PIN_ASCL        30
#define PIN_SPIA_SCK    46
#define PIN_SPIA_MOSI   33
#define PIN_SPIA_MISO   32
#define PIN_CS_ADC      47
#define PIN_CS_DAC      48
static const int BOARD_PINS[] = {46, 33, 32, 47, 48, 3, 2, 5, 24, 25, 50, 49, 29, 4, 28, 27, 23, 22, 21, 26, 52, 51};
#define ADDR_TCA        0x20
#define ADDR_EE         0x50
#define TCA_OUT0        2
#define TCA_CFG0        6
#define TCA_CFG1        7
#define OE_N            0x40                // TCA9555 P06: gate outputs disabled while high
#define DAC_GAIN        8.5f
#define DAC_OFFSET      (7.5f * 2.5f * 20 / 35)  // 10.714 V
#define SPI_CONV_HZ     4000000

#define RGB565_WHITE    0xFFFF
#define RGB565_GREY     0x8410

// ---- the screen and camera
static esp_lcd_panel_handle_t panel;
static esp_lcd_panel_lt8912b_io_t io;
static void *fbs[NUM_FBS];
static ppa_client_handle_t ppa;
static int cam_fd = -1;
static uint32_t cam_w, cam_h;
static void *cam_bufs[CAM_BUFS];
static size_t cam_buf_bytes;
static bool h_positive, v_positive;

// ---- the detectors' picture and what they found
static void *det_buf;
static size_t det_bytes;
static TaskHandle_t det_task_handle;
static volatile bool det_want;              // the detectors are ready for another picture

typedef struct {
    bool has_hand[2];                       // [0] the hand on the screen's left, [1] on the right
    bool hand_live[2];                      // found in this picture, or held from an earlier one
    box_t hand[2];
} scene_t;
static portMUX_TYPE scene_lock = portMUX_INITIALIZER_UNLOCKED;
static scene_t scene;                       // the latest detection, for the overlay
static float lane_target[2];                // volts
static bool lane_set[2];                    // each lane has had a hand at least once

// ---- the analogue board
static bool board_ready;
static i2c_master_dev_handle_t dev_tca;
static spi_device_handle_t spi_conv;

// ============================================================================ the screen (p4_camera_screen)

// the screen's EDID: true only if its preferred timing is 720x720p60r2, to the pixel and the 10 kHz
static bool screen_is_tlq(i2c_master_bus_handle_t bus)
{
    i2c_device_config_t c = {.dev_addr_length = I2C_ADDR_BIT_LEN_7, .device_address = ADDR_EDID, .scl_speed_hz = 100000};
    i2c_master_dev_handle_t d = NULL;
    if (i2c_master_bus_add_device(bus, &c, &d) != ESP_OK) {
        return false;
    }
    uint8_t e[128] = {0}, offset = 0;
    esp_err_t err = i2c_master_transmit_receive(d, &offset, 1, e, sizeof(e), 100);
    i2c_master_bus_rm_device(d);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "no EDID at 0x50: is the screen on the HDMI lead, and the rack on? Nothing sent");
        return false;
    }
    static const uint8_t header[8] = {0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00};
    uint8_t sum = 0;
    for (int i = 0; i < 128; i++) {
        sum += e[i];
    }
    if (memcmp(e, header, 8) != 0 || sum != 0) {
        ESP_LOGE(TAG, "the EDID did not read back whole (header or checksum): nothing sent");
        return false;
    }
    const uint8_t *t = e + 54;  // the preferred timing
    const unsigned clk = t[0] | t[1] << 8;  // 10 kHz units
    const unsigned ha = t[2] | (t[4] >> 4) << 8, hb = t[3] | (t[4] & 15) << 8;
    const unsigned va = t[5] | (t[7] >> 4) << 8, vb = t[6] | (t[7] & 15) << 8;
    const unsigned hfp = t[8] | (t[11] >> 6) << 8, hs = t[9] | ((t[11] >> 4) & 3) << 8;
    const unsigned vfp = (t[10] >> 4) | ((t[11] >> 2) & 3) << 4, vs = (t[10] & 15) | (t[11] & 3) << 4;
    const bool separate = (t[17] & 0x18) == 0x18;
    h_positive = t[17] & 0x02;
    v_positive = t[17] & 0x04;
    const bool ok = clk == PCLK_HZ / 10000 && ha == H_RES && va == V_RES && ha + hb == H_TOTAL && va + vb == V_TOTAL
                    && hfp == HFP && hs == HS && vfp == VFP && vs == VS && separate;
    if (!ok) {
        ESP_LOGE(TAG, "not the TLQ-SCREEN's 720x720p60 (%ux%u, %.2f MHz): nothing sent", ha, va, clk / 100.0);
    }
    return ok;
}

// LT8912B at 720x720p60r2 in DVI mode; the DSI host reads RGB565 frame buffers and sends RGB888
static esp_err_t screen_start(i2c_master_bus_handle_t bus)
{
    periph_rtc_apll_acquire();
    uint32_t apll_hz = 0;
    ESP_RETURN_ON_ERROR(periph_rtc_apll_freq_set(PCLK_HZ, &apll_hz), TAG, "APLL");

    esp_lcd_dsi_bus_handle_t dsi = NULL;
    esp_lcd_dsi_bus_config_t dsi_cfg = LT8912B_PANEL_BUS_DSI_2CH_CONFIG();  // 2 lanes at 960 Mbps
    ESP_RETURN_ON_ERROR(esp_lcd_new_dsi_bus(&dsi_cfg, &dsi), TAG, "DSI bus");

    esp_lcd_panel_io_i2c_config_t io_main = LT8912B_IO_CFG(100000, LT8912B_IO_I2C_MAIN_ADDRESS);
    esp_lcd_panel_io_i2c_config_t io_cec = LT8912B_IO_CFG(100000, LT8912B_IO_I2C_CEC_ADDRESS);
    esp_lcd_panel_io_i2c_config_t io_avi = LT8912B_IO_CFG(100000, LT8912B_IO_I2C_AVI_ADDRESS);
    ESP_RETURN_ON_ERROR(esp_lcd_new_panel_io_i2c(bus, &io_main, &io.main), TAG, "bridge I/O");
    ESP_RETURN_ON_ERROR(esp_lcd_new_panel_io_i2c(bus, &io_cec, &io.cec_dsi), TAG, "bridge I/O");
    ESP_RETURN_ON_ERROR(esp_lcd_new_panel_io_i2c(bus, &io_avi, &io.avi), TAG, "bridge I/O");

    esp_lcd_dpi_panel_config_t dpi_cfg = {
        .dpi_clk_src = MIPI_DSI_DPI_CLK_SRC_APLL,
        .dpi_clock_freq_mhz = PCLK_HZ / 1e6f,
        .virtual_channel = 0,
        .in_color_format = LCD_COLOR_FMT_RGB565,
        .out_color_format = LCD_COLOR_FMT_RGB888,
        .num_fbs = NUM_FBS,
        .video_timing = {
            .h_size = H_RES, .v_size = V_RES,
            .hsync_front_porch = HFP, .hsync_pulse_width = HS, .hsync_back_porch = HBP,
            .vsync_front_porch = VFP, .vsync_pulse_width = VS, .vsync_back_porch = VBP,
        },
        .flags.disable_lp = true,
    };
    lt8912b_vendor_config_t vendor = {
        .video_timing = {
            .hfp = HFP, .hs = HS, .hbp = HBP, .hact = H_RES, .htotal = H_TOTAL,
            .vfp = VFP, .vs = VS, .vbp = VBP, .vact = V_RES, .vtotal = V_TOTAL,
            .h_polarity = h_positive, .v_polarity = v_positive,
            .vic = 0,  // not a CEA mode; DVI sends no infoframe anyway
            .aspect_ratio = LT8912B_ASPECT_RATION_NO,
            .pclk_mhz = 39,  // the driver takes whole MHz; it only seeds the bridge's DDS
        },
        .mipi_config = {.dsi_bus = dsi, .dpi_config = &dpi_cfg, .lane_num = 2},
    };
    esp_lcd_panel_dev_config_t dev_cfg = {
        .reset_gpio_num = -1,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel = 24,
        .vendor_config = &vendor,
    };
    ESP_RETURN_ON_ERROR(esp_lcd_new_panel_lt8912b(&io, &dev_cfg, &panel), TAG, "bridge panel");
    ESP_RETURN_ON_ERROR(esp_lcd_panel_reset(panel), TAG, "bridge reset");
    ESP_RETURN_ON_ERROR(esp_lcd_panel_init(panel), TAG, "bridge init");
    // the driver sets HDMI mode (0xB2 = 0x01); the TLQ-SCREEN is a DVI receiver (a TFP401) and Tiliqua sends DVI
    const uint8_t dvi = 0x00;
    ESP_RETURN_ON_ERROR(esp_lcd_panel_io_tx_param(io.main, 0xB2, &dvi, 1), TAG, "DVI mode");
    return esp_lcd_dpi_panel_get_frame_buffer(panel, NUM_FBS, &fbs[0], &fbs[1], &fbs[2]);
}

static void camera_flip(uint32_t id)
{
    struct v4l2_ext_control ctrl = {.id = id, .value = 1};
    struct v4l2_ext_controls ctrls = {.ctrl_class = V4L2_CTRL_CLASS_USER, .count = 1, .controls = &ctrl};
    if (ioctl(cam_fd, VIDIOC_S_EXT_CTRLS, &ctrls) != 0) {
        ESP_LOGW(TAG, "camera flip 0x%" PRIx32 " not applied", id);
    }
}

// the OV5647 through esp_video's V4L2 interface, RGB565 into two cache-aligned PSRAM buffers
static esp_err_t camera_start(i2c_master_bus_handle_t bus)
{
    esp_video_init_csi_config_t csi = {
        .sccb_config = {.init_sccb = false, .i2c_handle = bus, .freq = 100000},
        .reset_pin = -1,
        .pwdn_pin = -1,
    };
    esp_video_init_config_t cfg = {.csi = &csi};
    ESP_RETURN_ON_ERROR(esp_video_init(&cfg), TAG, "esp_video_init");

    cam_fd = open(ESP_VIDEO_MIPI_CSI_DEVICE_NAME, O_RDONLY);
    ESP_RETURN_ON_FALSE(cam_fd >= 0, ESP_FAIL, TAG, "open %s", ESP_VIDEO_MIPI_CSI_DEVICE_NAME);
    struct v4l2_format fmt = {.type = V4L2_BUF_TYPE_VIDEO_CAPTURE};
    ESP_RETURN_ON_FALSE(ioctl(cam_fd, VIDIOC_G_FMT, &fmt) == 0, ESP_FAIL, TAG, "G_FMT");
    cam_w = fmt.fmt.pix.width;
    cam_h = fmt.fmt.pix.height;
    fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_RGB565;
    ESP_RETURN_ON_FALSE(ioctl(cam_fd, VIDIOC_S_FMT, &fmt) == 0, ESP_FAIL, TAG, "S_FMT");
    ESP_RETURN_ON_FALSE(cam_w >= SQUARE && cam_h >= SQUARE, ESP_FAIL, TAG, "camera frame smaller than %d square", SQUARE);
    camera_flip(V4L2_CID_VFLIP);  // as Waveshare's example sets them for this camera
    camera_flip(V4L2_CID_HFLIP);

    struct v4l2_requestbuffers req = {.count = CAM_BUFS, .type = V4L2_BUF_TYPE_VIDEO_CAPTURE, .memory = V4L2_MEMORY_USERPTR};
    ESP_RETURN_ON_FALSE(ioctl(cam_fd, VIDIOC_REQBUFS, &req) == 0, ESP_FAIL, TAG, "REQBUFS");
    size_t align = 0;
    ESP_RETURN_ON_ERROR(esp_cache_get_alignment(MALLOC_CAP_SPIRAM, &align), TAG, "cache alignment");
    for (int i = 0; i < CAM_BUFS; i++) {
        struct v4l2_buffer buf = {.type = V4L2_BUF_TYPE_VIDEO_CAPTURE, .memory = V4L2_MEMORY_USERPTR, .index = i};
        ESP_RETURN_ON_FALSE(ioctl(cam_fd, VIDIOC_QUERYBUF, &buf) == 0, ESP_FAIL, TAG, "QUERYBUF");
        cam_bufs[i] = heap_caps_aligned_calloc(align, 1, cam_w * cam_h * 2, MALLOC_CAP_SPIRAM);
        ESP_RETURN_ON_FALSE(cam_bufs[i], ESP_ERR_NO_MEM, TAG, "camera buffer");
        cam_buf_bytes = buf.length;
        buf.m.userptr = (unsigned long)cam_bufs[i];
        ESP_RETURN_ON_FALSE(ioctl(cam_fd, VIDIOC_QBUF, &buf) == 0, ESP_FAIL, TAG, "QBUF");
    }
    // the detectors' picture: the same cache alignment, its size rounded up to whole cache lines
    det_bytes = (DET * DET * 2 + align - 1) / align * align;
    det_buf = heap_caps_aligned_calloc(align, 1, det_bytes, MALLOC_CAP_SPIRAM);
    ESP_RETURN_ON_FALSE(det_buf, ESP_ERR_NO_MEM, TAG, "detection buffer");

    int type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    ESP_RETURN_ON_FALSE(ioctl(cam_fd, VIDIOC_STREAMON, &type) == 0, ESP_FAIL, TAG, "STREAMON");
    return ESP_OK;
}

// ============================================================================ the overlay

static inline void put(uint16_t *fb, int x, int y, uint16_t c)
{
    if ((unsigned)x < H_RES && (unsigned)y < V_RES) {
        fb[y * H_RES + x] = c;
    }
}

// a point in the detectors' picture to the frame buffer: scaled to 720, then the PPA's quarter turn clockwise
static void to_screen(int u, int v, int *x, int *y)
{
    *x = H_RES - 1 - v * H_RES / DET;
    *y = u * V_RES / DET;
}

static void draw_box(uint16_t *fb, const box_t *b, uint16_t c)
{
    int xa, ya, xb, yb;
    to_screen(b->x0, b->y0, &xa, &ya);
    to_screen(b->x1, b->y1, &xb, &yb);
    const int x0 = xa < xb ? xa : xb, x1 = xa < xb ? xb : xa, y0 = ya < yb ? ya : yb, y1 = ya < yb ? yb : ya;
    for (int t = 0; t < 3; t++) {
        for (int x = x0; x <= x1; x++) {
            put(fb, x, y0 + t, c);
            put(fb, x, y1 - t, c);
        }
        for (int y = y0; y <= y1; y++) {
            put(fb, x0 + t, y, c);
            put(fb, x1 - t, y, c);
        }
    }
}

static void draw_line(uint16_t *fb, int xa, int ya, int xb, int yb, uint16_t c)
{
    const int dx = abs(xb - xa), sx = xa < xb ? 1 : -1, dy = -abs(yb - ya), sy = ya < yb ? 1 : -1;
    int err = dx + dy;
    for (;;) {
        put(fb, xa, ya, c);
        put(fb, xa + 1, ya, c);
        put(fb, xa, ya + 1, c);
        if (xa == xb && ya == yb) {
            break;
        }
        const int e2 = 2 * err;
        if (e2 >= dy) {
            err += dy;
            xa += sx;
        }
        if (e2 <= dx) {
            err += dx;
            ya += sy;
        }
    }
}

static void draw_scene(uint16_t *fb)
{
    scene_t s;
    taskENTER_CRITICAL(&scene_lock);
    s = scene;
    taskEXIT_CRITICAL(&scene_lock);
    int xa, ya, xb, yb;
    to_screen(DET / 2, 0, &xa, &ya);  // the middle, top to bottom of the picture
    to_screen(DET / 2, DET - 1, &xb, &yb);
    draw_line(fb, xa, ya, xb, yb, RGB565_GREY);
    for (int i = 0; i < 2; i++) {
        if (s.has_hand[i]) {
            const int cy = (s.hand[i].y0 + s.hand[i].y1) / 2;
            to_screen(i ? DET / 2 : 0, cy, &xa, &ya);  // the fader's level: across its half, at the hand's height
            to_screen(i ? DET - 1 : DET / 2, cy, &xb, &yb);
            draw_line(fb, xa, ya, xb, yb, RGB565_GREY);
            draw_box(fb, &s.hand[i], s.hand_live[i] ? RGB565_WHITE : RGB565_GREY);
        }
    }
    // write the drawing back to PSRAM for the display DMA, and drop the lines so the next fill reads fresh
    esp_cache_msync(fb, FB_BYTES, ESP_CACHE_MSYNC_FLAG_DIR_C2M | ESP_CACHE_MSYNC_FLAG_INVALIDATE);
}

// ============================================================================ the camera task

// each camera frame: the middle square to the screen (and, when the detectors are ready, to them), then the overlay
static void camera_task(void *arg)
{
    int next = 0, frames = 0;
    bool first = true;
    int64_t t0 = esp_timer_get_time();
    for (;;) {
        struct v4l2_buffer buf = {.type = V4L2_BUF_TYPE_VIDEO_CAPTURE, .memory = V4L2_MEMORY_USERPTR};
        if (ioctl(cam_fd, VIDIOC_DQBUF, &buf) != 0) {
            ESP_LOGE(TAG, "DQBUF failed");
            vTaskDelay(pdMS_TO_TICKS(10));
            continue;
        }
        ppa_srm_oper_config_t srm = {
            .in = {
                .buffer = cam_bufs[buf.index], .pic_w = cam_w, .pic_h = cam_h,
                .block_w = SQUARE, .block_h = SQUARE,
                .block_offset_x = (cam_w - SQUARE) / 2, .block_offset_y = (cam_h - SQUARE) / 2,
                .srm_cm = PPA_SRM_COLOR_MODE_RGB565,
            },
            .out = {
                .buffer = fbs[next], .buffer_size = FB_BYTES, .pic_w = H_RES, .pic_h = V_RES,
                .srm_cm = PPA_SRM_COLOR_MODE_RGB565,
            },
            .rotation_angle = PPA_SRM_ROTATION_ANGLE_270,  // the PPA turns anticlockwise: 270 is a quarter clockwise
            .scale_x = (float)H_RES / SQUARE, .scale_y = (float)V_RES / SQUARE,
            .mode = PPA_TRANS_MODE_BLOCKING,
        };
        esp_err_t err = ppa_do_scale_rotate_mirror(ppa, &srm);
        if (err == ESP_OK && det_want) {
            // the same square, upright and a third the size, for the detectors
            srm.out.buffer = det_buf;
            srm.out.buffer_size = det_bytes;
            srm.out.pic_w = DET;
            srm.out.pic_h = DET;
            srm.rotation_angle = PPA_SRM_ROTATION_ANGLE_0;
            srm.scale_x = srm.scale_y = (float)DET / SQUARE;
            if (ppa_do_scale_rotate_mirror(ppa, &srm) == ESP_OK) {
                det_want = false;
                xTaskNotifyGive(det_task_handle);
            }
        }
        buf.m.userptr = (unsigned long)cam_bufs[buf.index];
        buf.length = cam_buf_bytes;
        if (ioctl(cam_fd, VIDIOC_QBUF, &buf) != 0) {
            ESP_LOGE(TAG, "QBUF failed");
        }
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "PPA failed: %s", esp_err_to_name(err));
            continue;
        }
        draw_scene(fbs[next]);
        // one of the panel's own buffers, so this is a swap at the next frame, not a copy
        esp_lcd_panel_draw_bitmap(panel, 0, 0, H_RES, V_RES, fbs[next]);
        next = (next + 1) % NUM_FBS;
        if (first) {
            esp_lcd_dpi_panel_set_pattern(panel, MIPI_DSI_PATTERN_NONE);  // the bars give way to the first picture
            ESP_LOGI(TAG, "first camera frame on the screen");
            first = false;
        }
        frames++;
        int64_t now = esp_timer_get_time();
        if (now - t0 >= 5000000) {
            ESP_LOGI(TAG, "%.1f camera frames/s to the screen", frames * 1e6 / (now - t0));
            frames = 0;
            t0 = now;
        }
    }
}

// ============================================================================ the detectors

static float centre_x(const box_t *b) { return (b->x0 + b->x1) * 0.5f; }

static void detect_task(void *arg)
{
    detect_init();
    int runs = 0, found[2] = {0, 0};
    int64_t hand_us = 0;
    float lo[2] = {INFINITY, INFINITY}, hi[2] = {0, 0};
    int64_t report = esp_timer_get_time();
    scene_t s = {0};  // the hands persist from picture to picture, held until found again
    for (;;) {
        det_want = true;
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        esp_cache_msync(det_buf, det_bytes, ESP_CACHE_MSYNC_FLAG_DIR_M2C);  // the PPA wrote it; read it fresh

        box_t h[8];
        const int64_t a = esp_timer_get_time();
        const int nh = detect_hands(det_buf, DET, DET, h, 8);
        const int64_t now = esp_timer_get_time();
        hand_us += now - a;
        runs++;

        // each half of the picture takes its most likely hand; a half with none found keeps its last hand, held
        s.hand_live[0] = s.hand_live[1] = false;
        for (int i = 0; i < nh; i++) {
            const int side = centre_x(&h[i]) < DET / 2.0f ? 0 : 1;
            if (!s.hand_live[side]) {  // the boxes come highest score first
                s.hand_live[side] = s.has_hand[side] = true;
                s.hand[side] = h[i];
                found[side]++;
            }
        }
        float target[2];
        for (int i = 0; i < 2; i++) {
            if (s.hand_live[i]) {
                const float up = 1 - (s.hand[i].y0 + s.hand[i].y1) * 0.5f / DET;  // 0 bottom, 1 top
                lo[i] = fminf(lo[i], up);
                hi[i] = fmaxf(hi[i], up);
                const float x = (up - END_STOP) / (1 - 2 * END_STOP);
                target[i] = LANE_VOLTS * (x < 0 ? 0 : x > 1 ? 1 : x);
            }
        }
        taskENTER_CRITICAL(&scene_lock);
        scene = s;
        for (int i = 0; i < 2; i++) {
            if (s.hand_live[i]) {
                lane_target[i] = target[i];
                lane_set[i] = true;
            }
        }
        taskEXIT_CRITICAL(&scene_lock);

        if (now - report >= 5000000) {
            ESP_LOGI(TAG, "%.1f detections/s; hands %.0f ms; left hand found in %d%%, right in %d%%",
                     runs * 1e6 / (now - report), hand_us / 1000.0 / runs, 100 * found[0] / runs, 100 * found[1] / runs);
            for (int i = 0; i < 2; i++) {
                const int cv = i ? LANE_CH_RIGHT + 1 : LANE_CH_LEFT + 1;
                if (hi[i] > 0) {
                    ESP_LOGI(TAG, "  %s lane (CV%d): %.0f%% to %.0f%% of the way up (0 V at %.0f%%, 10 V at %.0f%%)",
                             i ? "right" : "left", cv, 100 * lo[i], 100 * hi[i], 100 * END_STOP, 100 * (1 - END_STOP));
                } else {
                    ESP_LOGI(TAG, "  %s lane (CV%d): no hand found, holding", i ? "right" : "left", cv);
                }
                lo[i] = INFINITY;
                hi[i] = 0;
            }
            runs = found[0] = found[1] = 0;
            hand_us = 0;
            report = now;
        }
    }
}

// ============================================================================ the analogue board and the CV outs

static uint16_t cv_code(float v)
{
    long c = lroundf((v + DAC_OFFSET) * 65536 / (DAC_GAIN * 2.5f));
    return c < 0 ? 0 : c > 65535 ? 65535 : (uint16_t)c;
}

static bool tca_write(uint8_t reg, uint8_t v)
{
    const uint8_t b[2] = {reg, v};
    return i2c_master_transmit(dev_tca, b, 2, 20) == ESP_OK;
}

static void cs_output(int pin)
{
    gpio_set_level(pin, 1);
    gpio_set_direction(pin, GPIO_MODE_OUTPUT);
}

static void dac_frame(uint32_t w)
{
    spi_transaction_t t = {.flags = SPI_TRANS_USE_TXDATA, .length = 32};
    t.tx_data[0] = w >> 24;
    t.tx_data[1] = w >> 16;
    t.tx_data[2] = w >> 8;
    t.tx_data[3] = w;
    gpio_set_level(PIN_CS_DAC, 0);
    spi_device_polling_transmit(spi_conv, &t);
    gpio_set_level(PIN_CS_DAC, 1);
}

static void dac_write(uint8_t ch, uint16_t code) { dac_frame(0x03000000 | (ch << 20) | ((uint32_t)code << 4)); }

// the analogue board's start-up order (spec §15): the EEPROM answers first, then the DAC, then the two jack switches
static bool board_start(void)
{
    gpio_config_t g = {.mode = GPIO_MODE_INPUT};
    for (size_t i = 0; i < sizeof(BOARD_PINS) / sizeof(BOARD_PINS[0]); i++) {
        g.pin_bit_mask |= 1ULL << BOARD_PINS[i];  // every board pin an input, as from reset (GPIO24 and 25 from USB)
    }
    gpio_config(&g);

    i2c_master_bus_handle_t bus = NULL;
    i2c_master_bus_config_t bc = {
        .i2c_port = -1, .sda_io_num = PIN_ASDA, .scl_io_num = PIN_ASCL,
        .clk_source = I2C_CLK_SRC_DEFAULT, .glitch_ignore_cnt = 7, .flags.enable_internal_pullup = true,
    };
    if (i2c_new_master_bus(&bc, &bus) != ESP_OK) {
        return false;
    }
    if (i2c_master_probe(bus, ADDR_EE, 20) != ESP_OK) {
        ESP_LOGE(TAG, "the analogue board's EEPROM does not answer: is the rack on? No CV out");
        return false;
    }
    i2c_device_config_t c = {.dev_addr_length = I2C_ADDR_BIT_LEN_7, .device_address = ADDR_TCA, .scl_speed_hz = 400000};
    if (i2c_master_bus_add_device(bus, &c, &dev_tca) != ESP_OK) {
        return false;
    }
    // 1. every jack switch off and the gate outputs disabled, the output register before the pins turn into outputs
    if (!tca_write(TCA_OUT0, OE_N) || !tca_write(TCA_CFG0, 0x80) || !tca_write(TCA_CFG1, 0xFF)) {
        ESP_LOGE(TAG, "the TCA9555 did not take its settings: no CV out");
        return false;
    }
    cs_output(PIN_CS_ADC);
    cs_output(PIN_CS_DAC);
    spi_bus_config_t b = {
        .mosi_io_num = PIN_SPIA_MOSI, .miso_io_num = PIN_SPIA_MISO, .sclk_io_num = PIN_SPIA_SCK,
        .quadwp_io_num = -1, .quadhd_io_num = -1, .max_transfer_sz = 4,
    };
    spi_device_interface_config_t d = {.mode = 1, .clock_speed_hz = SPI_CONV_HZ, .spics_io_num = -1, .queue_size = 1};
    if (spi_bus_initialize(SPI2_HOST, &b, SPI_DMA_DISABLED) != ESP_OK || spi_bus_add_device(SPI2_HOST, &d, &spi_conv) != ESP_OK) {
        return false;
    }
    for (uint8_t ch = 0; ch < 8; ch++) {
        dac_write(ch, cv_code(0));  // 2. 0 V codes while the reference is still off
    }
    dac_frame(0x090A0000);          // 3. internal reference on: flexible mode, always on
    vTaskDelay(pdMS_TO_TICKS(10));  // 4. settle
    // 5 and 6: the lanes hold 0 V, then their switches close
    if (!tca_write(TCA_OUT0, OE_N | 1 << LANE_CH_LEFT | 1 << LANE_CH_RIGHT)) {
        return false;
    }
    return true;
}

// each lane glides to its target, and holds it while its hand goes unseen; 0 V until it has first had one
static void cv_task(void *arg)
{
    static const uint8_t ch[2] = {LANE_CH_LEFT, LANE_CH_RIGHT};
    const float k = 1 - expf(-CV_TICK_MS / SLEW_MS);
    float v[2] = {0, 0};
    uint16_t last[2] = {cv_code(0), cv_code(0)};
    TickType_t wake = xTaskGetTickCount();
    for (;;) {
        vTaskDelayUntil(&wake, pdMS_TO_TICKS(CV_TICK_MS));
        float target[2];
        taskENTER_CRITICAL(&scene_lock);
        for (int i = 0; i < 2; i++) {
            target[i] = lane_set[i] ? lane_target[i] : 0;
        }
        taskEXIT_CRITICAL(&scene_lock);
        for (int i = 0; i < 2; i++) {
            v[i] += k * (target[i] - v[i]);
            const uint16_t code = cv_code(v[i]);
            if (code != last[i]) {
                dac_write(ch[i], code);
                last[i] = code;
            }
        }
    }
}

// ============================================================================ the noise test: the codec and its schedule

// the PCM3060 as an I2S slave (hardware mode, 24-bit I2S), MCLK 256 fs, as in firmware/analogue_board_revb_test
#define RATE_ASKED  48077                   // ESP-IDF's divider search then rounds to 13 with no fraction
#define FS_REAL     48076.92f               // 160 MHz / 13 / 256: what the codec really runs at
#define FRAMES      48                      // 48-frame blocks, as every board on 11 Nov
#define PIN_MCLK    27
#define PIN_BCK     23
#define PIN_LRCK    22
#define PIN_DOUT    21                      // to the codec
#define PIN_DIN     26                      // from it
#define LEVEL       0.5f                    // -6 dBFS
#define SYNC_HZ     1500.0f
#define TONE_HZ     997.0f
#define TAKES       3
#define TAKE_S      52.0f

typedef enum { SEG_ZERO, SEG_SYNC, SEG_TONE, SEG_THROUGH, SEG_END } seg_kind_t;
typedef enum { ST_IDLE, ST_SCREEN, ST_DETECT } state_t;
static const char *const STATE_NAME[] = {
    "idle: no camera, nothing sent to the screen", "the camera on the TLQ-SCREEN", "the camera, the screen and the hand detector"};
typedef struct {
    uint8_t kind, state;
    uint32_t samples;
} seg_t;
static seg_t segs[64];
static int nsegs;
static volatile int seg_i;                  // the audio task's place in the schedule
static volatile uint8_t want_state;         // the state the schedule has reached, for the main task to start
static i2s_chan_handle_t i2s_tx, i2s_rx;

static void seg_add(seg_kind_t k, state_t st, float secs)
{
    segs[nsegs++] = (seg_t){.kind = k, .state = st, .samples = (uint32_t)lroundf(secs * FS_REAL)};
}

static void schedule_build(void)
{
    seg_add(SEG_ZERO, ST_IDLE, 30);
    for (int st = ST_IDLE; st <= ST_DETECT; st++) {
        if (st != ST_IDLE) {
            seg_add(SEG_ZERO, st, TAKE_S);  // a take's length of silence while the new state starts
        }
        for (int t = 0; t < TAKES; t++) {
            seg_add(SEG_SYNC, st, 0.25f);
            seg_add(SEG_ZERO, st, 1.75f);
            seg_add(SEG_ZERO, st, 20);
            seg_add(SEG_TONE, st, 10);
            seg_add(SEG_THROUGH, st, 20);
        }
    }
    seg_add(SEG_END, ST_DETECT, 0);
}

static inline int32_t to_codec(float v)
{
    v = v > 0.999f ? 0.999f : v < -0.999f ? -0.999f : v;
    return (int32_t)(v * 8388607) * 256;  // 24 bits at the top of the 32-bit slot
}

// a block in, a block out, in step with the codec's frames
static void audio_task(void *arg)
{
    static int32_t in[FRAMES * 2], out[FRAMES * 2];
    uint32_t pos = 0;
    float phase = 0;
    for (;;) {
        size_t n = 0;
        i2s_channel_read(i2s_rx, in, sizeof(in), &n, portMAX_DELAY);
        for (int i = 0; i < FRAMES; i++) {
            const seg_t *sg = &segs[seg_i];
            float l = 0, r = 0;
            if (sg->kind == SEG_SYNC || sg->kind == SEG_TONE) {
                l = r = LEVEL * sinf(2 * (float)M_PI * phase);
                phase += (sg->kind == SEG_SYNC ? SYNC_HZ : TONE_HZ) / FS_REAL;
                if (phase >= 1) {
                    phase -= 1;
                }
            } else if (sg->kind == SEG_THROUGH) {
                // the inputs invert (bring-up block 10), so they are negated: input to output, unity
                l = -(float)in[2 * i] / 2147483648.0f;
                r = -(float)in[2 * i + 1] / 2147483648.0f;
            }
            out[2 * i] = to_codec(l);
            out[2 * i + 1] = to_codec(r);
            if (sg->kind != SEG_END && ++pos >= sg->samples) {
                pos = 0;
                seg_i++;
                want_state = segs[seg_i].state;
            }
        }
        i2s_channel_write(i2s_tx, out, sizeof(out), &n, portMAX_DELAY);
    }
}

static esp_err_t audio_start(void)
{
    i2s_chan_config_t cc = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    cc.dma_desc_num = 6;
    cc.dma_frame_num = FRAMES;
    cc.auto_clear = true;
    ESP_RETURN_ON_ERROR(i2s_new_channel(&cc, &i2s_tx, &i2s_rx), TAG, "I2S channels");
    i2s_std_config_t sc = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(RATE_ASKED),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_STEREO),
        .gpio_cfg = {.mclk = PIN_MCLK, .bclk = PIN_BCK, .ws = PIN_LRCK, .dout = PIN_DOUT, .din = PIN_DIN},
    };
    sc.clk_cfg.clk_src = I2S_CLK_SRC_PLL_160M;  // / 13: the APLL stays free for the screen
    ESP_RETURN_ON_ERROR(i2s_channel_init_std_mode(i2s_tx, &sc), TAG, "I2S out");
    ESP_RETURN_ON_ERROR(i2s_channel_init_std_mode(i2s_rx, &sc), TAG, "I2S in");
    ESP_RETURN_ON_ERROR(i2s_channel_enable(i2s_tx), TAG, "I2S out on");
    ESP_RETURN_ON_ERROR(i2s_channel_enable(i2s_rx), TAG, "I2S in on");
    xTaskCreatePinnedToCore(audio_task, "audio", 4096, NULL, 10, NULL, 1);
    return ESP_OK;
}

// a reset leaves the Olimex bridge as the last program set it (the ribbon's 3V3 stays up), and after a camera program
// its HDMI output is still on with nothing coming in: the TLQ-SCREEN then flashes about every 2 s. So it goes off at
// boot, as firmware/analogue_board_revb_test does: the main page's 0x33 = 0x0C
static void bridge_quiet(i2c_master_bus_handle_t bus)
{
    i2c_device_config_t c = {.dev_addr_length = I2C_ADDR_BIT_LEN_7, .device_address = LT8912B_IO_I2C_MAIN_ADDRESS, .scl_speed_hz = 100000};
    i2c_master_dev_handle_t d = NULL;
    if (i2c_master_bus_add_device(bus, &c, &d) != ESP_OK) {
        return;
    }
    const uint8_t off[2] = {0x33, 0x0C};
    const esp_err_t err = i2c_master_transmit(d, off, 2, 50);
    i2c_master_bus_rm_device(d);
    ESP_LOGI(TAG, "the bridge's HDMI output %s", err == ESP_OK ? "is off" : "could NOT be turned off");
}

// ============================================================================

void app_main(void)
{
    // the MIPI PHY supply (camera and display share it): LDO channel 3 at 2.5 V
    esp_ldo_channel_handle_t ldo3 = NULL, ldo4 = NULL;
    esp_ldo_channel_config_t ldo3_cfg = {.chan_id = 3, .voltage_mv = 2500};
    ESP_ERROR_CHECK(esp_ldo_acquire_channel(&ldo3_cfg, &ldo3));
    // the bank of GPIO46-48 (SPIA_SCK, CS_ADC, CS_DAC): LDO channel 4 at 3.3 V before the converter bus
    esp_ldo_channel_config_t ldo4_cfg = {.chan_id = 4, .voltage_mv = 3300};
    const esp_err_t ldo4_err = esp_ldo_acquire_channel(&ldo4_cfg, &ldo4);
    if (ldo4_err != ESP_OK) {
        ESP_LOGE(TAG, "LDO channel 4 did not take 3.3 V (%s): no CV out", esp_err_to_name(ldo4_err));
    }
    board_ready = ldo4_err == ESP_OK && board_start();
    if (board_ready) {
        xTaskCreatePinnedToCore(cv_task, "cv", 3072, NULL, 6, NULL, 1);
        ESP_LOGI(TAG, "CV out, vertical faders: the hand on the screen's left -> CV1 (X1), on the right -> CV3 (X2); "
                 "0 V at %.0f%% of the way up, 10 V at %.0f%%", 100 * END_STOP, 100 * (1 - END_STOP));
    }

    i2c_master_bus_handle_t bus = NULL;
    i2c_master_bus_config_t bus_cfg = {
        .i2c_port = -1, .sda_io_num = I2C_SDA, .scl_io_num = I2C_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT, .glitch_ignore_cnt = 7,
    };
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus));
    bool tlq = false;
    if (i2c_master_probe(bus, LT8912B_IO_I2C_MAIN_ADDRESS, 50) != ESP_OK) {
        ESP_LOGE(TAG, "LT8912B not found: check the display ribbon. The screen states will start nothing");
    } else {
        bridge_quiet(bus);
        tlq = screen_is_tlq(bus);  // read now, so a wrong screen is known before the run; nothing is sent yet
        if (!tlq) {
            ESP_LOGE(TAG, "not the TLQ-SCREEN: the screen states will start nothing, so this run is idle throughout");
        }
    }

    schedule_build();
    if (audio_start() != ESP_OK) {
        ESP_LOGE(TAG, "the codec did not start: no test");
        return;
    }
    ESP_LOGI(TAG, "the noise test: 30 s, then three takes each idle, with the screen, and with the detector, 52 s a "
             "take and a take's silence before each new state; about 10 minutes. Codec at 48 076.9 Hz, 48-frame blocks");

    bool camera_ok = false;
    uint8_t state = ST_IDLE;
    int last_seg = -1;
    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(50));
        if (seg_i != last_seg) {
            last_seg = seg_i;
            static const char *const KIND[] = {"zero", "sync", "tone", "through", "end"};
            ESP_LOGI(TAG, "segment %d: %s, %s", last_seg, KIND[segs[last_seg].kind], STATE_NAME[segs[last_seg].state]);
        }
        if (want_state == state) {
            continue;
        }
        state = want_state;
        ESP_LOGI(TAG, "state: %s", STATE_NAME[state]);
        if (state == ST_SCREEN && tlq) {
            ppa_client_config_t ppa_cfg = {.oper_type = PPA_OPERATION_SRM};
            if (screen_start(bus) != ESP_OK) {
                ESP_LOGE(TAG, "the screen side failed to start");
            } else if (ppa_register_client(&ppa_cfg, &ppa) != ESP_OK || camera_start(bus) != ESP_OK) {
                ESP_LOGE(TAG, "the camera failed to start");
            } else {
                camera_ok = true;
                xTaskCreatePinnedToCore(camera_task, "cam_screen", 4096, NULL, 5, NULL, 1);
                ESP_LOGI(TAG, "screen running at 720x720p60, DVI, with the camera picture");
            }
        } else if (state == ST_DETECT && camera_ok) {
            xTaskCreatePinnedToCore(detect_task, "detect", 16384, NULL, 4, &det_task_handle, 0);
            ESP_LOGI(TAG, "the hand detector is running");
        }
    }
}
