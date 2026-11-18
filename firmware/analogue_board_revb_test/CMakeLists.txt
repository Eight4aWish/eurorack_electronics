# Rev B bring-up test for the analogue board with the Waveshare ESP32-P4-WIFI6 (ESP-IDF 5.5.4).
# One serial command per block of docs/analogue_board_revb_bringup.md stage 6; build and flash as
# that stage says.
cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(analogue_board_revb_test)
