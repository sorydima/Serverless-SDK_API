cmake_minimum_required(VERSION 3.16)
project(mesh-gateway-service)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find userver
find_package(userver REQUIRED)

# Add executable
add_executable(${PROJECT_NAME}
    src/main.cpp
    src/mesh_gateway_handler.cpp
    src/device_discovery.cpp
    src/routing_engine.cpp
)

# Link userver components
target_link_libraries(${PROJECT_NAME} userver::core)

# Include directories
target_include_directories(${PROJECT_NAME} PRIVATE src/)

# Install
install(TARGETS ${PROJECT_NAME} DESTINATION bin)
