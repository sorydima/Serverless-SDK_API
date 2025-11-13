#include "ai_core_handler.hpp"
#include "model_manager.hpp"
#include "inference_engine.hpp"
#include "quantum_processor.hpp"

#include <userver/http/common_headers.hpp>
#include <userver/formats/json/serialize.hpp>

namespace ai_core {

AICoreHandler::AICoreHandler(
    const userver::components::ComponentConfig& config,
    const userver::components::ComponentContext& context)
    : HttpHandlerJsonBase(config, context) {

    model_manager_ = std::make_shared<ModelManager>();
    inference_engine_ = std::make_shared<InferenceEngine>();
    quantum_processor_ = std::make_shared<QuantumProcessor>();

    LOG_INFO() << "AI Core Handler initialized";
}

userver::formats::json::Value AICoreHandler::HandleRequestJson(
    const userver::server::http::HttpRequest& request,
    const userver::formats::json::Value& request_json) const {

    const auto& method = request.GetMethod();
    const auto& path = request.GetPath();

    LOG_DEBUG() << "Received AI request: " << method << " " << path;

    // Route to appropriate handler based on path
    if (path == "/models") {
        return HandleGetModels(request_json);
    } else if (path == "/models/load" && method == userver::http::HttpMethod::kPost) {
        return HandleLoadModel(request_json);
    } else if (path == "/models/unload" && method == userver::http::HttpMethod::kPost) {
        return HandleUnloadModel(request_json);
    } else if (path == "/inference" && method == userver::http::HttpMethod::kPost) {
        return HandleRunInference(request_json);
    } else if (path == "/inference/status") {
        return HandleGetInferenceStatus(request_json);
    } else if (path == "/train" && method == userver::http::HttpMethod::kPost) {
        return HandleTrainModel(request_json);
    } else if (path == "/quantum/status") {
        return HandleGetQuantumStatus(request_json);
    }

    return userver::formats::json::MakeObject("error", "Unknown AI endpoint");
}

userver::formats::json::Value AICoreHandler::HandleGetModels(
    const userver::formats::json::Value& request_json) const {

    auto models = model_manager_->GetAvailableModels();

    userver::formats::json::ValueBuilder response;
    response["status"] = "success";
    response["model_count"] = models.size();

    userver::formats::json::ValueBuilder model_list;
    for (const auto& model : models) {
        userver::formats::json::ValueBuilder model_json;
        model_json["model_id"] = model.model_id;
        model_json["model_type"] = model.model_type;
        model_json["status"] = model.status;
        model_json["accuracy"] = model.accuracy;
        model_json["memory_usage_mb"] = static_cast<int>(model.memory_usage_mb);
        model_json["last_used"] = std::chrono::duration_cast<std::chrono::seconds>(
            model.last_used.time_since_epoch()).count();

        model_list.PushBack(model_json.ExtractValue());
    }

    response["models"] = model_list.ExtractValue();
    return response.ExtractValue();
}

userver::formats::json::Value AICoreHandler::HandleLoadModel(
    const userver::formats::json::Value& request_json) const {

    const auto model_id = request_json["model_id"].As<std::string>("");

    if (model_id.empty()) {
        return userver::formats::json::MakeObject("error", "model_id required");
    }

    bool success = model_manager_->LoadModel(model_id);

    userver::formats::json::ValueBuilder response;
    response["success"] = success;
    if (success) {
        response["status"] = "model_loaded";
        response["model_id"] = model_id;
    } else {
        response["status"] = "load_failed";
        response["error"] = "Unable to load model";
    }

    return response.ExtractValue();
}

userver::formats::json::Value AICoreHandler::HandleUnloadModel(
    const userver::formats::json::Value& request_json) const {

    const auto model_id = request_json["model_id"].As<std::string>("");

    if (model_id.empty()) {
        return userver::formats::json::MakeObject("error", "model_id required");
    }

    bool success = model_manager_->UnloadModel(model_id);

    userver::formats::json::ValueBuilder response;
    response["success"] = success;
    if (success) {
        response["status"] = "model_unloaded";
        response["model_id"] = model_id;
    } else {
        response["status"] = "unload_failed";
        response["error"] = "Unable to unload model";
    }

    return response.ExtractValue();
}

userver::formats::json::Value AICoreHandler::HandleRunInference(
    const userver::formats::json::Value& request_json) const {

    const auto model_id = request_json["model_id"].As<std::string>("");
    const auto request_id = request_json["request_id"].As<std::string>("");

    if (model_id.empty()) {
        return userver::formats::json::MakeObject("error", "model_id required");
    }

    InferenceRequest inference_req;
    inference_req.model_id = model_id;
    inference_req.input_data = request_json["input"];
    inference_req.request_id = request_id.empty() ?
        "req_" + std::to_string(std::rand()) : request_id;
    inference_req.timestamp = std::chrono::system_clock::now();

    // Run inference asynchronously
    auto result = inference_engine_->RunInference(inference_req);

    // Store result for status checking
    inference_results_[result.request_id] = result;

    userver::formats::json::ValueBuilder response;
    response["request_id"] = result.request_id;
    response["status"] = result.success ? "completed" : "failed";
    response["processing_time_ms"] = result.processing_time_ms;

    if (result.success) {
        response["output"] = result.output_data;
        response["confidence"] = result.confidence;
    } else {
        response["error"] = result.error_message;
    }

    return response.ExtractValue();
}

userver::formats::json::Value AICoreHandler::HandleGetInferenceStatus(
    const userver::formats::json::Value& request_json) const {

    const auto request_id = request_json["request_id"].As<std::string>("");

    if (request_id.empty()) {
        return userver::formats::json::MakeObject("error", "request_id required");
    }

    auto result_it = inference_results_.find(request_id);
    if (result_it == inference_results_.end()) {
        return userver::formats::json::MakeObject("error", "Request not found");
    }

    const auto& result = result_it->second;

    userver::formats::json::ValueBuilder response;
    response["request_id"] = result.request_id;
    response["status"] = result.success ? "completed" : "failed";
    response["processing_time_ms"] = result.processing_time_ms;

    if (result.success) {
        response["output"] = result.output_data;
        response["confidence"] = result.confidence;
    } else {
        response["error"] = result.error_message;
    }

    return response.ExtractValue();
}

userver::formats::json::Value AICoreHandler::HandleTrainModel(
    const userver::formats::json::Value& request_json) const {

    const auto model_id = request_json["model_id"].As<std::string>("");
    const auto dataset_path = request_json["dataset_path"].As<std::string>("");

    if (model_id.empty() || dataset_path.empty()) {
        return userver::formats::json::MakeObject("error", "model_id and dataset_path required");
    }

    // Start training process (would be asynchronous in real implementation)
    LOG_INFO() << "Starting training for model: " << model_id;

    userver::formats::json::ValueBuilder response;
    response["status"] = "training_started";
    response["model_id"] = model_id;
    response["training_id"] = "train_" + std::to_string(std::rand());
    response["estimated_duration_minutes"] = 30;

    return response.ExtractValue();
}

userver::formats::json::Value AICoreHandler::HandleGetQuantumStatus(
    const userver::formats::json::Value& request_json) const {

    auto status = quantum_processor_->GetStatus();

    userver::formats::json::ValueBuilder response;
    response["status"] = "active";
    response["quantum_processor"] = status;
    response["available_qubits"] = 32;  // Simulated
    response["coherence_time_us"] = 50.0;
    response["gate_fidelity"] = 0.995;

    return response.ExtractValue();
}

}  // namespace ai_core
