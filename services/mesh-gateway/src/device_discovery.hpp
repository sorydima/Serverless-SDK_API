#pragma once

#include "mesh_gateway_handler.hpp"

#include <vector>
#include <thread>
#include <atomic>
#include <mutex>

namespace mesh_gateway {

class DeviceDiscovery {
public:
    DeviceDiscovery();
    ~DeviceDiscovery();

    std::vector<DeviceInfo> GetDiscoveredDevices() const;

    void StartDiscovery();
    void StopDiscovery();

private:
    void DiscoveryLoop();
    void SimulateDeviceDiscovery();

    mutable std::mutex devices_mutex_;
    std::vector<DeviceInfo> discovered_devices_;

    std::thread discovery_thread_;
    std::atomic<bool> running_{false};
};

}  // namespace mesh_gateway
