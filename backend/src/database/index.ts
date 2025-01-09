import { Pool } from 'pg';
import { logger } from '../utils/logger';

const pool = new Pool({
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
    password: process.env.DB_PASSWORD,
    port: parseInt(process.env.DB_PORT || '5432'),
    ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

export async function initializeDatabase(): Promise<void> {
    try {
        // Test database connection
        const client = await pool.connect();
        logger.info('Successfully connected to the database');
        client.release();

        // Initialize tables if they don't exist
        await initializeTables();
    } catch (error) {
        logger.error('Failed to initialize database:', error);
        throw error;
    }
}

async function initializeTables(): Promise<void> {
    try {
        // Read and execute migration files
        const migrations = [
            // Add migration file paths here
            '../db/migrations/003_backup_schema.sql',
            // Add more migrations as needed
        ];

        for (const migration of migrations) {
            try {
                const sql = require(migration);
                await pool.query(sql);
                logger.info(`Successfully executed migration: ${migration}`);
            } catch (error) {
                logger.error(`Failed to execute migration ${migration}:`, error);
                throw error;
            }
        }
    } catch (error) {
        logger.error('Failed to initialize tables:', error);
        throw error;
    }
}

export { pool }; 