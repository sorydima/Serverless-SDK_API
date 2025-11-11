cmake_minimum_required(VERSION 3.16)

project(SynapseSDK_AuroraOS VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 REQUIRED COMPONENTS Core Quick)

qt_standard_project_setup()

qt_add_executable(SynapseSDK_AuroraOS
    main.cpp
    resources.qrc
)

qt_add_qml_module(SynapseSDK_AuroraOS
    URI SynapseSDK
    VERSION 1.0
    QML_FILES
        Main.qml
)

target_link_libraries(SynapseSDK_AuroraOS
    PRIVATE Qt6::Core Qt6::Quick
)

include(GNUInstallDirs)
install(TARGETS SynapseSDK_AuroraOS
    BUNDLE DESTINATION .
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
