-- TorqCare Database Schema for PostgreSQL
-- Multi-Agent Vehicle Care System

-- Create Database
CREATE DATABASE torqcare_db;

\c torqcare_db;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================
-- 1. SENSOR DATA TABLE
-- ================================================
CREATE TABLE sensor_data (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Engine metrics
    engine_temp DECIMAL(5,2),  -- Celsius
    rpm DECIMAL(6,2),
    oil_pressure DECIMAL(5,2), -- PSI
    coolant_level DECIMAL(5,2), -- Percentage
    
    -- Electrical system
    battery_voltage DECIMAL(4,2), -- Volts
    alternator_voltage DECIMAL(4,2),
    
    -- Fuel system
    fuel_level DECIMAL(5,2), -- Percentage
    fuel_pressure DECIMAL(5,2), -- PSI
    
    -- Tire monitoring
    tire_pressure_fl DECIMAL(4,2), -- Front Left PSI
    tire_pressure_fr DECIMAL(4,2), -- Front Right PSI
    tire_pressure_rl DECIMAL(4,2), -- Rear Left PSI
    tire_pressure_rr DECIMAL(4,2), -- Rear Right PSI
    tire_temp_fl DECIMAL(5,2),
    tire_temp_fr DECIMAL(5,2),
    tire_temp_rl DECIMAL(5,2),
    tire_temp_rr DECIMAL(5,2),
    
    -- Brake system
    brake_fluid_level DECIMAL(5,2), -- Percentage
    brake_pad_thickness_fl DECIMAL(4,2), -- mm
    brake_pad_thickness_fr DECIMAL(4,2),
    brake_pad_thickness_rl DECIMAL(4,2),
    brake_pad_thickness_rr DECIMAL(4,2),
    
    -- Transmission
    transmission_temp DECIMAL(5,2),
    transmission_fluid_level DECIMAL(5,2),
    
    -- Performance
    speed DECIMAL(5,2), -- km/h
    acceleration DECIMAL(5,2), -- m/s²
    odometer DECIMAL(10,2), -- km
    
    -- Environmental
    ambient_temp DECIMAL(5,2),
    cabin_temp DECIMAL(5,2),
    
    -- GPS
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    
    -- Anomaly flags
    anomaly_detected BOOLEAN DEFAULT FALSE,
    anomaly_type VARCHAR(100),
    
    -- Indexes for performance
    CONSTRAINT fk_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE
);

CREATE INDEX idx_sensor_vehicle_timestamp ON sensor_data(vehicle_id, timestamp DESC);
CREATE INDEX idx_sensor_anomaly ON sensor_data(anomaly_detected, timestamp DESC);
CREATE INDEX idx_sensor_timestamp ON sensor_data(timestamp DESC);

-- ================================================
-- 2. VEHICLES TABLE
-- ================================================
CREATE TABLE vehicles (
    vehicle_id VARCHAR(50) PRIMARY KEY,
    vin VARCHAR(17) UNIQUE NOT NULL,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    color VARCHAR(30),
    
    -- Owner information
    owner_id INTEGER NOT NULL,
    registration_date DATE,
    
    -- Vehicle specifications
    engine_type VARCHAR(50), -- Electric, Gasoline, Diesel, Hybrid
    engine_capacity DECIMAL(4,2), -- Liters
    transmission_type VARCHAR(30), -- Manual, Automatic, CVT
    
    -- Current status
    current_mileage DECIMAL(10,2),
    last_service_date DATE,
    next_service_due DATE,
    health_score DECIMAL(3,2), -- 0-100
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_owner FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_vehicle_owner ON vehicles(owner_id);
CREATE INDEX idx_vehicle_health ON vehicles(health_score);

-- ================================================
-- 3. USERS TABLE
-- ================================================
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    
    -- Account info
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Preferences
    notification_preferences JSONB,
    preferred_workshop_id INTEGER
);

CREATE INDEX idx_user_email ON users(email);

-- ================================================
-- 4. MAINTENANCE HISTORY TABLE
-- ================================================
CREATE TABLE maintenance_history (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) NOT NULL,
    
    -- Service details
    service_date TIMESTAMP NOT NULL,
    service_type VARCHAR(50) NOT NULL, -- Oil Change, Brake Service, Tire Rotation, etc.
    description TEXT,
    mileage_at_service DECIMAL(10,2),
    
    -- Workshop info
    workshop_id INTEGER,
    mechanic_name VARCHAR(100),
    
    -- Parts and costs
    parts_replaced JSONB, -- Array of parts
    labor_hours DECIMAL(5,2),
    parts_cost DECIMAL(10,2),
    labor_cost DECIMAL(10,2),
    total_cost DECIMAL(10,2),
    
    -- Issue resolution
    issue_reported TEXT,
    issue_resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    
    -- Quality tracking
    customer_rating INTEGER CHECK (customer_rating BETWEEN 1 AND 5),
    manufacturer_notified BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_maint_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    CONSTRAINT fk_maint_workshop FOREIGN KEY (workshop_id) REFERENCES workshops(workshop_id) ON DELETE SET NULL
);

