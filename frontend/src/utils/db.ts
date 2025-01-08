import { Pool, PoolConfig } from 'pg';

let pool: Pool | null = null;

export function getPool(): Pool {
  if (!pool) {
    const config: PoolConfig = {
      connectionString: process.env.DATABASE_URL,
      ssl: { rejectUnauthorized: false },
      max: 20, // Maximum number of clients in the pool
      idleTimeoutMillis: 30000, // How long a client is allowed to remain idle before being closed
      connectionTimeoutMillis: 2000, // How long to wait when connecting a new client
    };

    pool = new Pool(config);

    // Error handling
    pool.on('error', (err) => {
      console.error('Unexpected error on idle client', err);
      process.exit(-1);
    });
  }

  return pool;
}

// Helper function to run queries
export async function query(text: string, params?: any[]) {
  const client = await getPool().connect();
  try {
    return await client.query(text, params);
  } finally {
    client.release();
  }
}

// Cleanup function for graceful shutdown
export async function closePool() {
  if (pool) {
    await pool.end();
    pool = null;
  }
} 