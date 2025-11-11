import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    width: 800
    height: 600
    visible: true
    title: qsTr("SynapseSDK AuroraOS")

    // UI Adaptation Bridge
    UIAdaptationBridge {
        id: uiBridge
    }

    property var currentScreen: "dashboard"
    property var currentAdaptations: []

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        // Screen selector
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: 10

            Button {
                text: "Dashboard"
                onClicked: switchScreen("dashboard")
            }
            Button {
                text: "Messaging"
                onClicked: switchScreen("messaging")
            }
            Button {
                text: "Settings"
                onClicked: switchScreen("settings")
            }
        }

        // Adaptive content area
        StackLayout {
            id: contentStack
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 10

            // Dashboard screen
            DashboardScreen {
                id: dashboardScreen
                adaptations: currentAdaptations
                onInteractionRecorded: function(elementId, action) {
                    uiBridge.recordInteraction(currentScreen, elementId, action, "center")
                }
            }

            // Messaging screen
            MessagingScreen {
                id: messagingScreen
                adaptations: currentAdaptations
                onInteractionRecorded: function(elementId, action) {
                    uiBridge.recordInteraction(currentScreen, elementId, action, "center")
                }
            }

            // Settings screen
            SettingsScreen {
                id: settingsScreen
                adaptations: currentAdaptations
                onInteractionRecorded: function(elementId, action) {
                    uiBridge.recordInteraction(currentScreen, elementId, action, "center")
                }
            }
        }

        // Adaptation controls
        AdaptationControls {
            Layout.fillWidth: true
            Layout.margins: 10
            adaptations: currentAdaptations
            stats: uiBridge.getStats()
            onFeedbackGiven: function(elementId, feedback) {
                uiBridge.provideFeedback(elementId, feedback)
                refreshAdaptations()
            }
        }
    }

    function switchScreen(screenName) {
        currentScreen = screenName
        contentStack.currentIndex = getScreenIndex(screenName)
        refreshAdaptations()

        // Record screen view
        uiBridge.recordInteraction(screenName, "screen_view", "view", "center")
    }

    function getScreenIndex(screenName) {
        switch (screenName) {
            case "dashboard": return 0
            case "messaging": return 1
            case "settings": return 2
            default: return 0
        }
    }

    function refreshAdaptations() {
        currentAdaptations = uiBridge.getAdaptations(currentScreen, "demo_user")
        console.log("Loaded " + currentAdaptations.length + " adaptations for " + currentScreen)
    }

    Component.onCompleted: {
        refreshAdaptations()
    }
}

// Dashboard Screen Component
Item {
    id: dashboardScreen
    property var adaptations: []
    signal interactionRecorded(string elementId, string action)

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        Text {
            text: "SynapseSDK AuroraOS - Dashboard"
            font.pixelSize: 24
            Layout.alignment: Qt.AlignHCenter
        }

        // Quick Actions (adaptable)
        Rectangle {
            id: quickActionsRect
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            color: "lightblue"
            border.color: "blue"
            visible: getAdaptationVisibility("dashboard_quick_actions")

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10

                Text {
                    text: "Quick Actions"
                    font.pixelSize: 18
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Button {
                        text: "Messages"
                        onClicked: interactionRecorded("dashboard_quick_actions", "messages")
                    }
                    Button {
                        text: "Contacts"
                        onClicked: interactionRecorded("dashboard_quick_actions", "contacts")
                    }
                    Button {
                        text: "Settings"
                        onClicked: interactionRecorded("dashboard_quick_actions", "settings")
                    }
                }
            }
        }

        // Navigation (adaptable)
        Rectangle {
            id: navigationRect
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: "lightgreen"
            border.color: "green"
            visible: getAdaptationVisibility("dashboard_navigation")

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10

                Text {
                    text: "Navigation"
                    font.pixelSize: 18
                }

                Text {
                    text: "Navigation content adapted based on usage patterns"
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
            }
        }

        Item { Layout.fillHeight: true } // Spacer
    }

    function getAdaptationVisibility(elementId) {
        var adaptation = adaptations.find(function(a) { return a.elementId === elementId })
        return !adaptation || adaptation.action !== "hide"
    }
}