CREATE INDEX idx_maint_vehicle ON maintenance_history(vehicle_id, service_date DESC);
CREATE INDEX idx_maint_service_type ON maintenance_history(service_type);
CREATE INDEX idx_maint_workshop ON maintenance_history(workshop_id);

-- ================================================
-- 5. APPOINTMENTS TABLE
-- ================================================
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) NOT NULL,
    
    -- Appointment details
    issue_type VARCHAR(100) NOT NULL,
    urgency VARCHAR(20) NOT NULL CHECK (urgency IN ('routine', 'urgent', 'critical')),
    description TEXT,
    
    -- Scheduling
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    requested_date DATE,
    scheduled_time TIMESTAMP,
    completed_time TIMESTAMP,
    
    -- Workshop assignment
    workshop_id INTEGER,
    assigned_mechanic VARCHAR(100),
    estimated_duration INTERVAL,
    estimated_cost DECIMAL(10,2),
    
    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled')),
    
    -- Automated scheduling
    suggested_slots JSONB, -- AI-suggested time slots
    auto_scheduled BOOLEAN DEFAULT FALSE,
    
    -- Customer interaction
    customer_accepted BOOLEAN,
    cancellation_reason TEXT,
    
    -- Predictions
    predicted_issue VARCHAR(100),
    prediction_confidence DECIMAL(3,2),
    
    CONSTRAINT fk_appt_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    CONSTRAINT fk_appt_workshop FOREIGN KEY (workshop_id) REFERENCES workshops(workshop_id) ON DELETE SET NULL
);

CREATE INDEX idx_appt_vehicle ON appointments(vehicle_id, created_at DESC);
CREATE INDEX idx_appt_status ON appointments(status, scheduled_time);
CREATE INDEX idx_appt_workshop ON appointments(workshop_id, scheduled_time);
CREATE INDEX idx_appt_urgency ON appointments(urgency, status);

-- ================================================
-- 6. WORKSHOPS TABLE
-- ================================================
CREATE TABLE workshops (
    workshop_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    city VARCHAR(50),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    
    -- Contact
    phone VARCHAR(20),
    email VARCHAR(100),
    website VARCHAR(200),
    
    -- Location
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    
    -- Capabilities
    specializations TEXT[], -- Array of specializations
    certified_brands TEXT[],
    equipment_available JSONB,
    
    -- Availability
    operating_hours JSONB, -- Schedule by day
    appointment_slots_per_hour INTEGER DEFAULT 2,
    
    -- Performance metrics
    average_rating DECIMAL(3,2),
    total_services_completed INTEGER DEFAULT 0,
    average_completion_time INTERVAL,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workshop_city ON workshops(city, is_active);
CREATE INDEX idx_workshop_rating ON workshops(average_rating DESC);

-- ================================================
-- 7. FEEDBACK TABLE
-- ================================================
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) NOT NULL,
    appointment_id INTEGER,
    
    -- Feedback details
    feedback_type VARCHAR(20) NOT NULL CHECK (feedback_type IN ('repair', 'vehicle', 'service')),
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    
    -- Categories
    repair_quality_rating INTEGER CHECK (repair_quality_rating BETWEEN 1 AND 5),
    service_speed_rating INTEGER CHECK (service_speed_rating BETWEEN 1 AND 5),
    cost_satisfaction_rating INTEGER CHECK (cost_satisfaction_rating BETWEEN 1 AND 5),
    
    -- Issue tracking
    issue_recurring BOOLEAN DEFAULT FALSE,
    issue_fully_resolved BOOLEAN,
    additional_issues_found TEXT,
    
    -- Sharing status
    shared_with_manufacturer BOOLEAN DEFAULT FALSE,
    shared_with_workshop BOOLEAN DEFAULT FALSE,
    manufacturer_response TEXT,
    workshop_response TEXT,
    
    -- Media
    photos JSONB, -- Array of photo URLs
    
    -- Timestamps
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    
    CONSTRAINT fk_feedback_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    CONSTRAINT fk_feedback_appt FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE SET NULL
);

CREATE INDEX idx_feedback_vehicle ON feedback(vehicle_id, submitted_at DESC);
CREATE INDEX idx_feedback_appointment ON feedback(appointment_id);
CREATE INDEX idx_feedback_type_rating ON feedback(feedback_type, rating);

