#pragma once

#include <userver/formats/json.hpp>

#include <unordered_map>
#include <memory>
#include <mutex>
#include <chrono>

namespace storage {

struct CacheEntry {
    userver::formats::json::Value value;
    std::chrono::system_clock::time_point expires_at;
};

class CacheManager {
public:
    CacheManager();
    ~CacheManager() = default;

    bool Set(const std::string& key, const userver::formats::json::Value& value, int ttl_seconds);
    userver::formats::json::Value Get(const std::string& key);
    bool Delete(const std::string& key);
    void CleanupExpired();

    bool IsHealthy() const;

private:
    void InitializeConnection();

    mutable std::mutex cache_mutex_;
    std::unordered_map<std::string, CacheEntry> cache_;
    bool connection_healthy_;
};

}  // namespace storage
