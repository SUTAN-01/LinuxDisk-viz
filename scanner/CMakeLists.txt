cmake_minimum_required(VERSION 3.16)
project(disk_scanner C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_compile_options(-O3 -Wall -Wextra)

# SQLite3 amalgamation compiled once as a static library, linked by both
# the scanner and the test binary.
add_library(sqlite3 STATIC third_party/sqlite3.c)
target_include_directories(sqlite3 PUBLIC third_party)
target_compile_definitions(sqlite3 PRIVATE SQLITE_THREADSAFE=1)

add_executable(disk-scanner
    src/main.cpp
    src/ndjson_writer.cpp
    src/walker.cpp
    src/stat_pool.cpp
    src/cache.cpp
)
target_include_directories(disk-scanner PRIVATE src third_party)
target_link_libraries(disk-scanner PRIVATE sqlite3)

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
    tests/test_walker.cpp
    tests/test_stat_pool.cpp
    tests/test_cache.cpp
    tests/test_integration.cpp
    tests/test_cli.cpp
    src/ndjson_writer.cpp
    src/walker.cpp
    src/stat_pool.cpp
    src/cache.cpp
)
target_include_directories(disk_scanner_tests PRIVATE src third_party)
target_link_libraries(disk_scanner_tests PRIVATE GTest::gtest_main sqlite3)

include(GoogleTest)
gtest_discover_tests(disk_scanner_tests WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR})
