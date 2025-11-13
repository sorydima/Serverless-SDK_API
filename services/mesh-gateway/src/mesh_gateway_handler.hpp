#pragma once

#include <userver/server/handlers/http_handler_json_base.hpp>
#include <userver/formats/json.hpp>
#include <userver/logging/log.hpp>

#include <memory>
#include <unordered_map>
#include <string>
#include <vector>

namespace mesh_gateway {

struct DeviceInfo {
    std::string device_id;
    std::string device_type;
    std::string status;
    double latitude;
    double longitude;
    std::chrono::system_clock::time_point last_seen;
};

struct RouteInfo {
    std::string source_id;
    std::string destination_id;
    std::vector<std::string> path;
    int hop_count;
    double latency_ms;
};

class DeviceDiscovery;
class RoutingEngine;

class MeshGatewayHandler : public userver::server::handlers::HttpHandlerJsonBase {
public:
    static constexpr std::string_view kName = "mesh-gateway-handler";

    MeshGatewayHandler(const userver::components::ComponentConfig& config,
                      const userver::components::ComponentContext& context);

    userver::formats::json::Value HandleRequestJson(
        const userver::server::http::HttpRequest& request,
        const userver::formats::json::Value& request_json) const override;

private:
    userver::formats::json::Value HandleGetDevices(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleGetRoutes(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleSendMessage(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleGetMeshStatus(
        const userver::formats::json::Value& request_json) const;

    std::shared_ptr<DeviceDiscovery> device_discovery_;
    std::shared_ptr<RoutingEngine> routing_engine_;

    mutable std::unordered_map<std::string, DeviceInfo> device_registry_;
    mutable std::unordered_map<std::string, RouteInfo> active_routes_;
};

}  // namespace mesh_gateway
