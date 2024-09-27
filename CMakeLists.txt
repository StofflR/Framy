cmake_minimum_required(VERSION 3.25)
project(dither LANGUAGES CXX)

# Set C++ standard to C++23
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS ON)

# enable all warnings
add_compile_options(-Wall -Wextra -pedantic)

# add opencv2 package
find_package(OpenCV REQUIRED)

# Add include directories
include_directories(${OpenCV_INCLUDE_DIRS})

# Add source files
add_executable(dither dither.cpp)

target_link_libraries(dither ${OpenCV_LIBS} ${Python_LIBRARIES} ${pybind11_LIBRARIES})
