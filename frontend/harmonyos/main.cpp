#include "UIAdaptationBridge.h"
#include <iostream>
#include <string>
#include <vector>
#include <memory>

/**
 * Main application for HarmonyOS demonstrating UI adaptation
 */

// Forward declarations for HarmonyOS UI components
class HarmonyButton;
class HarmonyTextView;
class HarmonyLayout;

// Simple mock UI components for demonstration
class MockButton : public UIElement {
public:
    MockButton(const std::string& id) : id_(id), visible_(true) {
        std::cout << "Created button: " << id << std::endl;
    }

    void setVisible(bool visible) override {
        visible_ = visible;
        std::cout << "Button " << id_ << " visibility: " << (visible ? "shown" : "hidden") << std::endl;
    }

    void setPosition(const std::string& position) override {
        position_ = position;
        std::cout << "Button " << id_ << " position: " << position << std::endl;
    }

    void setSize(const std::string& size) override {
        size_ = size;
        std::cout << "Button " << id_ << " size: " << size << std::endl;
    }

private:
    std::string id_;
    bool visible_;
    std::string position_;
    std::string size_;
};

class MockTextView : public UIElement {
public:
    MockTextView(const std::string& id) : id_(id), visible_(true) {
        std::cout << "Created text view: " << id << std::endl;
    }

    void setVisible(bool visible) override {
        visible_ = visible;
        std::cout << "TextView " << id_ << " visibility: " << (visible ? "shown" : "hidden") << std::endl;
    }

    void setPosition(const std::string& position) override {
        position_ = position;
        std::cout << "TextView " << id_ << " position: " << position << std::endl;
    }

    void setSize(const std::string& size) override {
        size_ = size;
        std::cout << "TextView " << id_ << " size: " << size << std::endl;
    }

private:
    std::string id_;
    bool visible_;
    std::string position_;
    std::string size_;
};

// Mock UI container
class MockUIContainer {
public:
    void addElement(const std::string& id, std::shared_ptr<UIElement> element) {
        elements_[id] = element;
    }

    std::shared_ptr<UIElement> findElement(const std::string& id) {
        auto it = elements_.find(id);
        return it != elements_.end() ? it->second : nullptr;
    }

private:
    std::map<std::string, std::shared_ptr<UIElement>> elements_;
};

// Screen classes
class DashboardScreen {
public:
    DashboardScreen(MockUIContainer& container, UIAdaptationBridge& bridge)
        : container_(container), bridge_(bridge) {

        // Create UI elements
        quickActionsButton_ = std::make_shared<MockButton>("dashboard_quick_actions");
        navigationText_ = std::make_shared<MockTextView>("dashboard_navigation");

        container.addElement("dashboard_quick_actions", quickActionsButton_);
        container.addElement("dashboard_navigation", navigationText_);

        std::cout << "DashboardScreen initialized" << std::endl;
    }

    void show() {
        std::cout << "\n=== SynapseSDK HarmonyOS - Dashboard ===" << std::endl;

        // Load adaptations
        auto adaptations = bridge_.loadAdaptationsForScreen("dashboard", "demo_user");

        // Apply adaptations
        for (const auto& adaptation : adaptations) {
            bridge_.applyAdaptation(adaptation.elementId, adaptation.action,
                                  adaptation.position, adaptation.size);
        }

        // Show screen content
        showQuickActions();
        showNavigation();
        showAdaptationControls(adaptations);
    }

    void recordInteraction(const std::string& elementId, const std::string& action) {
        bridge_.recordInteraction("dashboard", elementId, action, "center");
    }

private:
    void showQuickActions() {
        std::cout << "Quick Actions: Messages, Contacts, Settings" << std::endl;
    }

    void showNavigation() {
        std::cout << "Navigation: Adapted based on usage patterns" << std::endl;
    }

    void showAdaptationControls(const std::vector<UIAdaptation>& adaptations) {
        std::cout << "\nUI Adaptation Controls:" << std::endl;
        for (const auto& adaptation : adaptations) {
            std::cout << adaptation.elementId << ": " << adaptation.action
                     << " (" << adaptation.confidence << ")" << std::endl;
        }

        auto stats = bridge_.getStats();
        std::cout << "Stats: Interactions: " << stats.totalInteractions
                 << ", Elements: " << stats.adaptedElements
                 << ", Users: " << stats.activeUsers << std::endl;
    }

