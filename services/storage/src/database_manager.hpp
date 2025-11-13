#pragma once

#include "storage_handler.hpp"

#include <vector>
#include <memory>
#include <mutex>

namespace storage {

class DatabaseManager {
public:
    DatabaseManager();
    ~DatabaseManager() = default;

    bool InsertRecord(const std::string& table, const DatabaseRecord& record);
    DatabaseRecord GetRecord(const std::string& table, const std::string& id);
    bool UpdateRecord(const std::string& table, const DatabaseRecord& record);
    bool DeleteRecord(const std::string& table, const std::string& id);
    std::vector<DatabaseRecord> QueryRecords(const std::string& table,
                                           const std::string& query,
                                           int limit);

    bool IsHealthy() const;

private:
    void InitializeConnection();
    void CreateTables();

    mutable std::mutex db_mutex_;
    std::unordered_map<std::string, std::vector<DatabaseRecord>> tables_;
    bool connection_healthy_;
};

}  // namespace storage
