/*
 * Health's first gesture program (ESP-IDF 5.5.4, Waveshare ESP32-P4-WIFI6 on the analogue board Rev B).
 *
 * The camera shows on the TLQ-SCREEN as in firmware/p4_camera_screen (bring-up step 10), and Espressif's face and
 * hand detectors (esp-dl) look at the same square picture. The head is the reference: each hand's distance from it,
 * counted in head-widths so it holds when the player steps about, is a fader-like lane on a CV out.
 *
 *   the hand on the screen's left  -> CV1 (X1 on the panel), 0 to 10 V -> Oneiroi's supersaw volume jack
 *   the hand on the screen's right -> CV3 (X2 on the panel), 0 to 10 V -> Oneiroi's filter cutoff jack (knob left)
 *
 * A lane is 0 V with the hand at NEAR_HW head-widths from the head or closer, and 10 V at FAR_HW or further. If its
 * hand (or the head) goes unseen for HOLD_US, the lane falls back to 0 V. The CV glides between detections.
 *
 * The screen shows what the detectors found: the head in red, the hands in white, a grey line from the head to each.
 * The console prints, every 5 s, detections a second, each model's time, how often the head and hands were seen,
 * and the range of each lane in head-widths (to set NEAR_HW and FAR_HW from real playing). 'f' on the console swaps
 * the face detector between Espressif's fast two-stage one and the 224x224 one.
 *
 * Pipeline: OV5647 1280x960 -> ISP -> RGB565 -> PPA: the middle 960x960 -> (a) 720x720, a quarter clockwise, to the
 * screen; (b) 320x320, upright, to the detectors when they are ready for another picture.
 *
 * The analogue board: LDO channel 4 at 3.3 V first (GPIO46-48 are in its bank), then the EEPROM must answer before
 * any other bus starts, then the DAC8568's start-up order (spec §15, requirement 3): every jack switch off, 0 V codes,
 * reference on, then each used channel's switch. Only CV1 and CV3 are switched on; the other jacks stay open.
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
#include "driver/uart.h"
#include "driver/uart_vfs.h"
#include "driver/ppa.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_mipi_dsi.h"
#include "esp_lcd_lt8912b.h"
#include "linux/videodev2.h"
#include "esp_video_init.h"
#include "esp_video_device.h"
#include "detect.h"

static const char *TAG = "gesture";

// ---- the lanes
#define LANE_CH_LEFT    0           // CV1, X1 on the panel: the hand on the screen's left
#define LANE_CH_RIGHT   2           // CV3, X2 on the panel: the hand on the screen's right
#define NEAR_HW         1.0f        // head-widths from the head: 0 V at this or closer
#define FAR_HW          4.0f        // ...and 10 V at this or further
#define LANE_VOLTS      10.0f
#define HOLD_US         1000000     // a lane holds this long without its hand or the head, then falls to 0 V
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
#define RGB565_RED      0xE022              // the brand red, #E30613
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
    bool has_face, has_hand[2];             // [0] the hand on the screen's left, [1] on the right
    box_t face, hand[2];
} scene_t;
static portMUX_TYPE scene_lock = portMUX_INITIALIZER_UNLOCKED;
static scene_t scene;                       // the latest detection, for the overlay
static float lane_target[2];                // volts
static int64_t lane_seen[2];                // when each lane last had its hand and the head

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
    if (!s.has_face && !s.has_hand[0] && !s.has_hand[1]) {
        return;
    }
    if (s.has_face) {
        int hx, hy;
        to_screen((s.face.x0 + s.face.x1) / 2, (s.face.y0 + s.face.y1) / 2, &hx, &hy);
        for (int i = 0; i < 2; i++) {
            if (s.has_hand[i]) {
                int x, y;
                to_screen((s.hand[i].x0 + s.hand[i].x1) / 2, (s.hand[i].y0 + s.hand[i].y1) / 2, &x, &y);
                draw_line(fb, hx, hy, x, y, RGB565_GREY);
            }
        }
        draw_box(fb, &s.face, RGB565_RED);
    }
    for (int i = 0; i < 2; i++) {
        if (s.has_hand[i]) {
            draw_box(fb, &s.hand[i], RGB565_WHITE);
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
static float centre_y(const box_t *b) { return (b->y0 + b->y1) * 0.5f; }

static void detect_task(void *arg)
{
    detect_init();
    int runs = 0, with_head = 0, two_hands = 0, one_hand = 0;
    int64_t face_us = 0, hand_us = 0;
    float lo[2] = {INFINITY, INFINITY}, hi[2] = {0, 0};
    int64_t report = esp_timer_get_time();
    box_t head = {0};
    int64_t head_seen = 0;
    for (;;) {
        det_want = true;
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        esp_cache_msync(det_buf, det_bytes, ESP_CACHE_MSYNC_FLAG_DIR_M2C);  // the PPA wrote it; read it fresh

        uint8_t key;
        if (uart_read_bytes(UART_NUM_0, &key, 1, 0) == 1 && (key == 'f' || key == 'F')) {
            detect_swap_face_model();
            ESP_LOGI(TAG, "face detector now %s (it loads on its first run)", detect_face_model());
        }

        box_t f[4], h[8];
        const int64_t a = esp_timer_get_time();
        const int nf = detect_faces(det_buf, DET, DET, f, 4);
        const int64_t b = esp_timer_get_time();
        const int nh = detect_hands(det_buf, DET, DET, h, 8);
        const int64_t now = esp_timer_get_time();
        face_us += b - a;
        hand_us += now - b;
        runs++;

        if (nf > 0) {
            head = f[0];  // the most likely face
            head_seen = now;
            with_head++;
        }
        const bool head_fresh = head_seen && now - head_seen < HOLD_US;
        // each side of the head (or of the picture, with no head yet) takes its most likely hand
        const float split = head_fresh ? centre_x(&head) : DET / 2.0f;
        scene_t s = {.has_face = nf > 0, .face = head};
        for (int i = 0; i < nh; i++) {
            const int side = centre_x(&h[i]) < split ? 0 : 1;
            if (!s.has_hand[side]) {  // the boxes come highest score first
                s.has_hand[side] = true;
                s.hand[side] = h[i];
            }
        }
        two_hands += s.has_hand[0] && s.has_hand[1];
        one_hand += s.has_hand[0] != s.has_hand[1];

        float target[2];
        bool update[2] = {false, false};
        const float head_w = (float)(head.x1 - head.x0);
        for (int i = 0; i < 2; i++) {
            if (s.has_hand[i] && head_fresh && head_w > 0) {
                const float d = hypotf(centre_x(&s.hand[i]) - centre_x(&head), centre_y(&s.hand[i]) - centre_y(&head)) / head_w;
                lo[i] = fminf(lo[i], d);
                hi[i] = fmaxf(hi[i], d);
                const float x = (d - NEAR_HW) / (FAR_HW - NEAR_HW);
                target[i] = LANE_VOLTS * (x < 0 ? 0 : x > 1 ? 1 : x);
                update[i] = true;
            }
        }
        taskENTER_CRITICAL(&scene_lock);
        scene = s;
        for (int i = 0; i < 2; i++) {
            if (update[i]) {
                lane_target[i] = target[i];
                lane_seen[i] = now;
            }
        }
        taskEXIT_CRITICAL(&scene_lock);

        if (now - report >= 5000000) {
            ESP_LOGI(TAG, "%.1f detections/s; face %.0f ms (%s), hands %.0f ms; head in %d%%, two hands %d%%, one %d%%",
                     runs * 1e6 / (now - report), face_us / 1000.0 / runs, detect_face_model(), hand_us / 1000.0 / runs,
                     100 * with_head / runs, 100 * two_hands / runs, 100 * one_hand / runs);
            for (int i = 0; i < 2; i++) {
                if (hi[i] > 0) {
                    ESP_LOGI(TAG, "  %s lane (CV%d): %.1f to %.1f head-widths from the head (0 V at %.1f, 10 V at %.1f)",
                             i ? "right" : "left", i ? LANE_CH_RIGHT + 1 : LANE_CH_LEFT + 1, lo[i], hi[i], NEAR_HW, FAR_HW);
                } else {
                    ESP_LOGI(TAG, "  %s lane (CV%d): no hand with a head", i ? "right" : "left",
                             i ? LANE_CH_RIGHT + 1 : LANE_CH_LEFT + 1);
                }
                lo[i] = INFINITY;
                hi[i] = 0;
            }
            runs = with_head = two_hands = one_hand = 0;
            face_us = hand_us = 0;
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

// each lane glides to its target, or to 0 V once its hand or the head has gone unseen for HOLD_US
static void cv_task(void *arg)
{
    static const uint8_t ch[2] = {LANE_CH_LEFT, LANE_CH_RIGHT};
    const float k = 1 - expf(-CV_TICK_MS / SLEW_MS);
    float v[2] = {0, 0};
    uint16_t last[2] = {cv_code(0), cv_code(0)};
    TickType_t wake = xTaskGetTickCount();
    for (;;) {
        vTaskDelayUntil(&wake, pdMS_TO_TICKS(CV_TICK_MS));
        const int64_t now = esp_timer_get_time();
        float target[2];
        taskENTER_CRITICAL(&scene_lock);
        for (int i = 0; i < 2; i++) {
            target[i] = lane_seen[i] && now - lane_seen[i] < HOLD_US ? lane_target[i] : 0;
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

// ============================================================================

void app_main(void)
{
    // the console through the UART driver, so the detector task can read 'f' without blocking
    uart_driver_install(UART_NUM_0, 256, 0, 0, NULL, 0);
    uart_vfs_dev_use_driver(UART_NUM_0);

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
        ESP_LOGI(TAG, "CV out: the hand on the screen's left -> CV1 (X1), on the right -> CV3 (X2); 0 V at %.1f "
                 "head-widths from the head, 10 V at %.1f", NEAR_HW, FAR_HW);
    }

    i2c_master_bus_handle_t bus = NULL;
    i2c_master_bus_config_t bus_cfg = {
        .i2c_port = -1, .sda_io_num = I2C_SDA, .scl_io_num = I2C_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT, .glitch_ignore_cnt = 7,
    };
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus));
    if (i2c_master_probe(bus, LT8912B_IO_I2C_MAIN_ADDRESS, 50) != ESP_OK) {
        ESP_LOGE(TAG, "LT8912B not found: check the display ribbon. Nothing sent");
        return;
    }
    if (!screen_is_tlq(bus)) {
        return;
    }
    if (screen_start(bus) != ESP_OK) {
        ESP_LOGE(TAG, "the screen side failed to start");
        return;
    }
    esp_lcd_dpi_panel_set_pattern(panel, MIPI_DSI_PATTERN_BAR_VERTICAL);
    ESP_LOGI(TAG, "screen running at 720x720p60, DVI: colour bars for %d s", BARS_MS / 1000);
    vTaskDelay(pdMS_TO_TICKS(BARS_MS));

    ppa_client_config_t ppa_cfg = {.oper_type = PPA_OPERATION_SRM};
    ESP_ERROR_CHECK(ppa_register_client(&ppa_cfg, &ppa));
    if (camera_start(bus) != ESP_OK) {
        ESP_LOGE(TAG, "camera failed to start: the bars stay");
        return;
    }
    xTaskCreatePinnedToCore(detect_task, "detect", 16384, NULL, 4, &det_task_handle, 0);
    xTaskCreatePinnedToCore(camera_task, "cam_screen", 4096, NULL, 5, NULL, 1);
    ESP_LOGI(TAG, "'f' on the console swaps the face detector");
}
