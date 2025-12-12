-- PostgreSQL initialization script
-- This file is automatically executed when the database container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE torqcare_db TO torqcare_user;

-- Database is created by docker-compose, tables are created by SQLAlchemy