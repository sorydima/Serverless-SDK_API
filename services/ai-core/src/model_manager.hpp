#pragma once

#include "ai_core_handler.hpp"

#include <vector>
#include <unordered_map>
#include <memory>
#include <mutex>

namespace ai_core {

class ModelManager {
public:
    ModelManager();
    ~ModelManager() = default;

    std::vector<ModelInfo> GetAvailableModels() const;
    bool LoadModel(const std::string& model_id);
    bool UnloadModel(const std::string& model_id);
    bool IsModelLoaded(const std::string& model_id) const;

private:
    void InitializeDefaultModels();

    mutable std::mutex models_mutex_;
    std::unordered_map<std::string, ModelInfo> available_models_;
    std::unordered_set<std::string> loaded_models_;
};

}  // namespace ai_core
