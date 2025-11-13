#include "cache_manager.hpp"

#include <userver/logging/log.hpp>

namespace storage {

CacheManager::CacheManager() : connection_healthy_(true) {
    InitializeConnection();
    LOG_INFO() << "Cache Manager initialized";
}

bool CacheManager::Set(const std::string& key, const userver::formats::json::Value& value, int ttl_seconds) {
    std::lock_guard<std::mutex> lock(cache_mutex_);

    try {
        CacheEntry entry;
        entry.value = value;
        entry.expires_at = std::chrono::system_clock::now() + std::chrono::seconds(ttl_seconds);

        cache_[key] = entry;

        LOG_DEBUG() << "Set cache key: " << key << " with TTL: " << ttl_seconds << "s";
        return true;

    } catch (const std::exception& e) {
        LOG_ERROR() << "Failed to set cache: " << e.what();
        connection_healthy_ = false;
        return false;
    }
}

userver::formats::json::Value CacheManager::Get(const std::string& key) {
    std::lock_guard<std::mutex> lock(cache_mutex_);

    try {
        auto it = cache_.find(key);
        if (it == cache_.end()) {
            LOG_DEBUG() << "Cache key not found: " << key;
            return userver::formats::json::Value{};
        }

        // Check if expired
        if (std::chrono::system_clock::now() > it->second.expires_at) {
            LOG_DEBUG() << "Cache key expired: " << key;
            cache_.erase(it);
            return userver::formats::json::Value{};
        }

        LOG_DEBUG() << "Retrieved cache key: " << key;
        return it->second.value;

    } catch (const std::exception& e) {
        LOG_ERROR() << "Failed to get cache: " << e.what();
        connection_healthy_ = false;
        return userver::formats::json::Value{};
    }
}

bool CacheManager::Delete(const std::string& key) {
    std::lock_guard<std::mutex> lock(cache_mutex_);

    try {
        auto it = cache_.find(key);
        if (it == cache_.end()) {
            LOG_DEBUG() << "Cache key not found for deletion: " << key;
            return false;
        }

        cache_.erase(it);
        LOG_DEBUG() << "Deleted cache key: " << key;
        return true;

    } catch (const std::exception& e) {
        LOG_ERROR() << "Failed to delete cache: " << e.what();
        connection_healthy_ = false;
        return false;
    }
}

void CacheManager::CleanupExpired() {
    std::lock_guard<std::mutex> lock(cache_mutex_);

    auto now = std::chrono::system_clock::now();
    size_t removed_count = 0;

    for (auto it = cache_.begin(); it != cache_.end(); ) {
        if (now > it->second.expires_at) {
            it = cache_.erase(it);
            ++removed_count;
        } else {
            ++it;
        }
    }

    if (removed_count > 0) {
        LOG_INFO() << "Cleaned up " << removed_count << " expired cache entries";
    }
}

bool CacheManager::IsHealthy() const {
    return connection_healthy_;
}

void CacheManager::InitializeConnection() {
    // In a real implementation, this would establish connection to Redis cluster
    // For simulation, we just set the healthy flag
    connection_healthy_ = true;
    LOG_INFO() << "Cache connection initialized (simulated)";
}

}  // namespace storage
