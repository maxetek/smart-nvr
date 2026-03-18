-- Create database if it doesn't exist
-- Note: This runs inside the postgres container on first init
SELECT 'CREATE DATABASE smartnvr'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'smartnvr')\gexec
