-- Create backups table
CREATE TABLE IF NOT EXISTS backups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    type VARCHAR(20) NOT NULL, -- 'full' or 'incremental'
    status VARCHAR(20) NOT NULL, -- 'pending', 'in_progress', 'completed', 'failed'
    size_bytes BIGINT,
    checksum VARCHAR(64),
    storage_path TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create backup_schedules table
CREATE TABLE IF NOT EXISTS backup_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    frequency VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly'
    time_of_day TIME NOT NULL,
    retention_days INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_run TIMESTAMP WITH TIME ZONE,
    next_run TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create backup_contents table
CREATE TABLE IF NOT EXISTS backup_contents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backup_id UUID NOT NULL REFERENCES backups(id),
    content_type VARCHAR(50) NOT NULL, -- 'positions', 'orders', 'trades', etc.
    record_count INTEGER NOT NULL,
    content_checksum VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create backup_logs table
CREATE TABLE IF NOT EXISTS backup_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backup_id UUID REFERENCES backups(id),
    schedule_id UUID REFERENCES backup_schedules(id),
    level VARCHAR(20) NOT NULL, -- 'info', 'warning', 'error'
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_backups_user_id ON backups(user_id);
CREATE INDEX IF NOT EXISTS idx_backups_timestamp ON backups(timestamp);
CREATE INDEX IF NOT EXISTS idx_backup_schedules_user ON backup_schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_backup_schedules_next_run ON backup_schedules(next_run);
CREATE INDEX IF NOT EXISTS idx_backup_contents_backup ON backup_contents(backup_id);
CREATE INDEX IF NOT EXISTS idx_backup_logs_backup ON backup_logs(backup_id);
CREATE INDEX IF NOT EXISTS idx_backup_logs_schedule ON backup_logs(schedule_id);

-- Create trigger for updating backup_schedules.updated_at
CREATE TRIGGER update_backup_schedules_updated_at
    BEFORE UPDATE ON backup_schedules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to update next_run timestamp
CREATE OR REPLACE FUNCTION update_next_run()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.frequency = 'daily' THEN
        NEW.next_run := (CURRENT_DATE + NEW.time_of_day + INTERVAL '1 day')::TIMESTAMP;
    ELSIF NEW.frequency = 'weekly' THEN
        NEW.next_run := (CURRENT_DATE + NEW.time_of_day + INTERVAL '1 week')::TIMESTAMP;
    ELSIF NEW.frequency = 'monthly' THEN
        NEW.next_run := (CURRENT_DATE + NEW.time_of_day + INTERVAL '1 month')::TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updating next_run
CREATE TRIGGER update_backup_schedule_next_run
    BEFORE INSERT OR UPDATE ON backup_schedules
    FOR EACH ROW
    EXECUTE FUNCTION update_next_run(); 