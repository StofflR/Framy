cmake_minimum_required(VERSION 3.18)
project(dither LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS ON)

# enable all warnings
add_compile_options(-Wall -Wextra -pedantic)

# set build type release
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# add opencv2 package
find_package(OpenCV REQUIRED)
#add open mp package
find_package(OpenMP REQUIRED)

# Add include directories
include_directories(${OpenCV_INCLUDE_DIRS})
include_directories(${OpenMP_INCLUDE_DIRS})

set(files
        dithering/dither.cpp
        dithering/dither.h
)

# Add source files
add_executable(dither ${files})

#link openmp libs
target_link_libraries(dither ${OpenCV_LIBS} OpenMP::OpenMP_CXX ${Python_LIBRARIES} ${pybind11_LIBRARIES})
