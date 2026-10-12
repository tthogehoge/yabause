project(m68kmake)

cmake_minimum_required(VERSION 3.5)

set(M68KMAKE_HOST "${CMAKE_CURRENT_BINARY_DIR}/m68kmake-host")

add_custom_command(
    OUTPUT "${M68KMAKE_HOST}"
    COMMAND "${YAB_HOST_C_COMPILER}" "${CMAKE_CURRENT_SOURCE_DIR}/m68kmake.c"
            -o "${M68KMAKE_HOST}"
    DEPENDS m68kmake.c
    COMMENT "Building host m68kmake"
    VERBATIM)

if (MSVC)
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif (MSVC)

add_custom_command(OUTPUT m68kops.h
                   COMMAND "${M68KMAKE_HOST}" ${CMAKE_CURRENT_BINARY_DIR}/ ${CMAKE_CURRENT_SOURCE_DIR}/m68k_in.c
                   DEPENDS "${M68KMAKE_HOST}" m68k_in.c
                   COMMENT "Generating musashi 68k core"
                   VERBATIM)

add_custom_target(musashi ALL DEPENDS m68kops.h)
