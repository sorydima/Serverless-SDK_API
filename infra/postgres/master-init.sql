-- PostgreSQL Master Initialization Script

-- Create replication user
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator_password';

-- Create synapse database and user
CREATE DATABASE synapse;
CREATE USER synapse WITH ENCRYPTED PASSWORD 'synapse_password';
GRANT ALL PRIVILEGES ON DATABASE synapse TO synapse;

-- Create storage database and user
CREATE DATABASE storage_db;
CREATE USER storage_user WITH ENCRYPTED PASSWORD 'storage_password';
GRANT ALL PRIVILEGES ON DATABASE storage_db TO storage_user;

-- Create ai_core database and user
CREATE DATABASE ai_core_db;
CREATE USER ai_core_user WITH ENCRYPTED PASSWORD 'ai_core_password';
GRANT ALL PRIVILEGES ON DATABASE ai_core_db TO ai_core_user;

-- Configure replication settings
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET wal_keep_size = '1GB';
ALTER SYSTEM SET listen_addresses = '*';

-- Create tables for synapse
\c synapse;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables for storage service
\c storage_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS mesh_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id VARCHAR(255) UNIQUE NOT NULL,
    device_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'offline',
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    location JSONB,
    capabilities JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(255) UNIQUE NOT NULL,
    model_type VARCHAR(100),
    version VARCHAR(50),
    status VARCHAR(50) DEFAULT 'unloaded',
    accuracy DECIMAL(5,4),
    parameters_count BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS blockchain_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_hash VARCHAR(255) UNIQUE NOT NULL,
    block_height BIGINT,
    sender_address VARCHAR(255),
    receiver_address VARCHAR(255),
    amount DECIMAL(36,18),
    gas_used BIGINT,
    status VARCHAR(50) DEFAULT 'pending',
    transaction_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    session_token VARCHAR(500) UNIQUE NOT NULL,
    device_info JSONB,
    ip_address INET,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_mesh_devices_status ON mesh_devices(status);
CREATE INDEX idx_mesh_devices_last_seen ON mesh_devices(last_seen);
CREATE INDEX idx_ai_models_status ON ai_models(status);
CREATE INDEX idx_blockchain_transactions_hash ON blockchain_transactions(transaction_hash);
CREATE INDEX idx_blockchain_transactions_status ON blockchain_transactions(status);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);

-- Create ai_core database tables
\c ai_core_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS model_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(255) UNIQUE NOT NULL,
    model_type VARCHAR(100),
    framework VARCHAR(100),
    version VARCHAR(50),
    accuracy DECIMAL(5,4),
    parameters JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inference_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES model_registry(id),
    input_data JSONB,
    output_data JSONB,
    processing_time_ms INTEGER,
    status VARCHAR(50) DEFAULT 'processing',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS quantum_circuits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    circuit_name VARCHAR(255) UNIQUE NOT NULL,
    qubits_count INTEGER,
    gates_count INTEGER,
    circuit_data JSONB,
    execution_count INTEGER DEFAULT 0,
    last_executed TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for ai_core
CREATE INDEX idx_model_registry_type ON model_registry(model_type);
CREATE INDEX idx_inference_requests_model ON inference_requests(model_id);
CREATE INDEX idx_inference_requests_status ON inference_requests(status);
CREATE INDEX idx_quantum_circuits_name ON quantum_circuits(circuit_name);
