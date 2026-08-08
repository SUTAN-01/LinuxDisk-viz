cmake_minimum_required(VERSION 3.16)
project(disk_scanner CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_compile_options(-O3 -Wall -Wextra)

add_executable(disk-scanner
    src/main.cpp
    src/ndjson_writer.cpp
)
target_include_directories(disk-scanner PRIVATE src)

enable_testing()

include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
)
FetchContent_MakeAvailable(googletest)

add_executable(disk_scanner_tests
    tests/test_smoke.cpp
    tests/test_ndjson_writer.cpp
    src/ndjson_writer.cpp
)
target_include_directories(disk_scanner_tests PRIVATE src)
target_link_libraries(disk_scanner_tests PRIVATE GTest::gtest_main)

include(GoogleTest)
gtest_discover_tests(disk_scanner_tests)
