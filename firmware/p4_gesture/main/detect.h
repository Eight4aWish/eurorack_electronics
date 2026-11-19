// Espressif's face and hand detectors (esp-dl), behind a C interface for main.c
#pragma once
#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int x0, y0, x1, y1;  // in the picture's pixels, top left to bottom right
    float score;
} box_t;

void detect_init(void);
// faces or hands in an RGB565 (little-endian) picture: up to max boxes, highest score first; returns how many
int detect_faces(void *rgb565, int w, int h, box_t *out, int max);
int detect_hands(void *rgb565, int w, int h, box_t *out, int max);
// the face detector: Espressif's fast two-stage one (MSR+MNP) or the 224x224 one-stage one (ESPDet-Pico)
void detect_swap_face_model(void);
const char *detect_face_model(void);

#ifdef __cplusplus
}
#endif
