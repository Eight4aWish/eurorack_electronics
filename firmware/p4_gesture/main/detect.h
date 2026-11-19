// Espressif's hand detector (esp-dl), behind a C interface for main.c
#pragma once
#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int x0, y0, x1, y1;  // in the picture's pixels, top left to bottom right
    float score;
} box_t;

void detect_init(void);
// hands in an RGB565 (little-endian) picture: up to max boxes, highest score first; returns how many
int detect_hands(void *rgb565, int w, int h, box_t *out, int max);

#ifdef __cplusplus
}
#endif
