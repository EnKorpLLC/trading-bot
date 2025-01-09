import { NextRequest } from 'next/server';
import { loggingMiddleware, logEvent } from '@/middleware/logging';
import { query } from '@/utils/db';
import { LogLevel } from '@/types/logging';

// Mock the database query function
jest.mock('@/utils/db', () => ({
    query: jest.fn()
}));

describe('Logging Middleware', () => {
    let mockRequest: Partial<NextRequest>;
    const mockQuery = query as jest.MockedFunction<typeof query>;

    beforeEach(() => {
        mockRequest = {
            ip: '127.0.0.1',
            nextUrl: { pathname: '/api/trading/orders' },
            headers: new Headers({
                'user-agent': 'test-agent',
                'x-user-id': 'test-user'
            }),
            method: 'POST',
            url: 'http://localhost:3000/api/trading/orders'
        };

        // Reset mock
        mockQuery.mockClear();
        mockQuery.mockResolvedValue({ rows: [] });
    });

    test('should log incoming requests', async () => {
        await loggingMiddleware(mockRequest as NextRequest);

        expect(mockQuery).toHaveBeenCalledWith(
            expect.stringContaining('INSERT INTO system_logs'),
            expect.arrayContaining([
                'INFO',
                'API',
                expect.stringContaining('Incoming POST request')
            ])
        );
    });

    test('should log request completion', async () => {
        await loggingMiddleware(mockRequest as NextRequest);

        expect(mockQuery).toHaveBeenCalledWith(
            expect.stringContaining('INSERT INTO system_logs'),
            expect.arrayContaining([
                'INFO',
                'API',
                expect.stringContaining('Completed POST request')
            ])
        );
    });

    test('should add request ID and response time headers', async () => {
        const response = await loggingMiddleware(mockRequest as NextRequest);
        
        expect(response.headers.get('X-Request-ID')).toBeDefined();
        expect(response.headers.get('X-Response-Time')).toMatch(/^\d+ms$/);
    });

    test('should log errors with stack traces', async () => {
        // Mock next() to throw an error
        const error = new Error('Test error');
        mockQuery.mockRejectedValueOnce(error);

        const response = await loggingMiddleware(mockRequest as NextRequest);
        
        expect(mockQuery).toHaveBeenCalledWith(
            expect.stringContaining('INSERT INTO system_logs'),
            expect.arrayContaining([
                'ERROR',
                'API',
                expect.stringContaining('Error processing POST request')
            ])
        );

        expect(response.status).toBe(500);
        const body = await response.json();
        expect(body.error).toBe('Internal server error');
        expect(body.requestId).toBeDefined();
    });

    test('should mask sensitive data in logs', async () => {
        mockRequest.headers.set('authorization', 'Bearer secret-token');
        await loggingMiddleware(mockRequest as NextRequest);

        const logCalls = mockQuery.mock.calls;
        const loggedData = JSON.parse(logCalls[0][1][3]); // Get details parameter

        expect(loggedData.headers.authorization).toBe('********');
    });
});

describe('Event Logging', () => {
    const mockQuery = query as jest.MockedFunction<typeof query>;

    beforeEach(() => {
        mockQuery.mockClear();
        mockQuery.mockResolvedValue({ rows: [] });
    });

    test('should log events with correct level', async () => {
        await logEvent(LogLevel.INFO, 'Test', 'Test message');

        expect(mockQuery).toHaveBeenCalledWith(
            expect.stringContaining('INSERT INTO system_logs'),
            expect.arrayContaining([
                'INFO',
                'Test',
                'Test message'
            ])
        );
    });

    test('should mask sensitive data in event details', async () => {
        const sensitiveData = {
            password: 'secret123',
            apiKey: 'api-key-123',
            normalField: 'visible'
        };

        await logEvent(LogLevel.INFO, 'Test', 'Test message', sensitiveData);

        const logCalls = mockQuery.mock.calls;
        const loggedData = JSON.parse(logCalls[0][1][3]); // Get details parameter

        expect(loggedData.password).toBe('********');
        expect(loggedData.apiKey).toBe('********');
        expect(loggedData.normalField).toBe('visible');
    });

    test('should handle nested sensitive data', async () => {
        const nestedData = {
            user: {
                password: 'secret123',
                email: 'test@example.com'
            },
            credentials: {
                apiKey: 'api-key-123'
            }
        };

        await logEvent(LogLevel.INFO, 'Test', 'Test message', nestedData);

        const logCalls = mockQuery.mock.calls;
        const loggedData = JSON.parse(logCalls[0][1][3]); // Get details parameter

        expect(loggedData.user.password).toBe('********');
        expect(loggedData.user.email).toBe('test@example.com');
        expect(loggedData.credentials.apiKey).toBe('********');
    });

    test('should fallback to console on database error', async () => {
        const consoleSpy = jest.spyOn(console, 'log');
        mockQuery.mockRejectedValueOnce(new Error('Database error'));

        await logEvent(LogLevel.ERROR, 'Test', 'Test message');

        expect(consoleSpy).toHaveBeenCalled();
        consoleSpy.mockRestore();
    });
}); 