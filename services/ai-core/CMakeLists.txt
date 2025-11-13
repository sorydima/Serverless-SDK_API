cmake_minimum_required(VERSION 3.16)
project(ai-core-service)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find userver
find_package(userver REQUIRED)

# Find additional libraries
find_package(OpenSSL REQUIRED)
find_package(Threads REQUIRED)

# Add executable
add_executable(${PROJECT_NAME}
    src/main.cpp
    src/ai_core_handler.cpp
    src/model_manager.cpp
    src/inference_engine.cpp
    src/quantum_processor.cpp
)

# Link libraries
target_link_libraries(${PROJECT_NAME}
    userver::core
    OpenSSL::SSL
    OpenSSL::Crypto
    Threads::Threads
)

# Include directories
target_include_directories(${PROJECT_NAME} PRIVATE src/)

# Install
install(TARGETS ${PROJECT_NAME} DESTINATION bin)
