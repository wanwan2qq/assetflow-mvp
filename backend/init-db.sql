-- Initialize AssetFlow database
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database user if not exists (already created by POSTGRES_USER env var)
-- The database and user are automatically created by the postgres image

-- Set timezone
SET timezone = 'UTC';