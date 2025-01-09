import { NextRequest, NextResponse } from 'next/server';
import { apiLimiter, loginLimiter } from '@/config/security';

export async function rateLimitMiddleware(req: NextRequest) {
    try {
        const ip = req.ip || req.headers.get('x-forwarded-for') || 'unknown';
        const path = req.nextUrl.pathname;

        // Use login limiter for authentication endpoints
        if (path.startsWith('/api/auth/')) {
            try {
                await loginLimiter.consume(ip);
            } catch (error) {
                return new NextResponse(
                    JSON.stringify({
                        error: 'Too many login attempts. Please try again later.'
                    }),
                    {
                        status: 429,
                        headers: {
                            'Retry-After': String(error.msBeforeNext / 1000),
                            'Content-Type': 'application/json'
                        }
                    }
                );
            }
        }
        // Use API limiter for all other endpoints
        else if (path.startsWith('/api/')) {
            try {
                const rateLimitRes = await apiLimiter.consume(ip);
                const response = NextResponse.next();
                
                // Add rate limit headers
                response.headers.set('X-RateLimit-Limit', String(apiLimiter.points));
                response.headers.set('X-RateLimit-Remaining', String(rateLimitRes.remainingPoints));
                response.headers.set('X-RateLimit-Reset', String(rateLimitRes.msBeforeNext));
                
                return response;
            } catch (error) {
                return new NextResponse(
                    JSON.stringify({
                        error: 'Too many requests. Please try again later.'
                    }),
                    {
                        status: 429,
                        headers: {
                            'Retry-After': String(error.msBeforeNext / 1000),
                            'Content-Type': 'application/json'
                        }
                    }
                );
            }
        }

        return NextResponse.next();
    } catch (error) {
        console.error('Rate limit middleware error:', error);
        return new NextResponse(
            JSON.stringify({ error: 'Internal server error' }),
            { status: 500 }
        );
    }
} 