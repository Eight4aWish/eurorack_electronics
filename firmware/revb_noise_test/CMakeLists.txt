# The noise test (docs/noise_test.md) on Health: Rev B's audio path with the P4 idle, the camera on the TLQ-SCREEN,
# then the hand detector too. Built on firmware/p4_gesture.
cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(revb_noise_test)
