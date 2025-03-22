project(m68kmake)

cmake_minimum_required(VERSION 2.6)

add_executable(m68kmake m68kmake.c)

if (MSVC)
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif (MSVC)

add_custom_command(OUTPUT m68kops.h
                   COMMAND /home/takashi/distribution/build.ROCKNIX-RK3566.aarch64/yabasanshiro-sa-a40dace1ae0af3ebd45848549fdf396f40e3930f/m68kmake_host ${CMAKE_CURRENT_BINARY_DIR}/ ${CMAKE_CURRENT_SOURCE_DIR}/m68k_in.c
                   DEPENDS m68kmake.c
                   COMMENT "Generating musashi 68k core"
                   VERBATIM)

add_custom_target(musashi ALL DEPENDS m68kops.h)
