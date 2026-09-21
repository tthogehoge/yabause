ROCKNIX=/home/takashi/work/distribution
TOOLCHAIN=${ROCKNIX}/build.ROCKNIX-RK3566.aarch64/toolchain
SYSROOT_PREFIX=${TOOLCHAIN}/aarch64-rocknix-linux-gnu/sysroot
PKG_BUILD=`pwd`/../
SDL2DIR=${TOOLCHAIN}

PKG_CMAKE_OPTS_TARGET=" -DUSE_EGL=ON -DUSE_OPENGL=OFF"
# opengl
#PKG_CMAKE_OPTS_TARGET+=" -DUSE_EGL=ON -DUSE_OPENGL=ON"
# opengles
PKG_CMAKE_OPTS_TARGET="${PKG_CMAKE_OPTS_TARGET} -DUSE_EGL=ON -DUSE_OPENGL=OFF"
PKG_CMAKE_OPTS_TARGET="${PKG_CMAKE_OPTS_TARGET} -DCMAKE_SYSTEM_PROCESSOR=x86_64
                         -DOPENGL_INCLUDE_DIR=${SYSROOT_PREFIX}/usr/include \
                         -DOPENGL_opengl_LIBRARY=${SYSROOT_PREFIX}/usr/lib \
                         -DOPENGL_glx_LIBRARY=${SYSROOT_PREFIX}/usr/lib \
                         -DLIBPNG_LIB_DIR=${SYSROOT_PREFIX}/usr/lib \
                         -Dpng_STATIC_LIBRARIES=${SYSROOT_PREFIX}/usr/lib/libpng16.so \
                         -DCMAKE_BUILD_TYPE=Release \
                         -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON"
PKG_CMAKE_OPTS_TARGET="${PKG_CMAKE_OPTS_TARGET} -DYAB_WANT_ARM7=ON \
		       -DYAB_WANT_DYNAREC_DEVMIYAX=ON \
		       -DYAB_PORTS=retro_arena \
		       -DCMAKE_PROJECT_INCLUDE=${PKG_BUILD}/yabause/src/retro_arena/n2.cmake"
PKG_CMAKE_OPTS_TARGET="${PKG_CMAKE_OPTS_TARGET} -DCMAKE_C_FLAGS=-Ofast -DCMAKE_CXX_FLAGS=-Ofast"

mkdir -p build
cd build
${TOOLCHAIN}/bin/cmake ../ -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_TOOLCHAIN_FILE=${TOOLCHAIN}/etc/cmake-aarch64-rocknix-linux-gnu.conf ${PKG_CMAKE_OPTS_TARGET}

