#include "device_discovery.hpp"

#include <userver/logging/log.hpp>
#include <chrono>
#include <random>

namespace mesh_gateway {

DeviceDiscovery::DeviceDiscovery() {
    LOG_INFO() << "Device Discovery initialized";
    StartDiscovery();
}

DeviceDiscovery::~DeviceDiscovery() {
    StopDiscovery();
}

void DeviceDiscovery::StartDiscovery() {
    if (running_) return;

    running_ = true;
    discovery_thread_ = std::thread([this]() {
        DiscoveryLoop();
    });

    LOG_INFO() << "Device discovery started";
}

void DeviceDiscovery::StopDiscovery() {
    if (!running_) return;

    running_ = false;
    if (discovery_thread_.joinable()) {
        discovery_thread_.join();
    }

    LOG_INFO() << "Device discovery stopped";
}

std::vector<DeviceInfo> DeviceDiscovery::GetDiscoveredDevices() const {
    std::lock_guard<std::mutex> lock(devices_mutex_);
    return discovered_devices_;
}

void DeviceDiscovery::DiscoveryLoop() {
    while (running_) {
        SimulateDeviceDiscovery();
        std::this_thread::sleep_for(std::chrono::seconds(5));
    }
}

void DeviceDiscovery::SimulateDeviceDiscovery() {
    std::lock_guard<std::mutex> lock(devices_mutex_);

    // Simulate discovering new devices
    static int device_counter = 0;
    if (device_counter < 10 && (rand() % 100) < 20) {  // 20% chance to discover new device
        DeviceInfo new_device;
        new_device.device_id = "device_" + std::to_string(++device_counter);
        new_device.device_type = "mesh_node";
        new_device.status = "online";
        new_device.latitude = 55.7558 + (rand() % 100 - 50) * 0.001;  // Moscow area
        new_device.longitude = 37.6173 + (rand() % 100 - 50) * 0.001;
        new_device.last_seen = std::chrono::system_clock::now();

        discovered_devices_.push_back(new_device);
        LOG_INFO() << "Discovered new device: " << new_device.device_id;
    }

    // Update last seen times and remove offline devices
    auto now = std::chrono::system_clock::now();
    for (auto it = discovered_devices_.begin(); it != discovered_devices_.end(); ) {
        auto time_diff = std::chrono::duration_cast<std::chrono::seconds>(
            now - it->last_seen).count();

        if (time_diff > 300) {  // 5 minutes timeout
            LOG_INFO() << "Device went offline: " << it->device_id;
            it = discovered_devices_.erase(it);
        } else {
            it->last_seen = now;
            ++it;
        }
    }
}

}  // namespace mesh_gateway
