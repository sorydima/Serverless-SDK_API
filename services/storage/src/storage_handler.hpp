#pragma once

#include <userver/server/handlers/http_handler_json_base.hpp>
#include <userver/formats/json.hpp>
#include <userver/logging/log.hpp>

#include <memory>
#include <string>
#include <unordered_map>

namespace storage {

struct StorageObject {
    std::string key;
    std::string data;
    std::string content_type;
    size_t size_bytes;
    std::chrono::system_clock::time_point created_at;
    std::chrono::system_clock::time_point modified_at;
    std::unordered_map<std::string, std::string> metadata;
};

struct DatabaseRecord {
    std::string id;
    userver::formats::json::Value data;
    std::chrono::system_clock::time_point created_at;
    std::chrono::system_clock::time_point updated_at;
};

class DatabaseManager;
class CacheManager;
class FileStorage;

class StorageHandler : public userver::server::handlers::HttpHandlerJsonBase {
public:
    static constexpr std::string_view kName = "storage-handler";

    StorageHandler(const userver::components::ComponentConfig& config,
                   const userver::components::ComponentContext& context);

    userver::formats::json::Value HandleRequestJson(
        const userver::server::http::HttpRequest& request,
        const userver::formats::json::Value& request_json) const override;

private:
    // Object storage endpoints
    userver::formats::json::Value HandleStoreObject(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleGetObject(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleDeleteObject(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleListObjects(
        const userver::formats::json::Value& request_json) const;

    // Database endpoints
    userver::formats::json::Value HandleInsertRecord(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleGetRecord(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleUpdateRecord(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleDeleteRecord(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleQueryRecords(
        const userver::formats::json::Value& request_json) const;

    // Cache endpoints
    userver::formats::json::Value HandleSetCache(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleGetCache(
        const userver::formats::json::Value& request_json) const;

    userver::formats::json::Value HandleDeleteCache(
        const userver::formats::json::Value& request_json) const;

    // Health check
    userver::formats::json::Value HandleHealthCheck(
        const userver::formats::json::Value& request_json) const;

    std::shared_ptr<DatabaseManager> database_manager_;
    std::shared_ptr<CacheManager> cache_manager_;
    std::shared_ptr<FileStorage> file_storage_;
};

}  // namespace storage
