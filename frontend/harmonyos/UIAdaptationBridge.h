#ifndef UI_ADAPTATION_BRIDGE_H
#define UI_ADAPTATION_BRIDGE_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <mutex>
#include <thread>
#include <chrono>
#include <functional>
#include <nlohmann/json.hpp>

// Forward declarations
class UIElement;

/**
 * Data structures for UI adaptation
 */
struct UIElementConfig {
    std::string elementId;
    std::string defaultPosition;
    bool defaultVisibility;
    float adaptationWeight;
};

struct InteractionEvent {
    std::string screenName;
    std::string elementId;
    std::string action;
    std::string position;
    std::chrono::system_clock::time_point timestamp;
};

struct UIAdaptation {
    std::string elementId;
    std::string action;
    std::string position;
    std::string size;
    float confidence;
    std::string reasoning;
};

struct AdaptationFeedback {
    std::string elementId;
    std::string userId;
    float feedback;
    std::chrono::system_clock::time_point timestamp;
};

struct AdaptationStats {
    int totalInteractions;
    int adaptedElements;
    int activeUsers;
};

/**
 * UI Adaptation Bridge for HarmonyOS
 *
 * Integrates reinforcement learning-based UI adaptation with HarmonyOS UI components.
 */
class UIAdaptationBridge {
public:
    UIAdaptationBridge();
    ~UIAdaptationBridge();

    // Interaction recording
    void recordInteraction(const std::string& screenName,
                          const std::string& elementId,
                          const std::string& action,
                          const std::string& position = "center");

    // Adaptation calculation
    std::vector<UIAdaptation> getAdaptations(const std::string& screenName,
                                           const std::string& userId = "");

    // UI manipulation
    void applyAdaptation(const std::string& elementId,
                        const std::string& action,
                        const std::string& position = "",
                        const std::string& size = "");

    // Feedback system
    void provideFeedback(const std::string& elementId,
                        float feedback,
                        const std::string& userId = "");

    // Statistics
    AdaptationStats getStats();

    // Convenience methods
    std::vector<UIAdaptation> loadAdaptationsForScreen(const std::string& screenName,
                                                     const std::string& userId = "");

    // Signals (implemented as callbacks in C++)
    std::function<void(const std::vector<UIAdaptation>&)> adaptationReady;
    std::function<void(const std::string&, const std::string&)> adaptationApplied;

private:
    // Configuration
    void initializeConfigs();

    // Adaptation calculation
    UIAdaptation calculateAdaptation(const UIElementConfig& config,
                                   const std::vector<InteractionEvent>& interactions,
                                   const nlohmann::json& userPrefs);

    // UI element management
    std::shared_ptr<UIElement> findElement(const std::string& elementId);

    // State management
    void updateAdaptationState(const InteractionEvent& event);
    void loadSavedState();
    void saveState();

    // User preferences
    nlohmann::json loadUserPreferences(const std::string& userId);
    void updateUserPreferences(const std::string& userId,
                             const std::string& elementId,
                             float feedback);

    // Feedback storage
    void storeFeedback(const AdaptationFeedback& feedback);

private:
    std::string currentUserId_;
    std::map<std::string, UIElementConfig> uiConfigs_;
    std::vector<InteractionEvent> interactionHistory_;
    nlohmann::json adaptationState_;

    // Threading
    std::mutex historyMutex_;
    std::mutex stateMutex_;
    std::thread saveThread_;
    bool running_;
};

/**
 * Placeholder UI Element class
 * In a real implementation, this would integrate with HarmonyOS UI framework
 */
class UIElement {
public:
    virtual ~UIElement() = default;
    virtual void setVisible(bool visible) = 0;
    virtual void setPosition(const std::string& position) = 0;
    virtual void setSize(const std::string& size) = 0;
};

#endif // UI_ADAPTATION_BRIDGE_H
