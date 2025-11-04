-- Initialize PostgreSQL database for Decentralized Autonomous Forum
-- This script runs automatically when PostgreSQL container starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search
CREATE EXTENSION IF NOT EXISTS "unaccent"; -- For search normalization

-- Create schema (optional, using public schema by default)
-- CREATE SCHEMA IF NOT EXISTS forum;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE decentralized_forum TO forum_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO forum_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO forum_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO forum_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO forum_user;

-- Output confirmation
SELECT 'Database initialized successfully!' AS status;
SELECT version() AS postgresql_version;
