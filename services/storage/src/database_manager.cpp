#include "database_manager.hpp"

#include <userver/logging/log.hpp>
#include <algorithm>

namespace storage {

DatabaseManager::DatabaseManager() : connection_healthy_(true) {
    InitializeConnection();
    CreateTables();
    LOG_INFO() << "Database Manager initialized";
}

bool DatabaseManager::InsertRecord(const std::string& table, const DatabaseRecord& record) {
    std::lock_guard<std::mutex> lock(db_mutex_);

    try {
        auto& table_records = tables_[table];
        // Check if record with this ID already exists
        auto it = std::find_if(table_records.begin(), table_records.end(),
                              [&record](const DatabaseRecord& r) { return r.id == record.id; });

        if (it != table_records.end()) {
            LOG_WARNING() << "Record with ID " << record.id << " already exists in table " << table;
            return false;
        }

        table_records.push_back(record);
        LOG_INFO() << "Inserted record " << record.id << " into table " << table;
        return true;

    } catch (const std::exception& e) {
        LOG_ERROR() << "Failed to insert record: " << e.what();
        connection_healthy_ = false;
        return false;
    }
}

DatabaseRecord DatabaseManager::GetRecord(const std::string& table, const std::string& id) {
    std::lock_guard<std::mutex> lock(db_mutex_);

    try {
        auto table_it = tables_.find(table);
        if (table_it == tables_.end()) {
            return DatabaseRecord{};
        }

        auto& table_records = table_it->second;
        auto it = std::find_if(table_records.begin(), table_records.end(),
                              [&id](const DatabaseRecord& r) { return r.id == id; });

        if (it != table_records.end()) {
            LOG_DEBUG() << "Retrieved record " << id << " from table " << table;
            return *it;
        }

        LOG_DEBUG() << "Record " << id << " not found in table " << table;
        return DatabaseRecord{};

    } catch (const std::exception& e) {
        LOG_ERROR() << "Failed to get record: " << e.what();
        connection_healthy_ = false;
        return DatabaseRecord{};
    }
}

bool DatabaseManager::UpdateRecord(const std::string& table, const DatabaseRecord& record) {
    std::lock_guard<std::mutex> lock(db_mutex_);

    try {
        auto table_it = tables_.find(table);
        if (table_it == tables_.end()) {
            LOG_WARNING() << "Table " << table << " does not exist";
            return false;
        }

        auto& table_records = table_it->second;
        auto it = std::find_if(table_records.begin(), table_records.end(),
                              [&record](const DatabaseRecord& r) { return r.id == record.id; });

        if (it == table_records.end()) {
            LOG_WARNING() << "Record " << record.id << " not found in table " << table;
            return false;
        }

        // Update the record
        it->data = record.data;
        it->updated_at = record.updated_at;

        LOG_INFO() << "Updated record " << record.id << " in table " << table;
        return true;

    } catch (const std::exception& e) {
        LOG_ERROR() << "Failed to update record: " << e.what();
        connection_healthy_ = false;
        return false;
    }
}

bool DatabaseManager::DeleteRecord(const std::string& table, const std::string& id) {
    std::lock_guard<std::mutex> lock(db_mutex_);

    try {
        auto table_it = tables_.find(table);
        if (table_it == tables_.end()) {
            LOG_WARNING() << "Table " << table << " does not exist";
            return false;
        }

        auto& table_records = table_it->second;
        auto it = std::find_if(table_records.begin(), table_records.end(),
                              [&id](const DatabaseRecord& r) { return r.id == id; });

        if (it == table_records.end()) {
            LOG_WARNING() << "Record " << id << " not found in table " << table;
            return false;
        }

        table_records.erase(it);
        LOG_INFO() << "Deleted record " << id << " from table " << table;
        return true;

    } catch (const std::exception& e) {
        LOG_ERROR() << "Failed to delete record: " << e.what();
        connection_healthy_ = false;
        return false;
    }
}

std::vector<DatabaseRecord> DatabaseManager::QueryRecords(
    const std::string& table, const std::string& query, int limit) {

    std::lock_guard<std::mutex> lock(db_mutex_);

    try {
        auto table_it = tables_.find(table);
        if (table_it == tables_.end()) {
            LOG_WARNING() << "Table " << table << " does not exist";
            return {};
        }

        auto& table_records = table_it->second;

        // Simple query implementation - in real system this would parse SQL
        std::vector<DatabaseRecord> results;

        if (query.empty()) {
            // Return all records
            results = table_records;
        } else {
            // Simple filtering based on query string
            for (const auto& record : table_records) {
                // Very basic query matching - in real implementation would use proper SQL parsing
                if (record.data.As<std::string>("").find(query) != std::string::npos) {
                    results.push_back(record);
                }
            }
        }

        // Apply limit
        if (results.size() > static_cast<size_t>(limit)) {
            results.resize(limit);
        }

        LOG_DEBUG() << "Queried " << results.size() << " records from table " << table;
        return results;

    } catch (const std::exception& e) {
        LOG_ERROR() << "Failed to query records: " << e.what();
        connection_healthy_ = false;
        return {};
    }
}

bool DatabaseManager::IsHealthy() const {
    return connection_healthy_;
}

void DatabaseManager::InitializeConnection() {
    // In a real implementation, this would establish connection to PostgreSQL
    // For simulation, we just set the healthy flag
    connection_healthy_ = true;
    LOG_INFO() << "Database connection initialized (simulated)";
}

void DatabaseManager::CreateTables() {
    // Create default tables
    tables_["mesh_devices"];
    tables_["ai_models"];
    tables_["blockchain_transactions"];
    tables_["user_sessions"];

    LOG_INFO() << "Database tables initialized (simulated)";
}

}  // namespace storage
