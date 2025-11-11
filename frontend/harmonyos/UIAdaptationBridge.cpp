#include "UIAdaptationBridge.h"
#include <iostream>
#include <fstream>
#include <nlohmann/json.hpp>
#include <chrono>
#include <thread>
#include <algorithm>

using json = nlohmann::json;

/**
 * UI Adaptation Bridge for HarmonyOS
 *
 * Integrates reinforcement learning-based UI adaptation with HarmonyOS UI components.
 * Provides seamless adaptation of UI elements based on user behavior patterns.
 */

UIAdaptationBridge::UIAdaptationBridge()
    : currentUserId_("default_user"),
      running_(true) {

    initializeConfigs();
    loadSavedState();

    // Start background save thread
    saveThread_ = std::thread([this]() {
        while (running_) {
            std::this_thread::sleep_for(std::chrono::seconds(30)); // Save every 30 seconds
            saveState();
        }
    });

    std::cout << "UIAdaptationBridge initialized for HarmonyOS" << std::endl;
}

UIAdaptationBridge::~UIAdaptationBridge() {
    running_ = false;
    if (saveThread_.joinable()) {
        saveThread_.join();
    }
    saveState();
}

/**
 * Initialize default UI element configurations
 */
void UIAdaptationBridge::initializeConfigs() {
    uiConfigs_["dashboard_quick_actions"] = UIElementConfig{
        "dashboard_quick_actions", "top", true, 0.8f
    };
    uiConfigs_["dashboard_navigation"] = UIElementConfig{
        "dashboard_navigation", "bottom", true, 0.9f
    };
    uiConfigs_["messaging_input_field"] = UIElementConfig{
        "messaging_input_field", "bottom", true, 0.7f
    };
    uiConfigs_["messaging_emoji_picker"] = UIElementConfig{
        "messaging_emoji_picker", "bottom", false, 0.6f
    };
    uiConfigs_["settings_advanced"] = UIElementConfig{
        "settings_advanced", "bottom", false, 0.5f
    };
    uiConfigs_["settings_accessibility"] = UIElementConfig{
        "settings_accessibility", "top", true, 0.8f
    };
}

/**
 * Record user interaction for learning
 */
void UIAdaptationBridge::recordInteraction(const std::string& screenName,
                                         const std::string& elementId,
                                         const std::string& action,
                                         const std::string& position) {
    InteractionEvent event{
        screenName,
        elementId,
        action,
        position,
        std::chrono::system_clock::now()
    };

    {
        std::lock_guard<std::mutex> lock(historyMutex_);
        interactionHistory_.push_back(event);

        // Keep only recent history
        if (interactionHistory_.size() > 1000) {
            interactionHistory_.erase(interactionHistory_.begin());
        }
    }

    // Update adaptation state
    updateAdaptationState(event);

    // Save state periodically
    static int interactionCount = 0;
    if (++interactionCount % 100 == 0) {
        saveState();
    }
}

/**
 * Get adaptation recommendations for current context
 */
std::vector<UIAdaptation> UIAdaptationBridge::getAdaptations(const std::string& screenName,
                                                            const std::string& userId) {
    std::string uid = userId.empty() ? currentUserId_ : userId;
    std::vector<UIAdaptation> adaptations;

    // Get user preferences
    auto userPrefs = loadUserPreferences(uid);

    // Get recent interactions for this screen
    std::vector<InteractionEvent> screenInteractions;
    {
        std::lock_guard<std::mutex> lock(historyMutex_);
        for (const auto& interaction : interactionHistory_) {
            if (interaction.screenName == screenName) {
                screenInteractions.push_back(interaction);
            }
        }
        // Keep only last 50
        if (screenInteractions.size() > 50) {
            screenInteractions.erase(screenInteractions.begin(),
                                   screenInteractions.end() - 50);
        }
    }

    // Generate adaptations
    for (const auto& configPair : uiConfigs_) {
        const auto& elementId = configPair.first;
        const auto& config = configPair.second;

        if (elementId.find(screenName + "_") == 0 || elementId.find(screenName) != std::string::npos) {
            auto adaptation = calculateAdaptation(config, screenInteractions, userPrefs);
            adaptations.push_back(adaptation);
        }
    }

    // Sort by confidence
    std::sort(adaptations.begin(), adaptations.end(),
              [](const UIAdaptation& a, const UIAdaptation& b) {
                  return a.confidence > b.confidence;
              });

    return adaptations;
}

