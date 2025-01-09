import { NextRequest } from 'next/server';
import { authMiddleware, validatePassword } from '@/middleware/auth';
import { SECURITY_CONFIG } from '@/config/security';

describe('Authentication Middleware', () => {
    let mockRequest: Partial<NextRequest>;

    beforeEach(() => {
        mockRequest = {
            nextUrl: { pathname: '/api/trading/orders' },
            headers: new Headers(),
            method: 'GET'
        };
    });

    test('should reject requests without authorization header', async () => {
        const response = await authMiddleware(mockRequest as NextRequest);
        expect(response.status).toBe(401);
        const body = await response.json();
        expect(body.error).toBe('Unauthorized - No token provided');
    });

    test('should reject invalid token format', async () => {
        mockRequest.headers = new Headers({
            'authorization': 'InvalidFormat token123'
        });
        const response = await authMiddleware(mockRequest as NextRequest);
        expect(response.status).toBe(401);
    });

    test('should allow access to public paths without token', async () => {
        mockRequest.nextUrl = { pathname: '/api/auth/login' };
        const response = await authMiddleware(mockRequest as NextRequest);
        expect(response.status).not.toBe(401);
    });
});

describe('Password Validation', () => {
    const requirements = SECURITY_CONFIG.auth.passwordRequirements;

    test('should reject passwords shorter than minimum length', () => {
        const result = validatePassword('Short1!');
        expect(result.isValid).toBe(false);
        expect(result.message).toContain(`at least ${requirements.minLength} characters`);
    });

    test('should require uppercase letters', () => {
        const result = validatePassword('lowercase123!');
        expect(result.isValid).toBe(false);
        expect(result.message).toContain('uppercase letter');
    });

    test('should require lowercase letters', () => {
        const result = validatePassword('UPPERCASE123!');
        expect(result.isValid).toBe(false);
        expect(result.message).toContain('lowercase letter');
    });

    test('should require numbers', () => {
        const result = validatePassword('Password!@#');
        expect(result.isValid).toBe(false);
        expect(result.message).toContain('number');
    });

    test('should require special characters', () => {
        const result = validatePassword('Password123');
        expect(result.isValid).toBe(false);
        expect(result.message).toContain('special character');
    });

    test('should accept valid passwords', () => {
        const result = validatePassword('SecurePassword123!@#');
        expect(result.isValid).toBe(true);
        expect(result.message).toBe('Password meets all requirements');
    });
}); 