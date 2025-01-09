import { NextRequest } from 'next/server';
import { rateLimitMiddleware } from '@/middleware/rateLimit';
import { SECURITY_CONFIG } from '@/config/security';

describe('Rate Limiting Middleware', () => {
    let mockRequest: Partial<NextRequest>;
    const testIp = '127.0.0.1';

    beforeEach(() => {
        mockRequest = {
            ip: testIp,
            nextUrl: { pathname: '/api/trading/orders' },
            headers: new Headers(),
            method: 'GET'
        };
    });

    test('should allow requests within API rate limit', async () => {
        const response = await rateLimitMiddleware(mockRequest as NextRequest);
        expect(response.status).not.toBe(429);

        const headers = response.headers;
        expect(headers.get('X-RateLimit-Limit')).toBe(String(SECURITY_CONFIG.rateLimits.api.points));
        expect(parseInt(headers.get('X-RateLimit-Remaining') || '0')).toBeGreaterThan(0);
    });

    test('should block requests exceeding API rate limit', async () => {
        // Make requests up to the limit
        for (let i = 0; i < SECURITY_CONFIG.rateLimits.api.points; i++) {
            await rateLimitMiddleware(mockRequest as NextRequest);
        }

        // Next request should be blocked
        const response = await rateLimitMiddleware(mockRequest as NextRequest);
        expect(response.status).toBe(429);
        const body = await response.json();
        expect(body.error).toContain('Too many requests');
    });

    test('should apply stricter limits to login endpoints', async () => {
        mockRequest.nextUrl = { pathname: '/api/auth/login' };

        // Make requests up to the login limit
        for (let i = 0; i < SECURITY_CONFIG.rateLimits.login.points; i++) {
            await rateLimitMiddleware(mockRequest as NextRequest);
        }

        // Next request should be blocked
        const response = await rateLimitMiddleware(mockRequest as NextRequest);
        expect(response.status).toBe(429);
        const body = await response.json();
        expect(body.error).toContain('Too many login attempts');
    });

    test('should include retry-after header when rate limited', async () => {
        mockRequest.nextUrl = { pathname: '/api/auth/login' };

        // Exceed login limit
        for (let i = 0; i <= SECURITY_CONFIG.rateLimits.login.points; i++) {
            await rateLimitMiddleware(mockRequest as NextRequest);
        }

        const response = await rateLimitMiddleware(mockRequest as NextRequest);
        expect(response.headers.get('Retry-After')).toBeDefined();
    });

    test('should track limits separately for different IPs', async () => {
        const secondIp = '127.0.0.2';
        
        // Exceed limit for first IP
        for (let i = 0; i < SECURITY_CONFIG.rateLimits.api.points; i++) {
            await rateLimitMiddleware(mockRequest as NextRequest);
        }

        // Should still allow requests from second IP
        mockRequest.ip = secondIp;
        const response = await rateLimitMiddleware(mockRequest as NextRequest);
        expect(response.status).not.toBe(429);
    });
}); 