// Messaging Screen Component
Item {
    id: messagingScreen
    property var adaptations: []
    signal interactionRecorded(string elementId, string action)

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        Text {
            text: "SynapseSDK AuroraOS - Messaging"
            font.pixelSize: 24
            Layout.alignment: Qt.AlignHCenter
        }

        // Message Input
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: "lightyellow"
            border.color: "orange"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10

                Text {
                    text: "Message Input"
                    font.pixelSize: 18
                }

                TextField {
                    Layout.fillWidth: true
                    placeholderText: "Type your message..."
                }
            }
        }

        // Emoji Picker (adaptable)
        Rectangle {
            id: emojiPickerRect
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            color: "lightpink"
            border.color: "red"
            visible: getAdaptationVisibility("messaging_emoji_picker")

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10

                Text {
                    text: "Emoji Picker"
                    font.pixelSize: 18
                }

                Text {
                    text: "😀 😀 😀 😀 😀 (Adapted based on usage)"
                    font.pixelSize: 24
                }

                Button {
                    text: "Select Emoji"
                    onClicked: interactionRecorded("messaging_emoji_picker", "select")
                }
            }
        }

        Item { Layout.fillHeight: true } // Spacer
    }

    function getAdaptationVisibility(elementId) {
        var adaptation = adaptations.find(function(a) { return a.elementId === elementId })
        return !adaptation || adaptation.action !== "hide"
    }
}

// Settings Screen Component
Item {
    id: settingsScreen
    property var adaptations: []
    signal interactionRecorded(string elementId, string action)

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        Text {
            text: "SynapseSDK AuroraOS - Settings"
            font.pixelSize: 24
            Layout.alignment: Qt.AlignHCenter
        }

        // Accessibility Settings (adaptable)
        Rectangle {
            id: accessibilityRect
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: "lightcyan"
            border.color: "teal"
            visible: getAdaptationVisibility("settings_accessibility")

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10

                Text {
                    text: "Accessibility"
                    font.pixelSize: 18
                }

                RowLayout {
                    CheckBox {
                        text: "High Contrast"
                        checked: true
                    }
                    CheckBox {
                        text: "Large Text"
                        checked: false
                    }
                }
            }
        }

        // Advanced Settings (adaptable - often hidden)
        Rectangle {
            id: advancedRect
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: "lightgray"
            border.color: "gray"
            visible: getAdaptationVisibility("settings_advanced")

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10

                Text {
                    text: "Advanced Settings"
                    font.pixelSize: 18
                }

                RowLayout {
                    CheckBox {
                        text: "Developer Mode"
                        checked: false
                    }
                    CheckBox {
                        text: "Debug Logging"
                        checked: false
                    }
                }
            }
        }

        Item { Layout.fillHeight: true } // Spacer
    }

    function getAdaptationVisibility(elementId) {
        var adaptation = adaptations.find(function(a) { return a.elementId === elementId })
        return !adaptation || adaptation.action !== "hide"
    }
}

// Adaptation Controls Component
Item {
    id: adaptationControls
    property var adaptations: []
    property var stats: ({})
    signal feedbackGiven(string elementId, real feedback)

    Layout.preferredHeight: 150

    Rectangle {
        anchors.fill: parent
        color: "whitesmoke"
        border.color: "black"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10

            Text {
                text: "UI Adaptation Controls"
                font.pixelSize: 18
                font.bold: true
            }

            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: adaptations
                delegate: RowLayout {
                    width: parent.width
                    Text {
                        text: modelData.elementId + ": " + modelData.action + " (" + modelData.confidence.toFixed(2) + ")"
                        Layout.fillWidth: true
                    }
                    Button {
                        text: "👍"
                        onClicked: feedbackGiven(modelData.elementId, 1.0)
                    }
                    Button {
                        text: "👎"
                        onClicked: feedbackGiven(modelData.elementId, 0.0)
                    }
                }
            }

            Text {
                text: "Stats: Interactions: " + (stats.totalInteractions || 0) +
                      ", Elements: " + (stats.adaptedElements || 0) +
                      ", Users: " + (stats.activeUsers || 0)
                font.pixelSize: 12
                color: "gray"
            }
        }
    }
}
