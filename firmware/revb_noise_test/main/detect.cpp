// Espressif's hand detector (esp-dl), behind a C interface for main.c. The model loads on its first run.
// Head detection (espressif/human_face_detect) was tried on 2026-11-19 and dropped for now: see main.c.
#include <algorithm>
#include <list>
#include "hand_detect.hpp"
#include "detect.h"

static HandDetect *hands;

void detect_init(void)
{
    hands = new HandDetect(HandDetect::ESPDET_PICO_224_224_HAND);
}

int detect_hands(void *rgb565, int w, int h, box_t *out, int max)
{
    dl::image::img_t img;
    img.data = rgb565;
    img.width = (uint16_t)w;
    img.height = (uint16_t)h;
    img.pix_type = dl::image::DL_IMAGE_PIX_TYPE_RGB565LE;
    int n = 0;
    for (const auto &r : hands->run(img)) {
        if (n == max) {
            break;
        }
        out[n++] = {r.box[0], r.box[1], r.box[2], r.box[3], r.score};
    }
    std::sort(out, out + n, [](const box_t &a, const box_t &b) { return a.score > b.score; });
    return n;
}