    MockUIContainer& container_;
    UIAdaptationBridge& bridge_;
    std::shared_ptr<MockButton> quickActionsButton_;
    std::shared_ptr<MockTextView> navigationText_;
};

class MessagingScreen {
public:
    MessagingScreen(MockUIContainer& container, UIAdaptationBridge& bridge)
        : container_(container), bridge_(bridge) {

        // Create UI elements
        emojiPickerButton_ = std::make_shared<MockButton>("messaging_emoji_picker");

        container.addElement("messaging_emoji_picker", emojiPickerButton_);

        std::cout << "MessagingScreen initialized" << std::endl;
    }

    void show() {
        std::cout << "\n=== SynapseSDK HarmonyOS - Messaging ===" << std::endl;

        // Load adaptations
        auto adaptations = bridge_.loadAdaptationsForScreen("messaging", "demo_user");

        // Apply adaptations
        for (const auto& adaptation : adaptations) {
            bridge_.applyAdaptation(adaptation.elementId, adaptation.action,
                                  adaptation.position, adaptation.size);
        }

        // Show screen content
        showMessageInput();
        showEmojiPicker();
        showAdaptationControls(adaptations);
    }

    void recordInteraction(const std::string& elementId, const std::string& action) {
        bridge_.recordInteraction("messaging", elementId, action, "center");
    }

private:
    void showMessageInput() {
        std::cout << "Message Input: Type your message..." << std::endl;
    }

    void showEmojiPicker() {
        std::cout << "Emoji Picker: 😀 😀 😀 😀 😀 (Adapted based on usage)" << std::endl;
    }

    void showAdaptationControls(const std::vector<UIAdaptation>& adaptations) {
        std::cout << "\nUI Adaptation Controls:" << std::endl;
        for (const auto& adaptation : adaptations) {
            std::cout << adaptation.elementId << ": " << adaptation.action
                     << " (" << adaptation.confidence << ")" << std::endl;
        }

        auto stats = bridge_.getStats();
        std::cout << "Stats: Interactions: " << stats.totalInteractions
                 << ", Elements: " << stats.adaptedElements
                 << ", Users: " << stats.activeUsers << std::endl;
    }

    MockUIContainer& container_;
    UIAdaptationBridge& bridge_;
    std::shared_ptr<MockButton> emojiPickerButton_;
};

class SettingsScreen {
public:
    SettingsScreen(MockUIContainer& container, UIAdaptationBridge& bridge)
        : container_(container), bridge_(bridge) {

        // Create UI elements
        accessibilityText_ = std::make_shared<MockTextView>("settings_accessibility");
        advancedText_ = std::make_shared<MockTextView>("settings_advanced");

        container.addElement("settings_accessibility", accessibilityText_);
        container.addElement("settings_advanced", advancedText_);

        std::cout << "SettingsScreen initialized" << std::endl;
    }

    void show() {
        std::cout << "\n=== SynapseSDK HarmonyOS - Settings ===" << std::endl;

        // Load adaptations
        auto adaptations = bridge_.loadAdaptationsForScreen("settings", "demo_user");

        // Apply adaptations
        for (const auto& adaptation : adaptations) {
            bridge_.applyAdaptation(adaptation.elementId, adaptation.action,
                                  adaptation.position, adaptation.size);
        }

        // Show screen content
        showAccessibilitySettings();
        showAdvancedSettings();
        showAdaptationControls(adaptations);
    }

    void recordInteraction(const std::string& elementId, const std::string& action) {
        bridge_.recordInteraction("settings", elementId, action, "center");
    }

private:
    void showAccessibilitySettings() {
        std::cout << "Accessibility: Font size, contrast, and other accessibility options" << std::endl;
    }

    void showAdvancedSettings() {
        std::cout << "Advanced Settings: Developer options and advanced configurations" << std::endl;
    }

    void showAdaptationControls(const std::vector<UIAdaptation>& adaptations) {
        std::cout << "\nUI Adaptation Controls:" << std::endl;
        for (const auto& adaptation : adaptations) {
            std::cout << adaptation.elementId << ": " << adaptation.action
                     << " (" << adaptation.confidence << ")" << std::endl;
        }

        auto stats = bridge_.getStats();
        std::cout << "Stats: Interactions: " << stats.totalInteractions
                 << ", Elements: " << stats.adaptedElements
                 << ", Users: " << stats.activeUsers << std::endl;
    }

