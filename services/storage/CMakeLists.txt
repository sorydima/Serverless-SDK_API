cmake_minimum_required(VERSION 3.16)
project(storage-service)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find userver
find_package(userver REQUIRED)

# Find additional libraries
find_package(PostgreSQL REQUIRED)
find_package(hiredis REQUIRED)
find_package(OpenSSL REQUIRED)

# Add executable
add_executable(${PROJECT_NAME}
    src/main.cpp
    src/storage_handler.cpp
    src/database_manager.cpp
    src/cache_manager.cpp
    src/file_storage.cpp
)

# Link libraries
target_link_libraries(${PROJECT_NAME}
    userver::core
    PostgreSQL::PostgreSQL
    hiredis::hiredis
    OpenSSL::SSL
    OpenSSL::Crypto
)

# Include directories
target_include_directories(${PROJECT_NAME} PRIVATE src/)

# Install
install(TARGETS ${PROJECT_NAME} DESTINATION bin)
