import { RateLimiterMemory } from 'rate-limiter-flexible';

export const SECURITY_CONFIG = {
    // Rate limiting settings
    rateLimits: {
        // API rate limits
        api: {
            points: 100,           // Number of requests
            duration: 60,          // Per 60 seconds
            blockDuration: 300     // Block for 5 minutes if exceeded
        },
        // Login attempt limits
        login: {
            points: 5,            // Number of attempts
            duration: 300,        // Per 5 minutes
            blockDuration: 900    // Block for 15 minutes if exceeded
        },
        // WebSocket connection limits
        websocket: {
            points: 10,           // Number of connections
            duration: 60,         // Per minute
            blockDuration: 300    // Block for 5 minutes if exceeded
        }
    },

    // CORS Configuration
    cors: {
        allowedOrigins: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
        allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
        exposedHeaders: ['Content-Length', 'X-Rate-Limit'],
        maxAge: 600, // 10 minutes
        credentials: true
    },

    // Authentication settings
    auth: {
        jwtExpiresIn: '24h',
        jwtRefreshExpiresIn: '7d',
        passwordMinLength: 12,
        passwordRequirements: {
            minLength: 12,
            requireUppercase: true,
            requireLowercase: true,
            requireNumbers: true,
            requireSpecialChars: true
        },
        sessionTimeout: 3600, // 1 hour in seconds
        maxSessionsPerUser: 5
    },

    // Input validation
    validation: {
        maxRequestBodySize: '10kb',
        allowedSymbols: ['BTC-USD', 'ETH-USD', 'XRP-USD'], // Add more as needed
        maxOrderSize: 100,
        maxLeverage: 10
    },

    // Security headers
    headers: {
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
};

// Create rate limiters
export const apiLimiter = new RateLimiterMemory({
    points: SECURITY_CONFIG.rateLimits.api.points,
    duration: SECURITY_CONFIG.rateLimits.api.duration,
    blockDuration: SECURITY_CONFIG.rateLimits.api.blockDuration
});

export const loginLimiter = new RateLimiterMemory({
    points: SECURITY_CONFIG.rateLimits.login.points,
    duration: SECURITY_CONFIG.rateLimits.login.duration,
    blockDuration: SECURITY_CONFIG.rateLimits.login.blockDuration
});

export const wsLimiter = new RateLimiterMemory({
    points: SECURITY_CONFIG.rateLimits.websocket.points,
    duration: SECURITY_CONFIG.rateLimits.websocket.duration,
    blockDuration: SECURITY_CONFIG.rateLimits.websocket.blockDuration
}); 