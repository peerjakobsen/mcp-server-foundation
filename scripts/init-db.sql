-- Database initialization script for MCP Server Foundation
-- This script runs when the PostgreSQL container is first created

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create basic schema structure if needed
-- Note: The application will handle table creation via migrations/ORM
-- This file is mainly for extensions and initial setup

-- Set default timezone
SET timezone = 'UTC';

-- Create application user permissions (already created by environment variables)
-- GRANT ALL PRIVILEGES ON DATABASE mcp_dev TO mcp;

-- Log successful initialization
SELECT 'MCP Server Foundation database initialized successfully' AS message;
