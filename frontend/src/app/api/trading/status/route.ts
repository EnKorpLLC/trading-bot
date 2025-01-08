import { NextResponse } from 'next/server';
import { query } from '@/utils/db';

export async function GET() {
  try {
    // Test database connection with a simple query
    const result = await query('SELECT NOW()');
    
    return NextResponse.json({
      status: 'online',
      timestamp: result.rows[0].now,
      database: 'connected'
    });
  } catch (error) {
    console.error('Database connection error:', error);
    return NextResponse.json(
      {
        status: 'error',
        message: 'Database connection failed',
        error: process.env.NODE_ENV === 'development' ? error.message : undefined
      },
      { status: 500 }
    );
  }
} 