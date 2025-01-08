const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(process.cwd(), '.env.local') });

console.log('Starting migration script...');
console.log('DATABASE_URL:', process.env.DATABASE_URL ? 'Found' : 'Not found');

async function checkTablesExist(pool) {
  const result = await pool.query(`
    SELECT EXISTS (
      SELECT FROM information_schema.tables 
      WHERE table_schema = 'public' 
      AND table_name = 'users'
    );
  `);
  return result.rows[0].exists;
}

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
    const tablesExist = await checkTablesExist(pool);
    if (tablesExist) {
      console.log('Tables already exist, skipping initial schema migration');
      return;
    }

    const migrationPath = path.join(process.cwd(), 'src', 'db', 'migrations', '001_initial_schema.sql');
    console.log('Reading migration file from:', migrationPath);
    const migrationSQL = fs.readFileSync(migrationPath, 'utf8');
    console.log('Migration file loaded, size:', migrationSQL.length);

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