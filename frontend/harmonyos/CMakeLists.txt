cmake_minimum_required(VERSION 3.16)

project(SynapseSDK_HarmonyOS VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# HarmonyOS specific settings
set(OHOS_SDK_PATH "$ENV{OHOS_SDK_HOME}")
if(NOT OHOS_SDK_PATH)
    message(FATAL_ERROR "OHOS_SDK_HOME environment variable not set")
endif()

include_directories(${OHOS_SDK_PATH}/native/include)

add_executable(SynapseSDK_HarmonyOS
    main.cpp
    app_ability.cpp
)

target_link_libraries(SynapseSDK_HarmonyOS
    PRIVATE ${OHOS_SDK_PATH}/native/libs/${CMAKE_SYSTEM_PROCESSOR}/libace_napi.z.so
)

include(GNUInstallDirs)
install(TARGETS SynapseSDK_HarmonyOS
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
