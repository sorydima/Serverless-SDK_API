#include "storage_handler.hpp"
#include "database_manager.hpp"
#include "cache_manager.hpp"
#include "file_storage.hpp"

#include <userver/http/common_headers.hpp>
#include <userver/formats/json/serialize.hpp>

namespace storage {

StorageHandler::StorageHandler(
    const userver::components::ComponentConfig& config,
    const userver::components::ComponentContext& context)
    : HttpHandlerJsonBase(config, context) {

    database_manager_ = std::make_shared<DatabaseManager>();
    cache_manager_ = std::make_shared<CacheManager>();
    file_storage_ = std::make_shared<FileStorage>();

    LOG_INFO() << "Storage Handler initialized";
}

userver::formats::json::Value StorageHandler::HandleRequestJson(
    const userver::server::http::HttpRequest& request,
    const userver::formats::json::Value& request_json) const {

    const auto& method = request.GetMethod();
    const auto& path = request.GetPath();

    LOG_DEBUG() << "Received storage request: " << method << " " << path;

    // Route to appropriate handler based on path
    if (path == "/objects" && method == userver::http::HttpMethod::kPost) {
        return HandleStoreObject(request_json);
    } else if (path.find("/objects/") == 0) {
        std::string object_key = path.substr(9);  // Remove "/objects/" prefix
        if (method == userver::http::HttpMethod::kGet) {
            return HandleGetObject(request_json);
        } else if (method == userver::http::HttpMethod::kDelete) {
            return HandleDeleteObject(request_json);
        }
    } else if (path == "/objects" && method == userver::http::HttpMethod::kGet) {
        return HandleListObjects(request_json);
    } else if (path == "/records" && method == userver::http::HttpMethod::kPost) {
        return HandleInsertRecord(request_json);
    } else if (path.find("/records/") == 0) {
        if (method == userver::http::HttpMethod::kGet) {
            return HandleGetRecord(request_json);
        } else if (method == userver::http::HttpMethod::kPut) {
            return HandleUpdateRecord(request_json);
        } else if (method == userver::http::HttpMethod::kDelete) {
            return HandleDeleteRecord(request_json);
        }
    } else if (path == "/records/query" && method == userver::http::HttpMethod::kPost) {
        return HandleQueryRecords(request_json);
    } else if (path == "/cache" && method == userver::http::HttpMethod::kPost) {
        return HandleSetCache(request_json);
    } else if (path.find("/cache/") == 0) {
        if (method == userver::http::HttpMethod::kGet) {
            return HandleGetCache(request_json);
        } else if (method == userver::http::HttpMethod::kDelete) {
            return HandleDeleteCache(request_json);
        }
    } else if (path == "/health") {
        return HandleHealthCheck(request_json);
    }

    return userver::formats::json::MakeObject("error", "Unknown storage endpoint");
}

userver::formats::json::Value StorageHandler::HandleStoreObject(
    const userver::formats::json::Value& request_json) const {

    const auto key = request_json["key"].As<std::string>("");
    const auto data = request_json["data"].As<std::string>("");
    const auto content_type = request_json["content_type"].As<std::string>("application/octet-stream");

    if (key.empty() || data.empty()) {
        return userver::formats::json::MakeObject("error", "key and data required");
    }

    StorageObject object;
    object.key = key;
    object.data = data;
    object.content_type = content_type;
    object.size_bytes = data.size();
    object.created_at = std::chrono::system_clock::now();
    object.modified_at = object.created_at;

    bool success = file_storage_->StoreObject(object);

    userver::formats::json::ValueBuilder response;
    response["success"] = success;
    if (success) {
        response["status"] = "object_stored";
        response["key"] = key;
        response["size_bytes"] = static_cast<int>(object.size_bytes);
    } else {
        response["status"] = "store_failed";
        response["error"] = "Unable to store object";
    }

    return response.ExtractValue();
}

userver::formats::json::Value StorageHandler::HandleGetObject(
    const userver::formats::json::Value& request_json) const {

    const auto key = request_json["key"].As<std::string>("");

    if (key.empty()) {
        return userver::formats::json::MakeObject("error", "key required");
    }

    auto object = file_storage_->GetObject(key);

    userver::formats::json::ValueBuilder response;
    if (!object.key.empty()) {
        response["success"] = true;
        response["key"] = object.key;
        response["data"] = object.data;
        response["content_type"] = object.content_type;
        response["size_bytes"] = static_cast<int>(object.size_bytes);
        response["created_at"] = std::chrono::duration_cast<std::chrono::seconds>(
            object.created_at.time_since_epoch()).count();
        response["modified_at"] = std::chrono::duration_cast<std::chrono::seconds>(
            object.modified_at.time_since_epoch()).count();
    } else {
        response["success"] = false;
        response["error"] = "Object not found";
    }

    return response.ExtractValue();
}

userver::formats::json::Value StorageHandler::HandleDeleteObject(
    const userver::formats::json::Value& request_json) const {

    const auto key = request_json["key"].As<std::string>("");

    if (key.empty()) {
        return userver::formats::json::MakeObject("error", "key required");
    }

    bool success = file_storage_->DeleteObject(key);

    userver::formats::json::ValueBuilder response;
    response["success"] = success;
    if (success) {
        response["status"] = "object_deleted";
        response["key"] = key;
    } else {
        response["status"] = "delete_failed";
        response["error"] = "Unable to delete object";
    }

    return response.ExtractValue();
}

userver::formats::json::Value StorageHandler::HandleListObjects(
    const userver::formats::json::Value& request_json) const {

    const auto prefix = request_json["prefix"].As<std::string>("");
    const auto max_keys = request_json["max_keys"].As<int>(1000);

    auto objects = file_storage_->ListObjects(prefix, max_keys);

    userver::formats::json::ValueBuilder response;
    response["success"] = true;
    response["object_count"] = objects.size();

    userver::formats::json::ValueBuilder object_list;
    for (const auto& object : objects) {
        userver::formats::json::ValueBuilder obj_json;
        obj_json["key"] = object.key;
        obj_json["size_bytes"] = static_cast<int>(object.size_bytes);
        obj_json["content_type"] = object.content_type;
        obj_json["modified_at"] = std::chrono::duration_cast<std::chrono::seconds>(
            object.modified_at.time_since_epoch()).count();
        object_list.PushBack(obj_json.ExtractValue());
    }

    response["objects"] = object_list.ExtractValue();
    return response.ExtractValue();
}

userver::formats::json::Value StorageHandler::HandleInsertRecord(
    const userver::formats::json::Value& request_json) const {

    const auto table = request_json["table"].As<std::string>("");
    const auto data = request_json["data"];

    if (table.empty() || data.IsEmpty()) {
        return userver::formats::json::MakeObject("error", "table and data required");
    }

    DatabaseRecord record;
    record.id = request_json["id"].As<std::string>("");
    if (record.id.empty()) {
        record.id = "rec_" + std::to_string(std::rand());
    }
    record.data = data;
    record.created_at = std::chrono::system_clock::now();
    record.updated_at = record.created_at;

    bool success = database_manager_->InsertRecord(table, record);

    userver::formats::json::ValueBuilder response;
    response["success"] = success;
    if (success) {
        response["status"] = "record_inserted";
        response["id"] = record.id;
        response["table"] = table;
    } else {
        response["status"] = "insert_failed";
        response["error"] = "Unable to insert record";
    }

    return response.ExtractValue();
}

userver::formats::json::Value StorageHandler::HandleGetRecord(
    const userver::formats::json::Value& request_json) const {

    const auto table = request_json["table"].As<std::string>("");
    const auto id = request_json["id"].As<std::string>("");

    if (table.empty() || id.empty()) {
        return userver::formats::json::MakeObject("error", "table and id required");
    }

    auto record = database_manager_->GetRecord(table, id);

    userver::formats::json::ValueBuilder response;
    if (!record.id.empty()) {
        response["success"] = true;
        response["id"] = record.id;
        response["data"] = record.data;
        response["created_at"] = std::chrono::duration_cast<std::chrono::seconds>(
            record.created_at.time_since_epoch()).count();
        response["updated_at"] = std::chrono::duration_cast<std::chrono::seconds>(
            record.updated_at.time_since_epoch()).count();
    } else {
        response["success"] = false;
        response["error"] = "Record not found";
    }

    return response.ExtractValue();
}

userver::formats::json::Value StorageHandler::HandleUpdateRecord(
    const userver::formats::json::Value& request_json) const {

    const auto table = request_json["table"].As<std::string>("");
    const auto id = request_json["id"].As<std::string>("");
    const auto data = request_json["data"];

    if (table.empty() || id.empty() || data.IsEmpty()) {
        return userver::formats::json::MakeObject("error", "table, id, and data required");
    }

    DatabaseRecord record;
    record.id = id;
    record.data = data;
    record.updated_at = std::chrono::system_clock::now();

    bool success = database_manager_->UpdateRecord(table, record);

    userver::formats::json::ValueBuilder response;
    response["success"] = success;
    if (success) {
        response["status"] = "record_updated";
        response["id"] = id;
        response["table"] = table;
    } else {
        response["status"] = "update_failed";
        response["error"] = "Unable to update record";
    }

    return response.ExtractValue();
}

userver::formats::json::Value StorageHandler::HandleDeleteRecord(
    const userver::formats::json::Value& request_json) const {

    const auto table = request_json["table"].As<std::string>("");
    const auto id = request_json["id"].As<std::string>("");

    if (table.empty() || id.empty()) {
        return userver::formats::json::MakeObject("error", "table and id required");
    }

    bool success = database_manager_->DeleteRecord(table, id);

    userver::formats::json::ValueBuilder response;
    response["success"] = success;
    if (success) {
        response["status"] = "record_deleted";
        response["id"] = id;
        response["table"] = table;
    } else {
        response["status"] = "delete_failed";
        response["error"] = "Unable to delete record";
    }

    return response.ExtractValue();
}

userver::formats::json::Value StorageHandler::HandleQueryRecords(
    const userver::formats::json::Value& request_json) const {

    const auto table = request_json["table"].As<std::string>("");
    const auto query = request_json["query"].As<std::string>("");
    const auto limit = request_json["limit"].As<int>(100);

    if (table.empty()) {
        return userver::formats::json::MakeObject("error", "table required");
    }

    auto records = database_manager_->QueryRecords(table, query, limit);

    userver::formats::json::ValueBuilder response;
    response["success"] = true;
    response["record_count"] = records.size();

    userver::formats::json::ValueBuilder record_list;
    for (const auto& record : records) {
        userver::formats::json::ValueBuilder rec_json;
        rec_json["id"] = record.id;
        rec_json["data"] = record.data;
        rec_json["created_at"] = std::chrono::duration_cast<std::chrono::seconds>(
            record.created_at.time_since_epoch()).count();
        rec_json["updated_at"] = std::chrono::duration_cast<std::chrono::seconds>(
            record.updated_at.time_since_epoch()).count();
        record_list.PushBack(rec_json.ExtractValue());
    }

    response["records"] = record_list.ExtractValue();
    return response.ExtractValue();
}

userver::formats::json::Value StorageHandler::HandleSetCache(
    const userver::formats::json::Value& request_json) const {

    const auto key = request_json["key"].As<std::string>("");
    const auto value = request_json["value"];
    const auto ttl_seconds = request_json["ttl_seconds"].As<int>(3600);

    if (key.empty() || value.IsEmpty()) {
        return userver::formats::json::MakeObject("error", "key and value required");
    }

    bool success = cache_manager_->Set(key, value, ttl_seconds);

    userver::formats::json::ValueBuilder response;
    response["success"] = success;
    if (success) {
        response["status"] = "cache_set";
        response["key"] = key;
        response["ttl_seconds"] = ttl_seconds;
    } else {
        response["status"] = "cache_set_failed";
        response["error"] = "Unable to set cache";
    }

    return response.ExtractValue();
}

userver::formats::json::Value StorageHandler::HandleGetCache(
    const userver::formats::json::Value& request_json) const {

    const auto key = request_json["key"].As<std::string>("");

    if (key.empty()) {
        return userver::formats::json::MakeObject("error", "key required");
    }

    auto value = cache_manager_->Get(key);

    userver::formats::json::ValueBuilder response;
    if (!value.IsEmpty()) {
        response["success"] = true;
        response["key"] = key;
        response["value"] = value;
    } else {
        response["success"] = false;
        response["error"] = "Cache key not found";
    }

    return response.ExtractValue();
}

userver::formats::json::Value StorageHandler::HandleDeleteCache(
    const userver::formats::json::Value& request_json) const {

    const auto key = request_json["key"].As<std::string>("");

    if (key.empty()) {
        return userver::formats::json::MakeObject("error", "key required");
    }

    bool success = cache_manager_->Delete(key);

    userver::formats::json::ValueBuilder response;
    response["success"] = success;
    if (success) {
        response["status"] = "cache_deleted";
        response["key"] = key;
    } else {
        response["status"] = "cache_delete_failed";
        response["error"] = "Unable to delete cache";
    }

    return response.ExtractValue();
}

userver::formats::json::Value StorageHandler::HandleHealthCheck(
    const userver::formats::json::Value& request_json) const {

    userver::formats::json::ValueBuilder response;
    response["status"] = "healthy";
    response["service"] = "storage";
    response["timestamp"] = std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();

    // Check component health
    userver::formats::json::ValueBuilder components;
    components["database"] = database_manager_->IsHealthy();
    components["cache"] = cache_manager_->IsHealthy();
    components["file_storage"] = file_storage_->IsHealthy();
    response["components"] = components.ExtractValue();

    return response.ExtractValue();
}

}  // namespace storage
