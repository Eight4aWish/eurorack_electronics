// Espressif's face and hand detectors (esp-dl), behind a C interface for main.c. Each model loads on its first run.
#include <algorithm>
#include <list>
#include "hand_detect.hpp"
#include "human_face_detect.hpp"
#include "detect.h"

static HandDetect *hands;
static HumanFaceDetect *faces[2];
static int face_model;  // 0: MSR+MNP, 1: ESPDet-Pico 224
static const char *const FACE_NAME[2] = {"MSR+MNP", "ESPDet-Pico 224"};

void detect_init(void)
{
    hands = new HandDetect(HandDetect::ESPDET_PICO_224_224_HAND);
    faces[0] = new HumanFaceDetect(HumanFaceDetect::MSRMNP_S8_V1);
}

void detect_swap_face_model(void)
{
    face_model ^= 1;
    if (!faces[face_model]) {
        faces[face_model] = new HumanFaceDetect(HumanFaceDetect::ESPDET_PICO_224_224_FACE);
    }
}

const char *detect_face_model(void) { return FACE_NAME[face_model]; }

static int copy_boxes(const std::list<dl::detect::result_t> &res, box_t *out, int max)
{
    int n = 0;
    for (const auto &r : res) {
        if (n == max) {
            break;
        }
        out[n++] = {r.box[0], r.box[1], r.box[2], r.box[3], r.score};
    }
    std::sort(out, out + n, [](const box_t &a, const box_t &b) { return a.score > b.score; });
    return n;
}

static dl::image::img_t picture(void *rgb565, int w, int h)
{
    dl::image::img_t img;
    img.data = rgb565;
    img.width = (uint16_t)w;
    img.height = (uint16_t)h;
    img.pix_type = dl::image::DL_IMAGE_PIX_TYPE_RGB565LE;
    return img;
}

int detect_faces(void *rgb565, int w, int h, box_t *out, int max)
{
    return copy_boxes(faces[face_model]->run(picture(rgb565, w, h)), out, max);
}

int detect_hands(void *rgb565, int w, int h, box_t *out, int max)
{
    return copy_boxes(hands->run(picture(rgb565, w, h)), out, max);
}
