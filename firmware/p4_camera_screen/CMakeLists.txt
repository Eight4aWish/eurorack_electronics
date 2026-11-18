# The camera on the Tiliqua Screen, through the Waveshare ESP32-P4-WIFI6 (ESP-IDF 5.5.4): bring-up
# step 10 of docs/analogue_board_revb_bringup.md. Built from the October bench program that put the
# camera on HDMI at 1280x720 (docs/analogue_board_esp32p4.md, Bench tests).
cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(p4_camera_screen)
