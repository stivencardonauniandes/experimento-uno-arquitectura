-- Create databases for each service
CREATE DATABASE inventory_db;
CREATE DATABASE orders_db;

-- Create users with appropriate permissions (optional)
-- CREATE USER inventory_user WITH PASSWORD 'inventory_pass';
-- CREATE USER orders_user WITH PASSWORD 'orders_pass';

-- Grant permissions
-- GRANT ALL PRIVILEGES ON DATABASE inventory_db TO inventory_user;
-- GRANT ALL PRIVILEGES ON DATABASE orders_db TO orders_user;

-- Connect to inventory_db and create extensions if needed
\c inventory_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Connect to orders_db and create extensions if needed
\c orders_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
