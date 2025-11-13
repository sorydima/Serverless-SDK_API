-- PostgreSQL Slave Initialization Script

-- Configure slave settings
ALTER SYSTEM SET hot_standby = on;
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET wal_keep_size = '1GB';
