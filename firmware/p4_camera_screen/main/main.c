/*
 * The camera on the Tiliqua Screen (TLQ-SCREEN), through the Waveshare ESP32-P4-WIFI6 on Health's board:
 * bring-up step 10 (docs/analogue_board_revb_bringup.md).
 *
 * OV5647 on CAMERA, 1280x960 binned at 45 fps -> ISP -> RGB565 -> the PPA takes the middle 960x960, scales it to
 * 720x720 and turns it a quarter clockwise into one of three DPI frame buffers -> MIPI DSI (RGB565 in, RGB888 out) on
 * DISPLAY -> Raspberry Pi display adapter cable -> Olimex MIPI-HDMI (LT8912B) in DVI mode -> HDMI lead -> TLQ-SCREEN.
 *
 * The screen must only ever get its own timing, Tiliqua's 720x720p60r2 (gateware/src/tiliqua/video/modeline.py):
 * 812x802 total at 39.07 MHz. So the first act is to read the screen's EDID through the Olimex's DDC, and nothing
 * is sent unless its preferred timing is exactly that. The sync polarities are taken from the EDID, as Tiliqua's
 * bootloader takes them.
 *
 * The panel is mounted a quarter turn round: a frame sent in scan order shows with its bottom on the right (a
 * quarter turn anticlockwise). Tiliqua turns its picture back; here the PPA turns each one a quarter clockwise.
 *
 * Colour bars come first, for a few seconds, with no camera and no PSRAM in the path: they prove the display side
 * on its own. Then the camera. The console prints what the bridge measures and the frames per second.
 *
 * The camera's SCCB, the bridge and the EDID share the P4 board's own I2C (GPIO7 SDA, GPIO8 SCL). Nothing on the
 * analogue board is touched: its pins stay as they come out of reset.
 */
#include <fcntl.h>
#include <inttypes.h>
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
#include "driver/i2c_master.h"
#include "driver/ppa.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_mipi_dsi.h"
#include "esp_lcd_lt8912b.h"
#include "linux/videodev2.h"
#include "esp_video_init.h"
#include "esp_video_device.h"

static const char *TAG = "cam_screen";

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
#define BARS_MS     5000

static esp_lcd_panel_handle_t panel;
static esp_lcd_panel_lt8912b_io_t io;
static void *fbs[NUM_FBS];
static ppa_client_handle_t ppa;
static int cam_fd = -1;
static uint32_t cam_w, cam_h;
static void *cam_bufs[CAM_BUFS];
static size_t cam_buf_bytes;
static bool h_positive, v_positive;

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
    ESP_LOGI(TAG, "screen EDID: product %04X, %ux%u, %ux%u total, %.2f MHz; h front %u sync %u, v front %u sync %u; "
             "syncs h%c v%c", e[10] | e[11] << 8, ha, va, ha + hb, va + vb, clk / 100.0, hfp, hs, vfp, vs,
             h_positive ? '+' : '-', v_positive ? '+' : '-');
    const bool ok = clk == PCLK_HZ / 10000 && ha == H_RES && va == V_RES && ha + hb == H_TOTAL && va + vb == V_TOTAL
                    && hfp == HFP && hs == HS && vfp == VFP && vs == VS && separate;
    if (!ok) {
        ESP_LOGE(TAG, "not the TLQ-SCREEN's 720x720p60: nothing sent");
    }
    return ok;
}

// LT8912B at 720x720p60r2 in DVI mode; the DSI host reads RGB565 frame buffers and sends RGB888
static esp_err_t screen_start(i2c_master_bus_handle_t bus)
{
    periph_rtc_apll_acquire();
    uint32_t apll_hz = 0;
    ESP_RETURN_ON_ERROR(periph_rtc_apll_freq_set(PCLK_HZ, &apll_hz), TAG, "APLL");
    ESP_LOGI(TAG, "APLL %" PRIu32 " Hz for a %d Hz pixel clock", apll_hz, PCLK_HZ);

    esp_lcd_dsi_bus_handle_t dsi = NULL;
    esp_lcd_dsi_bus_config_t dsi_cfg = LT8912B_PANEL_BUS_DSI_2CH_CONFIG();  // 2 lanes at 960 Mbps, as in October
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

// what the bridge measures of the MIPI input, and the screen's hot-plug line
static void bridge_report(void)
{
    uint8_t r[4] = {0}, mode = 0, hpd = 0;
    for (int i = 0; i < 4; i++) {
        esp_lcd_panel_io_rx_param(io.main, 0x9C + i, &r[i], 1);
    }
    esp_lcd_panel_io_rx_param(io.main, 0xB2, &mode, 1);
    esp_lcd_panel_io_rx_param(io.main, 0xC1, &hpd, 1);
    ESP_LOGI(TAG, "bridge: MIPI in, H %u, V %u (V is lines a frame: %d expected); %s mode; hot-plug %s",
             r[0] | r[1] << 8, r[2] | r[3] << 8, V_TOTAL, mode ? "HDMI" : "DVI", hpd & 0x80 ? "high" : "low");
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
    ESP_LOGI(TAG, "camera %" PRIu32 "x%" PRIu32 ", RGB565", cam_w, cam_h);
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
    int type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    ESP_RETURN_ON_FALSE(ioctl(cam_fd, VIDIOC_STREAMON, &type) == 0, ESP_FAIL, TAG, "STREAMON");
    return ESP_OK;
}

// each camera frame: the middle square, scaled to 720x720 and turned a quarter clockwise, into the next frame buffer
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
        buf.m.userptr = (unsigned long)cam_bufs[buf.index];
        buf.length = cam_buf_bytes;
        if (ioctl(cam_fd, VIDIOC_QBUF, &buf) != 0) {
            ESP_LOGE(TAG, "QBUF failed");
        }
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "PPA failed: %s", esp_err_to_name(err));
            continue;
        }
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

void app_main(void)
{
    // the MIPI PHY supply (camera and display share it): LDO channel 3 at 2.5 V
    esp_ldo_channel_handle_t ldo = NULL;
    esp_ldo_channel_config_t ldo_cfg = {.chan_id = 3, .voltage_mv = 2500};
    ESP_ERROR_CHECK(esp_ldo_acquire_channel(&ldo_cfg, &ldo));

    i2c_master_bus_handle_t bus = NULL;
    i2c_master_bus_config_t bus_cfg = {
        .i2c_port = 0, .sda_io_num = I2C_SDA, .scl_io_num = I2C_SCL,
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
    vTaskDelay(pdMS_TO_TICKS(500));
    bridge_report();
    vTaskDelay(pdMS_TO_TICKS(BARS_MS - 500));

    ppa_client_config_t ppa_cfg = {.oper_type = PPA_OPERATION_SRM};
    ESP_ERROR_CHECK(ppa_register_client(&ppa_cfg, &ppa));
    if (camera_start(bus) != ESP_OK) {
        ESP_LOGE(TAG, "camera failed to start: the bars stay");
        return;
    }
    xTaskCreatePinnedToCore(camera_task, "cam_screen", 4096, NULL, 5, NULL, 1);
}
