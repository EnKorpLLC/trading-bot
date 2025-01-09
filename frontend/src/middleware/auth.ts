import { NextRequest, NextResponse } from 'next/server';
import { jwtVerify } from 'jose';
import { SECURITY_CONFIG } from '@/config/security';
import { query } from '@/utils/db';

const PUBLIC_PATHS = [
    '/api/auth/login',
    '/api/auth/register',
    '/api/auth/refresh',
    '/api/health'
];

export async function authMiddleware(req: NextRequest) {
    try {
        // Skip authentication for public paths
        if (PUBLIC_PATHS.some(path => req.nextUrl.pathname.startsWith(path))) {
            return NextResponse.next();
        }

        // Get token from Authorization header
        const authHeader = req.headers.get('authorization');
        if (!authHeader?.startsWith('Bearer ')) {
            return new NextResponse(
                JSON.stringify({ error: 'Unauthorized - No token provided' }),
                { status: 401 }
            );
        }

        const token = authHeader.split(' ')[1];

        // Verify JWT
        const secret = new TextEncoder().encode(process.env.JWT_SECRET);
        try {
            const { payload } = await jwtVerify(token, secret);
            
            // Check if session is still valid
            const session = await query(
                'SELECT * FROM user_sessions WHERE user_id = $1 AND token = $2 AND expires_at > NOW()',
                [payload.sub, token]
            );

            if (session.rows.length === 0) {
                return new NextResponse(
                    JSON.stringify({ error: 'Session expired or invalid' }),
                    { status: 401 }
                );
            }

            // Update last activity
            await query(
                'UPDATE user_sessions SET last_activity = NOW() WHERE token = $1',
                [token]
            );

            // Add user info to request
            const requestHeaders = new Headers(req.headers);
            requestHeaders.set('x-user-id', payload.sub as string);

            // Continue with the request
            return NextResponse.next({
                request: {
                    headers: requestHeaders,
                },
            });
        } catch (error) {
            console.error('Token verification failed:', error);
            return new NextResponse(
                JSON.stringify({ error: 'Invalid or expired token' }),
                { status: 401 }
            );
        }
    } catch (error) {
        console.error('Auth middleware error:', error);
        return new NextResponse(
            JSON.stringify({ error: 'Internal server error' }),
            { status: 500 }
        );
    }
}

// Helper function to validate password requirements
export function validatePassword(password: string): { isValid: boolean; message: string } {
    const { passwordRequirements } = SECURITY_CONFIG.auth;
    
    if (password.length < passwordRequirements.minLength) {
        return {
            isValid: false,
            message: `Password must be at least ${passwordRequirements.minLength} characters long`
        };
    }

    if (passwordRequirements.requireUppercase && !/[A-Z]/.test(password)) {
        return {
            isValid: false,
            message: 'Password must contain at least one uppercase letter'
        };
    }

    if (passwordRequirements.requireLowercase && !/[a-z]/.test(password)) {
        return {
            isValid: false,
            message: 'Password must contain at least one lowercase letter'
        };
    }

    if (passwordRequirements.requireNumbers && !/\d/.test(password)) {
        return {
            isValid: false,
            message: 'Password must contain at least one number'
        };
    }

    if (passwordRequirements.requireSpecialChars && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
        return {
            isValid: false,
            message: 'Password must contain at least one special character'
        };
    }

    return { isValid: true, message: 'Password meets all requirements' };
} 