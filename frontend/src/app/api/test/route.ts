import { NextResponse } from 'next/server';
import { query } from '@/utils/db';

export async function GET() {
  try {
    // Simple test query
    const result = await query('SELECT NOW() as time, current_database() as db_name');
    
    return NextResponse.json({
      status: 'success',
      message: 'API is working',
      database: {
        connected: true,
        time: result.rows[0].time,
        name: result.rows[0].db_name
      }
    });
  } catch (error) {
    console.error('API test error:', error);
    return NextResponse.json({
      status: 'error',
      message: 'API test failed',
      error: process.env.NODE_ENV === 'development' ? error.message : 'Internal server error'
    }, { status: 500 });
  }
} 