-- ================================================
-- 8. PREDICTIONS TABLE
-- ================================================
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) NOT NULL,
    
    -- Prediction details
    predicted_failure VARCHAR(100) NOT NULL, -- Engine, Transmission, Brakes, Battery, etc.
    prediction_model VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL, -- 0-100
    
    -- Timeline
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estimated_failure_date DATE,
    time_to_failure_days INTEGER,
    
    -- Contributing factors
    contributing_metrics JSONB, -- Key sensor readings
    historical_patterns JSONB,
    
    -- Risk assessment
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    recommended_action TEXT,
    estimated_repair_cost DECIMAL(10,2),
    
    -- Outcome tracking
    actual_failure_occurred BOOLEAN,
    actual_failure_date DATE,
    prediction_accuracy DECIMAL(3,2), -- Post-analysis
    
    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'false_positive', 'monitoring')),
    resolution_notes TEXT,
    
    CONSTRAINT fk_pred_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE
);

CREATE INDEX idx_pred_vehicle ON predictions(vehicle_id, predicted_at DESC);
CREATE INDEX idx_pred_severity ON predictions(severity, status);
CREATE INDEX idx_pred_failure_type ON predictions(predicted_failure, confidence_score DESC);

-- ================================================
-- 9. ALERTS TABLE
-- ================================================
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) NOT NULL,
    
    -- Alert details
    alert_type VARCHAR(50) NOT NULL, -- critical, warning, info
    alert_category VARCHAR(50), -- engine, transmission, brakes, tires, etc.
    message TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    
    -- Source
    triggered_by VARCHAR(50), -- sensor, prediction, manual
    sensor_reading_id INTEGER,
    prediction_id INTEGER,
    
    -- Status
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    
    -- Actions taken
    action_required BOOLEAN DEFAULT FALSE,
    action_taken VARCHAR(100),
    appointment_created INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_alert_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    CONSTRAINT fk_alert_sensor FOREIGN KEY (sensor_reading_id) REFERENCES sensor_data(id) ON DELETE SET NULL,
    CONSTRAINT fk_alert_prediction FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE SET NULL,
    CONSTRAINT fk_alert_appointment FOREIGN KEY (appointment_created) REFERENCES appointments(id) ON DELETE SET NULL
);

CREATE INDEX idx_alert_vehicle ON alerts(vehicle_id, created_at DESC);
CREATE INDEX idx_alert_severity ON alerts(severity, resolved);
CREATE INDEX idx_alert_type ON alerts(alert_type, acknowledged);

-- ================================================
-- 10. AGENT LOGS TABLE
-- ================================================
CREATE TABLE agent_logs (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(50) NOT NULL,
    vehicle_id VARCHAR(50),
    
    -- Log details
    action_type VARCHAR(50) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    
    -- Performance
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Context
    triggered_by VARCHAR(50),
    related_entities JSONB, -- appointment_id, prediction_id, etc.
    
    -- Timestamp
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_logs_name ON agent_logs(agent_name, logged_at DESC);
CREATE INDEX idx_agent_logs_vehicle ON agent_logs(vehicle_id, logged_at DESC);
CREATE INDEX idx_agent_logs_success ON agent_logs(success);

-- ================================================
-- 11. QUALITY_INSIGHTS TABLE
-- ================================================
CREATE TABLE quality_insights (
    id SERIAL PRIMARY KEY,
    
    -- Vehicle model aggregation
    make VARCHAR(50),
    model VARCHAR(50),
    year INTEGER,
    
    -- Failure patterns
    failure_type VARCHAR(100) NOT NULL,
    occurrence_count INTEGER DEFAULT 1,
    first_occurrence DATE,
    last_occurrence DATE,
    
    -- Metrics
    average_mileage_at_failure DECIMAL(10,2),
    average_age_at_failure DECIMAL(5,2), -- Years
    failure_rate DECIMAL(5,4), -- Per 1000 vehicles
    
    -- Cost analysis
    average_repair_cost DECIMAL(10,2),
    total_repair_cost DECIMAL(12,2),
    warranty_coverage_rate DECIMAL(3,2), -- Percentage
    
    -- Feedback aggregation
    average_customer_satisfaction DECIMAL(3,2),
    recurring_issue_rate DECIMAL(3,2),
    
    -- Root cause analysis
    suspected_root_cause TEXT,
    manufacturing_defect_likely BOOLEAN DEFAULT FALSE,
    design_flaw_likely BOOLEAN DEFAULT FALSE,
    maintenance_related BOOLEAN DEFAULT FALSE,
    
    -- Manufacturer notifications
    manufacturer_notified BOOLEAN DEFAULT FALSE,
    notification_date TIMESTAMP,
    manufacturer_response TEXT,
    recall_issued BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analyzed_vehicle_count INTEGER
);

CREATE INDEX idx_quality_make_model ON quality_insights(make, model, year);
CREATE INDEX idx_quality_failure_type ON quality_insights(failure_type, failure_rate DESC);
CREATE INDEX idx_quality_manufacturer_notified ON quality_insights(manufacturer_notified, manufacturing_defect_likely);

-- ================================================
-- VIEWS FOR ANALYTICS
-- ================================================

-- Vehicle Health Dashboard View
CREATE VIEW v_vehicle_health_summary AS
SELECT 
    v.vehicle_id,
    v.vin,
    v.make,
    v.model,
    v.year,
    v.health_score,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status IN ('pending', 'confirmed')) as pending_appointments,
    COUNT(DISTINCT p.id) FILTER (WHERE p.status = 'active' AND p.severity IN ('high', 'critical')) as critical_predictions,
    COUNT(DISTINCT al.id) FILTER (WHERE al.resolved = FALSE AND al.severity = 'critical') as unresolved_critical_alerts,
    MAX(sd.timestamp) as last_telemetry_update,
    AVG(f.rating) as average_feedback_rating
