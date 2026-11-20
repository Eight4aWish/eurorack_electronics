idf_component_register(SRCS "main.c" "detect.cpp" INCLUDE_DIRS ".")
# idf.py -B build_dark -DSCREEN_DARK=1 build flash: the screen stays dark (main.c). Its own build folder, so the
# setting, which CMake caches, never reaches the usual build/.
if(SCREEN_DARK)
    target_compile_definitions(${COMPONENT_LIB} PRIVATE SCREEN_DARK=1)
endif()
