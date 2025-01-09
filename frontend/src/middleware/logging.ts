import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/utils/db';

enum LogLevel {
    INFO = 'INFO',
    WARN = 'WARN',
    ERROR = 'ERROR'
}

interface LogEntry {
    level: LogLevel;
    component: string;
    message: string;
    details?: any;
    timestamp?: Date;
}

async function logToDatabase(entry: LogEntry) {
    try {
        await query(
            `INSERT INTO system_logs (level, component, message, details)
             VALUES ($1, $2, $3, $4)`,
            [entry.level, entry.component, entry.message, JSON.stringify(entry.details)]
        );
    } catch (error) {
        console.error('Error writing to log database:', error);
        // Fallback to console logging if database write fails
        console.log(JSON.stringify(entry));
    }
}

function maskSensitiveData(data: any): any {
    if (!data) return data;
    
    const maskedData = { ...data };
    const sensitiveFields = ['password', 'token', 'apiKey', 'secret'];
    
    Object.keys(maskedData).forEach(key => {
        if (sensitiveFields.includes(key.toLowerCase())) {
            maskedData[key] = '********';
        } else if (typeof maskedData[key] === 'object') {
            maskedData[key] = maskSensitiveData(maskedData[key]);
        }
    });
    
    return maskedData;
}

export async function loggingMiddleware(req: NextRequest) {
    const startTime = Date.now();
    const requestId = crypto.randomUUID();

    // Extract basic request information
    const logData = {
        requestId,
        method: req.method,
        url: req.url,
        path: req.nextUrl.pathname,
        userAgent: req.headers.get('user-agent'),
        ip: req.ip || req.headers.get('x-forwarded-for') || 'unknown',
        userId: req.headers.get('x-user-id') || 'anonymous'
    };

    try {
        // Log request
        await logToDatabase({
            level: LogLevel.INFO,
            component: 'API',
            message: `Incoming ${req.method} request to ${req.nextUrl.pathname}`,
            details: {
                ...logData,
                headers: Object.fromEntries(req.headers.entries())
            }
        });

        // Get the response
        const response = await NextResponse.next();
        const duration = Date.now() - startTime;

        // Log response
        await logToDatabase({
            level: LogLevel.INFO,
            component: 'API',
            message: `Completed ${req.method} request to ${req.nextUrl.pathname}`,
            details: {
                ...logData,
                statusCode: response.status,
                duration,
                size: response.headers.get('content-length')
            }
        });

        // Add response headers
        response.headers.set('X-Request-ID', requestId);
        response.headers.set('X-Response-Time', `${duration}ms`);

        return response;
    } catch (error) {
        const duration = Date.now() - startTime;

        // Log error
        await logToDatabase({
            level: LogLevel.ERROR,
            component: 'API',
            message: `Error processing ${req.method} request to ${req.nextUrl.pathname}`,
            details: {
                ...logData,
                error: {
                    message: error.message,
                    stack: error.stack,
                    name: error.name
                },
                duration
            }
        });

        // Return error response
        return new NextResponse(
            JSON.stringify({ 
                error: 'Internal server error',
                requestId 
            }),
            { 
                status: 500,
                headers: {
                    'X-Request-ID': requestId,
                    'X-Response-Time': `${duration}ms`
                }
            }
        );
    }
}

// Helper function to log application events
export async function logEvent(
    level: LogLevel,
    component: string,
    message: string,
    details?: any
) {
    await logToDatabase({
        level,
        component,
        message,
        details: maskSensitiveData(details)
    });
} 