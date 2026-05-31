-- PostGIS-Enabled Spatial Database Schema for Geotagged Outbreak Analytics

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS crops (
    id SERIAL PRIMARY KEY,
    crop_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS diseases (
    id SERIAL PRIMARY KEY,
    disease_name VARCHAR(200) UNIQUE NOT NULL,
    pesticide_registry_vetted BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS farmer_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id INT NOT NULL,
    crop_id INT REFERENCES crops(id),
    disease_id INT REFERENCES diseases(id),
    confidence_score DOUBLE PRECISION NOT NULL,
    gps_coordinates GEOMETRY(Point, 4326), -- PostGIS point mapping
    district VARCHAR(100),
    state VARCHAR(100),
    altitude DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE TABLE IF NOT EXISTS outbreak_alerts (
    id SERIAL PRIMARY KEY,
    district VARCHAR(100) NOT NULL,
    disease_id INT REFERENCES diseases(id),
    severity_level VARCHAR(20) NOT NULL, -- LOW, MEDIUM, CRITICAL
    registered_at TIMESTAMP DEFAULT timezone('utc'::text, now())
);

-- Indexing point coordinates for efficient distance queries
CREATE INDEX IF NOT EXISTS idx_farmer_scans_gps ON farmer_scans USING GIST (gps_coordinates);
