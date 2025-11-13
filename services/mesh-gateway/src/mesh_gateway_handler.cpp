#include "mesh_gateway_handler.hpp"
#include "device_discovery.hpp"
#include "routing_engine.hpp"

#include <userver/http/common_headers.hpp>
#include <userver/formats/json/serialize.hpp>

namespace mesh_gateway {

MeshGatewayHandler::MeshGatewayHandler(
    const userver::components::ComponentConfig& config,
    const userver::components::ComponentContext& context)
    : HttpHandlerJsonBase(config, context) {

    device_discovery_ = std::make_shared<DeviceDiscovery>();
    routing_engine_ = std::make_shared<RoutingEngine>();

    LOG_INFO() << "Mesh Gateway Handler initialized";
}

userver::formats::json::Value MeshGatewayHandler::HandleRequestJson(
    const userver::server::http::HttpRequest& request,
    const userver::formats::json::Value& request_json) const {

    const auto& method = request.GetMethod();
    const auto& path = request.GetPath();

    LOG_DEBUG() << "Received request: " << method << " " << path;

    // Route to appropriate handler based on path
    if (path == "/devices") {
        return HandleGetDevices(request_json);
    } else if (path == "/routes") {
        return HandleGetRoutes(request_json);
    } else if (path == "/send" && method == userver::http::HttpMethod::kPost) {
        return HandleSendMessage(request_json);
    } else if (path == "/status") {
        return HandleGetMeshStatus(request_json);
    }

    return userver::formats::json::MakeObject("error", "Unknown endpoint");
}

userver::formats::json::Value MeshGatewayHandler::HandleGetDevices(
    const userver::formats::json::Value& request_json) const {

    // Get device list from discovery service
    auto devices = device_discovery_->GetDiscoveredDevices();

    userver::formats::json::ValueBuilder response;
    response["status"] = "success";
    response["device_count"] = devices.size();

    userver::formats::json::ValueBuilder device_list;
    for (const auto& device : devices) {
        userver::formats::json::ValueBuilder device_json;
        device_json["device_id"] = device.device_id;
        device_json["device_type"] = device.device_type;
        device_json["status"] = device.status;
        device_json["latitude"] = device.latitude;
        device_json["longitude"] = device.longitude;
        device_json["last_seen"] = std::chrono::duration_cast<std::chrono::seconds>(
            device.last_seen.time_since_epoch()).count();

        device_list.PushBack(device_json.ExtractValue());
    }

    response["devices"] = device_list.ExtractValue();
    return response.ExtractValue();
}

userver::formats::json::Value MeshGatewayHandler::HandleGetRoutes(
    const userver::formats::json::Value& request_json) const {

    const auto source = request_json["source"].As<std::string>("");
    const auto destination = request_json["destination"].As<std::string>("");

    if (source.empty() || destination.empty()) {
        return userver::formats::json::MakeObject("error", "Source and destination required");
    }

    // Calculate route using routing engine
    auto route = routing_engine_->CalculateRoute(source, destination);

    userver::formats::json::ValueBuilder response;
    response["status"] = "success";
    response["source"] = route.source_id;
    response["destination"] = route.destination_id;
    response["hop_count"] = route.hop_count;
    response["latency_ms"] = route.latency_ms;

    userver::formats::json::ValueBuilder path_json;
    for (const auto& hop : route.path) {
        path_json.PushBack(hop);
    }
    response["path"] = path_json.ExtractValue();

    return response.ExtractValue();
}

userver::formats::json::Value MeshGatewayHandler::HandleSendMessage(
    const userver::formats::json::Value& request_json) const {

    const auto destination = request_json["destination"].As<std::string>("");
    const auto message = request_json["message"].As<std::string>("");

    if (destination.empty() || message.empty()) {
        return userver::formats::json::MakeObject("error", "Destination and message required");
    }

    // Send message through mesh network
    bool success = routing_engine_->SendMessage(destination, message);

    userver::formats::json::ValueBuilder response;
    response["success"] = success;
    if (success) {
        response["status"] = "message_sent";
        response["destination"] = destination;
    } else {
        response["status"] = "send_failed";
        response["error"] = "Unable to reach destination";
    }

    return response.ExtractValue();
}

userver::formats::json::Value MeshGatewayHandler::HandleGetMeshStatus(
    const userver::formats::json::Value& request_json) const {

    userver::formats::json::ValueBuilder response;
    response["status"] = "active";
    response["gateway_id"] = "mesh-gateway-001";
    response["uptime_seconds"] = 3600;  // Placeholder
    response["active_devices"] = device_registry_.size();
    response["active_routes"] = active_routes_.size();

    // Network health metrics
    userver::formats::json::ValueBuilder health;
    health["connectivity"] = 0.95;
    health["latency_avg_ms"] = 45.0;
    health["packet_loss"] = 0.02;
    response["network_health"] = health.ExtractValue();

    return response.ExtractValue();
}

}  // namespace mesh_gateway