    MockUIContainer& container_;
    UIAdaptationBridge& bridge_;
    std::shared_ptr<MockTextView> accessibilityText_;
    std::shared_ptr<MockTextView> advancedText_;
};

// Main application class
class SynapseHarmonyApp {
public:
    SynapseHarmonyApp()
        : uiBridge_(),
          dashboard_(uiContainer_, uiBridge_),
          messaging_(uiContainer_, uiBridge_),
          settings_(uiContainer_, uiBridge_) {

        // Set up signal handlers
        uiBridge_.adaptationReady = [this](const std::vector<UIAdaptation>& adaptations) {
            onAdaptationsReady(adaptations);
        };

        uiBridge_.adaptationApplied = [this](const std::string& elementId, const std::string& action) {
            onAdaptationApplied(elementId, action);
        };

        std::cout << "SynapseHarmonyApp initialized" << std::endl;
    }

    void run() {
        std::cout << "=== SynapseSDK HarmonyOS Demo ===" << std::endl;
        std::cout << "Commands: 'dashboard', 'messaging', 'settings', 'interact <element> <action>', 'feedback <element> <score>', 'quit'" << std::endl;

        std::string command;
        while (true) {
            std::cout << "\n> ";
            std::getline(std::cin, command);

            if (command == "quit" || command == "exit") {
                break;
            } else if (command == "dashboard") {
                currentScreen_ = "dashboard";
                dashboard_.show();
            } else if (command == "messaging") {
                currentScreen_ = "messaging";
                messaging_.show();
            } else if (command == "settings") {
                currentScreen_ = "settings";
                settings_.show();
            } else if (command.substr(0, 8) == "interact") {
                handleInteractCommand(command);
            } else if (command.substr(0, 8) == "feedback") {
                handleFeedbackCommand(command);
            } else {
                std::cout << "Unknown command. Try: dashboard, messaging, settings, interact <element> <action>, feedback <element> <score>, quit" << std::endl;
            }
        }
    }

private:
    void handleInteractCommand(const std::string& command) {
        // Parse: interact <element> <action>
        size_t firstSpace = command.find(' ');
        size_t secondSpace = command.find(' ', firstSpace + 1);

        if (firstSpace == std::string::npos || secondSpace == std::string::npos) {
            std::cout << "Invalid interact command. Use: interact <element> <action>" << std::endl;
            return;
        }

        std::string element = command.substr(firstSpace + 1, secondSpace - firstSpace - 1);
        std::string action = command.substr(secondSpace + 1);

        if (currentScreen_ == "dashboard") {
            dashboard_.recordInteraction(element, action);
        } else if (currentScreen_ == "messaging") {
            messaging_.recordInteraction(element, action);
        } else if (currentScreen_ == "settings") {
            settings_.recordInteraction(element, action);
        }

        std::cout << "Recorded interaction: " << element << " -> " << action << std::endl;
    }

    void handleFeedbackCommand(const std::string& command) {
        // Parse: feedback <element> <score>
        size_t firstSpace = command.find(' ');
        size_t secondSpace = command.find(' ', firstSpace + 1);

        if (firstSpace == std::string::npos || secondSpace == std::string::npos) {
            std::cout << "Invalid feedback command. Use: feedback <element> <score>" << std::endl;
            return;
        }

        std::string element = command.substr(firstSpace + 1, secondSpace - firstSpace - 1);
        float score = std::stof(command.substr(secondSpace + 1));

        uiBridge_.provideFeedback(element, score);
        std::cout << "Provided feedback: " << element << " = " << score << std::endl;
    }

    void onAdaptationsReady(const std::vector<UIAdaptation>& adaptations) {
        std::cout << "Adaptations ready: " << adaptations.size() << " adaptations" << std::endl;
    }

    void onAdaptationApplied(const std::string& elementId, const std::string& action) {
        std::cout << "Adaptation applied: " << elementId << " -> " << action << std::endl;
    }

    UIAdaptationBridge uiBridge_;
    MockUIContainer uiContainer_;
    DashboardScreen dashboard_;
    MessagingScreen messaging_;
    SettingsScreen settings_;
    std::string currentScreen_;
};

int main(int argc, char* argv[]) {
    try {
        SynapseHarmonyApp app;
        app.run();
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}
