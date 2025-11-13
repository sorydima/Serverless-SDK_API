#pragma once

#include "storage_handler.hpp"

#include <vector>
#include <unordered_map>
#include <memory>
#include <mutex>
#include <filesystem>

namespace storage {

class FileStorage {
public:
    FileStorage();
    ~FileStorage() = default;

    bool StoreObject(const StorageObject& object);
    StorageObject GetObject(const std::string& key);
    bool DeleteObject(const std::string& key);
    std::vector<StorageObject> ListObjects(const std::string& prefix, int max_keys);

    bool IsHealthy() const;

private:
    std::string GetObjectPath(const std::string& key) const;
    void EnsureDirectoryExists(const std::string& path) const;

    mutable std::mutex storage_mutex_;
    std::filesystem::path storage_root_;
    std::unordered_map<std::string, StorageObject> object_metadata_;
    bool storage_healthy_;
};

}  // namespace storage
