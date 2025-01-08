import { Pool } from 'pg';
import * as fs from 'fs';
import * as path from 'path';
import * as dotenv from 'dotenv';

console.log('Starting migration script...');

// Load environment variables from .env.local
const envPath = path.resolve(process.cwd(), '.env.local');
console.log('Loading environment from:', envPath);
dotenv.config({ path: envPath });

console.log('DATABASE_URL:', process.env.DATABASE_URL ? 'Found' : 'Not found');

async function runMigrations() {
  if (!process.env.DATABASE_URL) {
    throw new Error('DATABASE_URL environment variable is not set');
  }

  console.log('Creating database pool...');
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }
  });

  try {
    // Read migration file
    const migrationPath = path.join(process.cwd(), 'src', 'db', 'migrations', '001_initial_schema.sql');
    console.log('Reading migration file from:', migrationPath);
    const migrationSQL = fs.readFileSync(migrationPath, 'utf8');
    console.log('Migration file loaded, size:', migrationSQL.length);

    // Execute migration
    console.log('Running initial schema migration...');
    await pool.query(migrationSQL);
    console.log('Migration completed successfully');

  } catch (error) {
    console.error('Migration failed:', error);
    throw error;
  } finally {
    console.log('Closing database pool...');
    await pool.end();
  }
}

// Run migrations if this file is executed directly
if (require.main === module) {
  console.log('Running migrations...');
  runMigrations()
    .then(() => {
      console.log('Migration script completed successfully');
      process.exit(0);
    })
    .catch((error) => {
      console.error('Migration script failed:', error);
      process.exit(1);
    });
} 