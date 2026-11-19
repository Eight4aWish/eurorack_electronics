# Health's first gesture program: the camera on the TLQ-SCREEN with Espressif's face and hand detectors,
# and each hand's distance from the head as a fader-like CV lane. Built on firmware/p4_camera_screen.
cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(p4_gesture)