/**
 * Calculate adaptation for a specific UI element
 */
UIAdaptation UIAdaptationBridge::calculateAdaptation(const UIElementConfig& config,
                                                    const std::vector<InteractionEvent>& interactions,
                                                    const json& userPrefs) {
    float visibilityScore = 0.5f;
    float positionScore = 0.5f;

    // Analyze interaction patterns
    std::vector<InteractionEvent> elementInteractions;
    for (const auto& interaction : interactions) {
        if (interaction.elementId == config.elementId) {
            elementInteractions.push_back(interaction);
        }
    }

    if (!elementInteractions.empty()) {
        // Visibility adaptation based on usage
        float usageRate = static_cast<float>(elementInteractions.size()) / interactions.size();
        visibilityScore = std::max(0.0f, std::min(1.0f, usageRate * config.adaptationWeight));

        // Position adaptation based on interaction patterns
        std::map<std::string, int> positionCounts;
        for (const auto& interaction : elementInteractions) {
            positionCounts[interaction.position]++;
        }

        std::string preferredPosition = config.defaultPosition;
        int maxCount = 0;
        for (const auto& pair : positionCounts) {
            if (pair.second > maxCount) {
                maxCount = pair.second;
                preferredPosition = pair.first;
            }
        }

        positionScore = (preferredPosition == config.defaultPosition) ? 0.8f : 0.6f;
    }

    // Apply user preferences
    bool userVisibilityPref = config.defaultVisibility;
    if (userPrefs.contains(config.elementId + "_visible")) {
        userVisibilityPref = userPrefs[config.elementId + "_visible"];
    }

    bool finalVisibility = visibilityScore > 0.7f ? true :
                          visibilityScore < 0.3f ? false : userVisibilityPref;

    UIAdaptation adaptation{
        config.elementId,
        finalVisibility ? "show" : "hide",
        config.defaultPosition,
        "",
        (visibilityScore + positionScore) / 2.0f,
        "Based on " + std::to_string(elementInteractions.size()) +
        " interactions, usage rate: " + std::to_string(visibilityScore)
    };

    return adaptation;
}

/**
 * Apply UI adaptation
 */
void UIAdaptationBridge::applyAdaptation(const std::string& elementId,
                                       const std::string& action,
                                       const std::string& position,
                                       const std::string& size) {
    // Find the element in the UI tree
    auto element = findElement(elementId);
    if (!element) {
        std::cerr << "Element not found: " << elementId << std::endl;
        return;
    }

    try {
        if (action == "show") {
            element->setVisible(true);
            if (!position.empty()) {
                // Position logic would be implemented based on layout
                std::cout << "Showing element: " << elementId << " at " << position << std::endl;
            }
        } else if (action == "hide") {
            element->setVisible(false);
            std::cout << "Hiding element: " << elementId << std::endl;
        } else if (action == "move") {
            if (!position.empty()) {
                // Move logic would be implemented
                std::cout << "Moving element: " << elementId << " to " << position << std::endl;
            }
        } else if (action == "resize") {
            if (!size.empty()) {
                // Resize logic would be implemented
                std::cout << "Resizing element: " << elementId << " to " << size << std::endl;
            }
        }

        // Emit signal
        adaptationApplied(elementId, action);

    } catch (const std::exception& e) {
        std::cerr << "Failed to apply adaptation: " << elementId << ": " << e.what() << std::endl;
    }
}

/**
 * Find UI element by ID
 */
std::shared_ptr<UIElement> UIAdaptationBridge::findElement(const std::string& elementId) {
    // This would need to be implemented to traverse the UI object tree
    // For now, return nullptr as a placeholder
    std::cout << "Looking for element: " << elementId << std::endl;
    return nullptr;
}

/**
 * Provide feedback on adaptation effectiveness
 */
