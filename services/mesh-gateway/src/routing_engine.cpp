#include "routing_engine.hpp"

#include <userver/logging/log.hpp>
#include <queue>
#include <unordered_set>
#include <algorithm>

namespace mesh_gateway {

RoutingEngine::RoutingEngine() {
    LOG_INFO() << "Routing Engine initialized";

    // Initialize with some default topology
    topology_["device_1"] = {"device_2", "device_3"};
    topology_["device_2"] = {"device_1", "device_4", "device_5"};
    topology_["device_3"] = {"device_1", "device_6"};
    topology_["device_4"] = {"device_2", "device_7"};
    topology_["device_5"] = {"device_2", "device_8"};
    topology_["device_6"] = {"device_3", "device_9"};
    topology_["device_7"] = {"device_4", "device_10"};
    topology_["device_8"] = {"device_5"};
    topology_["device_9"] = {"device_6"};
    topology_["device_10"] = {"device_7"};

    // Initialize link latencies (in milliseconds)
    link_latencies_["device_1-device_2"] = 10.0;
    link_latencies_["device_1-device_3"] = 15.0;
    link_latencies_["device_2-device_4"] = 12.0;
    link_latencies_["device_2-device_5"] = 8.0;
    link_latencies_["device_3-device_6"] = 20.0;
    link_latencies_["device_4-device_7"] = 18.0;
    link_latencies_["device_5-device_8"] = 14.0;
    link_latencies_["device_6-device_9"] = 16.0;
    link_latencies_["device_7-device_10"] = 22.0;
}

RouteInfo RoutingEngine::CalculateRoute(
    const std::string& source, const std::string& destination) const {

    RouteInfo route;
    route.source_id = source;
    route.destination_id = destination;

    if (source == destination) {
        route.path = {source};
        route.hop_count = 0;
        route.latency_ms = 0.0;
        return route;
    }

    route.path = FindShortestPath(source, destination);
    route.hop_count = route.path.size() - 1;
    route.latency_ms = CalculateLatency(route.path);

    LOG_DEBUG() << "Calculated route from " << source << " to " << destination
                << " with " << route.hop_count << " hops";

    return route;
}

bool RoutingEngine::SendMessage(
    const std::string& destination, const std::string& message) const {

    // Simulate message sending through the mesh
    LOG_INFO() << "Sending message to " << destination << ": " << message.substr(0, 50) << "...";

    // In a real implementation, this would:
    // 1. Calculate the route to destination
    // 2. Establish connections along the path
    // 3. Send the message hop by hop
    // 4. Handle acknowledgments and retransmissions

    // For simulation, assume 95% success rate
    bool success = (rand() % 100) < 95;

    if (success) {
        LOG_INFO() << "Message sent successfully to " << destination;
    } else {
        LOG_WARNING() << "Failed to send message to " << destination;
    }

    return success;
}

void RoutingEngine::UpdateTopology(const std::vector<DeviceInfo>& devices) {
    // Update topology based on discovered devices
    // This would rebuild the routing table based on current network state

    LOG_DEBUG() << "Updating topology with " << devices.size() << " devices";

    // Clear existing topology
    topology_.clear();

    // Rebuild topology based on device locations and capabilities
    for (const auto& device : devices) {
        std::vector<std::string> neighbors;

        // Find nearby devices (simplified proximity calculation)
        for (const auto& other : devices) {
            if (other.device_id != device.device_id) {
                double distance = std::sqrt(
                    std::pow(other.latitude - device.latitude, 2) +
                    std::pow(other.longitude - device.longitude, 2)
                );

                // Consider devices within 1km as neighbors
                if (distance < 0.01) {  // Rough approximation
                    neighbors.push_back(other.device_id);

                    // Set link latency based on distance
                    std::string link_key = device.device_id + "-" + other.device_id;
                    link_latencies_[link_key] = distance * 1000;  // 1ms per km
                }
            }
        }

        topology_[device.device_id] = neighbors;
    }

    LOG_INFO() << "Topology updated with " << topology_.size() << " nodes";
}

std::vector<std::string> RoutingEngine::FindShortestPath(
    const std::string& start, const std::string& end) const {

    if (topology_.find(start) == topology_.end() ||
        topology_.find(end) == topology_.end()) {
        return {};  // No path if nodes don't exist
    }

    // BFS for shortest path in unweighted graph
    std::unordered_map<std::string, std::string> came_from;
    std::queue<std::string> frontier;
    std::unordered_set<std::string> visited;

    frontier.push(start);
    visited.insert(start);
    came_from[start] = "";

    bool found = false;
    while (!frontier.empty() && !found) {
        std::string current = frontier.front();
        frontier.pop();

        if (current == end) {
            found = true;
            break;
        }

        auto neighbors_it = topology_.find(current);
        if (neighbors_it != topology_.end()) {
            for (const auto& neighbor : neighbors_it->second) {
                if (visited.find(neighbor) == visited.end()) {
                    visited.insert(neighbor);
                    frontier.push(neighbor);
                    came_from[neighbor] = current;
                }
            }
        }
    }

    if (!found) {
        return {};  // No path found
    }

    // Reconstruct path
    std::vector<std::string> path;
    std::string current = end;
    while (!current.empty()) {
        path.push_back(current);
        current = came_from[current];
    }
    std::reverse(path.begin(), path.end());

    return path;
}

double RoutingEngine::CalculateLatency(const std::vector<std::string>& path) const {
    if (path.size() < 2) return 0.0;

    double total_latency = 0.0;
    for (size_t i = 0; i < path.size() - 1; ++i) {
        std::string link_key = path[i] + "-" + path[i + 1];
        auto latency_it = link_latencies_.find(link_key);
        if (latency_it != link_latencies_.end()) {
            total_latency += latency_it->second;
        } else {
            total_latency += 10.0;  // Default latency
        }
    }

    return total_latency;
}

}  // namespace mesh_gateway
