#include "file_storage.hpp"

#include <userver/logging/log.hpp>
#include <fstream>
#include <algorithm>

namespace storage {

FileStorage::FileStorage() : storage_root_("./storage"), storage_healthy_(true) {
    try {
        // Create storage directory if it doesn't exist
        std::filesystem::create_directories(storage_root_);
        LOG_INFO() << "File Storage initialized at: " << storage_root_.string();
    } catch (const std::exception& e) {
        LOG_ERROR() << "Failed to initialize file storage: " << e.what();
        storage_healthy_ = false;
    }
}

bool FileStorage::StoreObject(const StorageObject& object) {
    std::lock_guard<std::mutex> lock(storage_mutex_);

    try {
        std::string object_path = GetObjectPath(object.key);
        EnsureDirectoryExists(object_path);

        // Write object data to file
        std::ofstream file(object_path, std::ios::binary);
        if (!file) {
            LOG_ERROR() << "Failed to open file for writing: " << object_path;
            return false;
        }

        file.write(object.data.c_str(), object.data.size());
        file.close();

        // Store metadata
        object_metadata_[object.key] = object;

        LOG_INFO() << "Stored object: " << object.key << " (" << object.size_bytes << " bytes)";
        return true;

    } catch (const std::exception& e) {
        LOG_ERROR() << "Failed to store object: " << e.what();
        storage_healthy_ = false;
        return false;
    }
}

StorageObject FileStorage::GetObject(const std::string& key) {
    std::lock_guard<std::mutex> lock(storage_mutex_);

    try {
        auto metadata_it = object_metadata_.find(key);
        if (metadata_it == object_metadata_.end()) {
            LOG_DEBUG() << "Object not found in metadata: " << key;
            return StorageObject{};
        }

        std::string object_path = GetObjectPath(key);
        std::ifstream file(object_path, std::ios::binary | std::ios::ate);

        if (!file) {
            LOG_ERROR() << "Failed to open file for reading: " << object_path;
            return StorageObject{};
        }

        std::streamsize size = file.tellg();
        file.seekg(0, std::ios::beg);

        StorageObject object = metadata_it->second;
        object.data.resize(size);
        file.read(&object.data[0], size);
        file.close();

        LOG_DEBUG() << "Retrieved object: " << key << " (" << size << " bytes)";
        return object;

    } catch (const std::exception& e) {
        LOG_ERROR() << "Failed to get object: " << e.what();
        storage_healthy_ = false;
        return StorageObject{};
    }
}

bool FileStorage::DeleteObject(const std::string& key) {
    std::lock_guard<std::mutex> lock(storage_mutex_);

    try {
        std::string object_path = GetObjectPath(key);

        // Remove file
        if (std::filesystem::exists(object_path)) {
            std::filesystem::remove(object_path);
        }

        // Remove metadata
        auto metadata_it = object_metadata_.find(key);
        if (metadata_it != object_metadata_.end()) {
            object_metadata_.erase(metadata_it);
        }

        LOG_INFO() << "Deleted object: " << key;
        return true;

    } catch (const std::exception& e) {
        LOG_ERROR() << "Failed to delete object: " << e.what();
        storage_healthy_ = false;
        return false;
    }
}

std::vector<StorageObject> FileStorage::ListObjects(const std::string& prefix, int max_keys) {
    std::lock_guard<std::mutex> lock(storage_mutex_);

    try {
        std::vector<StorageObject> objects;

        for (const auto& pair : object_metadata_) {
            const auto& key = pair.first;
            const auto& object = pair.second;

            // Check prefix match
            if (!prefix.empty() && key.find(prefix) != 0) {
                continue;
            }

            objects.push_back(object);

            // Check max keys limit
            if (objects.size() >= static_cast<size_t>(max_keys)) {
                break;
            }
        }

        // Sort by key for consistent ordering
        std::sort(objects.begin(), objects.end(),
                 [](const StorageObject& a, const StorageObject& b) {
                     return a.key < b.key;
                 });

        LOG_DEBUG() << "Listed " << objects.size() << " objects with prefix: " << prefix;
        return objects;

    } catch (const std::exception& e) {
        LOG_ERROR() << "Failed to list objects: " << e.what();
        storage_healthy_ = false;
        return {};
    }
}

bool FileStorage::IsHealthy() const {
    return storage_healthy_;
}

std::string FileStorage::GetObjectPath(const std::string& key) const {
    // Create a simple hash-based directory structure to avoid too many files in one directory
    size_t hash = std::hash<std::string>{}(key);
    int dir1 = hash % 256;
    int dir2 = (hash >> 8) % 256;

    return (storage_root_ / std::to_string(dir1) / std::to_string(dir2) / key).string();
}

void FileStorage::EnsureDirectoryExists(const std::string& path) const {
    std::filesystem::path file_path(path);
    std::filesystem::path dir_path = file_path.parent_path();

    if (!dir_path.empty()) {
        std::filesystem::create_directories(dir_path);
    }
}

}  // namespace storage
