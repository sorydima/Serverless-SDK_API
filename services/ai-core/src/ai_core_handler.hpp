#pragma once

#include <userver/server/handlers/http_handler_json_base.hpp>
#include <userver/formats/json.hpp>
#include <userver/logging/log.hpp>

#include <memory>
#include <unordered_map>
#include <string>
#include <vector>

namespace ai_core {

struct ModelInfo {
    std::string model_id;
    std::string model_type;
    std::string status;
    double accuracy;
    std::chrono::system_clock::time_point last_used;
    size_t memory_usage_mb;
};

struct InferenceRequest {
    std::string model_id;
    userver::formats::json::Value input_data;
    std::string request_id;
    std::chrono::system_clock::time_point timestamp;
};

struct InferenceResult {
    std::string request_id;
    bool success;
    userver::formats::json::Value output_data;
    double confidence;
    double processing_time_ms;
    std::string error_message;
};

class ModelManager;
class InferenceEngine;
class QuantumProcessor;

class AICoreHandler : public userver::server::handlers::HttpHandlerJsonBase {
public:
    static constexpr std::string_view kName = "ai-core-handler";

    AICoreHandler(const userver::components::ComponentConfig& config,
                  const userver::components::ComponentContext& context);

    userver::formats::json::Value HandleRequestJson(
        const userver::server::http::HttpRequest& request,
        const userver::formats::json::Value& request_json) const override;

private:
    userver::formats::json::Value HandleGetModels(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleLoadModel(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleUnloadModel(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleRunInference(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleGetInferenceStatus(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleTrainModel(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleGetQuantumStatus(
        const userver::formats::json::Value& request_json) const;

    std::shared_ptr<ModelManager> model_manager_;
    std::shared_ptr<InferenceEngine> inference_engine_;
    std::shared_ptr<QuantumProcessor> quantum_processor_;

    mutable std::unordered_map<std::string, InferenceResult> inference_results_;
};

}  // namespace ai_core