FROM vehicles v
LEFT JOIN appointments a ON v.vehicle_id = a.vehicle_id
LEFT JOIN predictions p ON v.vehicle_id = p.vehicle_id
LEFT JOIN alerts al ON v.vehicle_id = al.vehicle_id
LEFT JOIN sensor_data sd ON v.vehicle_id = sd.vehicle_id
LEFT JOIN feedback f ON v.vehicle_id = f.vehicle_id
GROUP BY v.vehicle_id;

-- Workshop Performance View
CREATE VIEW v_workshop_performance AS
SELECT 
    w.workshop_id,
    w.name,
    w.city,
    w.average_rating,
    COUNT(DISTINCT a.id) as total_appointments,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'completed') as completed_appointments,
    AVG(f.rating) as recent_feedback_rating,
    AVG(EXTRACT(EPOCH FROM (a.completed_time - a.scheduled_time))/3600) as avg_service_hours
FROM workshops w
LEFT JOIN appointments a ON w.workshop_id = a.workshop_id
LEFT JOIN feedback f ON a.id = f.appointment_id
WHERE a.created_at > CURRENT_DATE - INTERVAL '90 days'
GROUP BY w.workshop_id;

-- ================================================
-- FUNCTIONS AND TRIGGERS
-- ================================================

-- Function to update vehicle health score
CREATE OR REPLACE FUNCTION update_vehicle_health_score()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE vehicles
    SET health_score = (
        SELECT 100 - (
            COUNT(*) FILTER (WHERE severity = 'critical') * 20 +
            COUNT(*) FILTER (WHERE severity = 'high') * 10 +
            COUNT(*) FILTER (WHERE severity = 'medium') * 5
        )
        FROM predictions
        WHERE vehicle_id = NEW.vehicle_id
        AND status = 'active'
    )
    WHERE vehicle_id = NEW.vehicle_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_health_score
AFTER INSERT OR UPDATE ON predictions
FOR EACH ROW
EXECUTE FUNCTION update_vehicle_health_score();

-- Function to auto-update timestamps
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_vehicles_timestamp
BEFORE UPDATE ON vehicles
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_workshops_timestamp
BEFORE UPDATE ON workshops
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- ================================================
-- SAMPLE DATA FOR TESTING
-- ================================================

-- Insert sample user
INSERT INTO users (email, full_name, phone, password_hash) VALUES
('john.doe@example.com', 'John Doe', '+1234567890', 'hashed_password_here');

-- Insert sample vehicle
INSERT INTO vehicles (vehicle_id, vin, make, model, year, owner_id, engine_type, current_mileage, health_score) VALUES
('VEH001', '5YJ3E1EA7KF123456', 'Tesla', 'Model 3', 2023, 1, 'Electric', 15234.50, 95.0);

-- Insert sample workshops
INSERT INTO workshops (name, address, city, state, phone, average_rating, is_active) VALUES
('AutoCare Center', '123 Main St', 'San Francisco', 'CA', '+1-415-555-0100', 4.8, TRUE),
('Premium Motors', '456 Oak Ave', 'San Francisco', 'CA', '+1-415-555-0200', 4.6, TRUE),
('QuickFix Garage', '789 Pine Rd', 'San Francisco', 'CA', '+1-415-555-0300', 4.9, TRUE);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO torqcare_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO torqcare_user;