void UIAdaptationBridge::provideFeedback(const std::string& elementId,
                                       float feedback,
                                       const std::string& userId) {
    std::string uid = userId.empty() ? currentUserId_ : userId;

    AdaptationFeedback fb{
        elementId,
        uid,
        feedback,
        std::chrono::system_clock::now()
    };

    // Store feedback for learning
    storeFeedback(fb);

    // Update user preferences
    updateUserPreferences(uid, elementId, feedback);
}

/**
 * Update adaptation state based on interaction
 */
void UIAdaptationBridge::updateAdaptationState(const InteractionEvent& event) {
    std::string stateKey = event.screenName + "_" + event.elementId;

    std::lock_guard<std::mutex> lock(stateMutex_);
    auto& state = adaptationState_[stateKey];
    state["interactions"] = state.value("interactions", 0) + 1;
    state["last_interaction"] = std::chrono::duration_cast<std::chrono::milliseconds>(
        event.timestamp.time_since_epoch()).count();
    state["position"] = event.position;
}

/**
 * Load saved adaptation state
 */
void UIAdaptationBridge::loadSavedState() {
    try {
        std::ifstream file("adaptation_state.json");
        if (file.is_open()) {
            json stateJson;
            file >> stateJson;
            adaptationState_ = stateJson;
            std::cout << "Loaded adaptation state for " << adaptationState_.size() << " elements" << std::endl;
        }
    } catch (const std::exception& e) {
        std::cerr << "Failed to load adaptation state: " << e.what() << std::endl;
    }
}

/**
 * Save current adaptation state
 */
void UIAdaptationBridge::saveState() {
    try {
        std::lock_guard<std::mutex> lock(stateMutex_);
        std::ofstream file("adaptation_state.json");
        if (file.is_open()) {
            file << adaptationState_.dump(4);
            std::cout << "Saved adaptation state" << std::endl;
        }
    } catch (const std::exception& e) {
        std::cerr << "Failed to save adaptation state: " << e.what() << std::endl;
    }
}

/**
 * Load user preferences
 */
json UIAdaptationBridge::loadUserPreferences(const std::string& userId) {
    try {
        std::ifstream file("user_prefs_" + userId + ".json");
        if (file.is_open()) {
            json prefs;
            file >> prefs;
            return prefs;
        }
    } catch (const std::exception& e) {
        std::cerr << "Failed to load user preferences for " << userId << ": " << e.what() << std::endl;
    }
    return json{};
}

/**
 * Update user preferences based on feedback
 */
void UIAdaptationBridge::updateUserPreferences(const std::string& userId,
                                             const std::string& elementId,
                                             float feedback) {
    try {
        auto prefs = loadUserPreferences(userId);

        // Update preference score
        std::string prefKey = elementId + "_pref";
        double currentPref = prefs.value(prefKey, 0.5);
        double newPref = currentPref * 0.8 + feedback * 0.2; // Weighted average
        prefs[prefKey] = newPref;

        // Save updated preferences
        std::ofstream file("user_prefs_" + userId + ".json");
        if (file.is_open()) {
            file << prefs.dump(4);
            std::cout << "Updated preferences for " << userId << std::endl;
        }
    } catch (const std::exception& e) {
        std::cerr << "Failed to update user preferences: " << e.what() << std::endl;
    }
}

/**
 * Store feedback for learning
 */
void UIAdaptationBridge::storeFeedback(const AdaptationFeedback& feedback) {
    // In a real implementation, this would send feedback to the RL model
    std::cout << "Feedback received: " << feedback.elementId << " = " << feedback.feedback << std::endl;
}

/**
 * Get adaptation statistics
 */
AdaptationStats UIAdaptationBridge::getStats() {
    std::lock_guard<std::mutex> lock(historyMutex_);
    return {
        static_cast<int>(interactionHistory_.size()),
        static_cast<int>(adaptationState_.size()),
        1 // Placeholder for active users
    };
}

/**
 * Load adaptations for a screen (convenience method)
 */
std::vector<UIAdaptation> UIAdaptationBridge::loadAdaptationsForScreen(const std::string& screenName,
                                                                     const std::string& userId) {
    auto adaptations = getAdaptations(screenName, userId);
    adaptationReady(adaptations);
    return adaptations;
}
