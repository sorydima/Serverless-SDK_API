-- PostgreSQL Security Hardening

-- Enable row-level security
ALTER DATABASE synapse SET row_security = on;
ALTER DATABASE storage_db SET row_security = on;
ALTER DATABASE ai_core_db SET row_security = on;

-- Create security roles
CREATE ROLE readonly;
CREATE ROLE readwrite;
CREATE ROLE admin;

-- Grant appropriate permissions
GRANT CONNECT ON DATABASE synapse TO readonly, readwrite, admin;
GRANT CONNECT ON DATABASE storage_db TO readonly, readwrite, admin;
GRANT CONNECT ON DATABASE ai_core_db TO readonly, readwrite, admin;

-- Set up schema permissions
\c synapse;
GRANT USAGE ON SCHEMA public TO readonly, readwrite, admin;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO readwrite;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;

\c storage_db;
GRANT USAGE ON SCHEMA public TO readonly, readwrite, admin;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO readwrite;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;

\c ai_core_db;
GRANT USAGE ON SCHEMA public TO readonly, readwrite, admin;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO readwrite;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;

-- Enable audit logging
ALTER SYSTEM SET log_statement = 'ddl';
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;

-- Set password policy
ALTER SYSTEM SET password_encryption = 'scram-sha-256';

-- Configure connection limits
ALTER SYSTEM SET max_connections = 200;

-- Enable SSL/TLS
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/etc/ssl/certs/postgresql.crt';
ALTER SYSTEM SET ssl_key_file = '/etc/ssl/private/postgresql.key';
ALTER SYSTEM SET ssl_ca_file = '/etc/ssl/certs/ca.crt';

-- Set up pg_hba.conf for secure connections
-- This would be configured in the Docker volume or host system

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, operation, old_values, user_name, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), current_user, now());
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, operation, old_values, new_values, user_name, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), row_to_json(NEW), current_user, now());
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, operation, new_values, user_name, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(NEW), current_user, now());
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create audit log table
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_name TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for audit log
CREATE INDEX idx_audit_log_table ON audit_log(table_name);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_log_user ON audit_log(user_name);

-- Grant permissions on audit log
GRANT SELECT ON audit_log TO readonly;
GRANT SELECT, INSERT ON audit_log TO readwrite;
GRANT ALL ON audit_log TO admin;
