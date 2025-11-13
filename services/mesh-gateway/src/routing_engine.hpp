#pragma once

#include "mesh_gateway_handler.hpp"

#include <unordered_map>
#include <vector>
#include <string>
#include <memory>

namespace mesh_gateway {

class RoutingEngine {
public:
    RoutingEngine();
    ~RoutingEngine() = default;

    RouteInfo CalculateRoute(const std::string& source, const std::string& destination) const;
    bool SendMessage(const std::string& destination, const std::string& message) const;

    void UpdateTopology(const std::vector<DeviceInfo>& devices);

private:
    std::vector<std::string> FindShortestPath(
        const std::string& start, const std::string& end) const;

    double CalculateLatency(const std::vector<std::string>& path) const;

    mutable std::unordered_map<std::string, std::vector<std::string>> topology_;
    mutable std::unordered_map<std::string, double> link_latencies_;
};

}  // namespace mesh_gateway
