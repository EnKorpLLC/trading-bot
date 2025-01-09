import { NextRequest } from 'next/server';
import { validationMiddleware } from '@/middleware/validation';
import { SECURITY_CONFIG } from '@/config/security';
import { OrderType, OrderSide } from '@/types/trading';

describe('Validation Middleware', () => {
    let mockRequest: Partial<NextRequest>;

    beforeEach(() => {
        mockRequest = {
            nextUrl: { pathname: '/api/trading/orders' },
            headers: new Headers({
                'content-type': 'application/json',
                'content-length': '100'
            }),
            method: 'POST'
        };
    });

    test('should reject oversized requests', async () => {
        mockRequest.headers.set('content-length', '1000000'); // 1MB
        const response = await validationMiddleware(mockRequest as NextRequest);
        expect(response.status).toBe(413);
        const body = await response.json();
        expect(body.error).toContain('Request body too large');
    });

    test('should sanitize input strings', async () => {
        const requestBody = {
            symbol: 'BTC-USD<script>alert("xss")</script>',
            type: OrderType.MARKET,
            side: OrderSide.BUY,
            quantity: 1
        };

        mockRequest.json = jest.fn().mockResolvedValue(requestBody);
        const response = await validationMiddleware(mockRequest as NextRequest);
        
        // Get the sanitized body from the new request
        const newRequest = (response as any).request as Request;
        const sanitizedBody = await newRequest.json();
        
        expect(sanitizedBody.symbol).not.toContain('<script>');
    });

    describe('Order Validation', () => {
        test('should validate valid market order', async () => {
            const validOrder = {
                symbol: 'BTC-USD',
                type: OrderType.MARKET,
                side: OrderSide.BUY,
                quantity: 1
            };

            mockRequest.json = jest.fn().mockResolvedValue(validOrder);
            const response = await validationMiddleware(mockRequest as NextRequest);
            expect(response.status).not.toBe(400);
        });

        test('should reject invalid symbol', async () => {
            const invalidOrder = {
                symbol: 'INVALID-PAIR',
                type: OrderType.MARKET,
                side: OrderSide.BUY,
                quantity: 1
            };

            mockRequest.json = jest.fn().mockResolvedValue(invalidOrder);
            const response = await validationMiddleware(mockRequest as NextRequest);
            expect(response.status).toBe(400);
            const body = await response.json();
            expect(body.details).toContain(expect.stringContaining('Symbol must be one of'));
        });

        test('should reject invalid order type', async () => {
            const invalidOrder = {
                symbol: 'BTC-USD',
                type: 'INVALID_TYPE',
                side: OrderSide.BUY,
                quantity: 1
            };

            mockRequest.json = jest.fn().mockResolvedValue(invalidOrder);
            const response = await validationMiddleware(mockRequest as NextRequest);
            expect(response.status).toBe(400);
            const body = await response.json();
            expect(body.details).toContain(expect.stringContaining('Order type must be one of'));
        });

        test('should reject excessive quantity', async () => {
            const invalidOrder = {
                symbol: 'BTC-USD',
                type: OrderType.MARKET,
                side: OrderSide.BUY,
                quantity: SECURITY_CONFIG.validation.maxOrderSize + 1
            };

            mockRequest.json = jest.fn().mockResolvedValue(invalidOrder);
            const response = await validationMiddleware(mockRequest as NextRequest);
            expect(response.status).toBe(400);
            const body = await response.json();
            expect(body.details).toContain(expect.stringContaining('Quantity must be between'));
        });

        test('should require price for limit orders', async () => {
            const invalidOrder = {
                symbol: 'BTC-USD',
                type: OrderType.LIMIT,
                side: OrderSide.BUY,
                quantity: 1
                // Missing price
            };

            mockRequest.json = jest.fn().mockResolvedValue(invalidOrder);
            const response = await validationMiddleware(mockRequest as NextRequest);
            expect(response.status).toBe(400);
            const body = await response.json();
            expect(body.details).toContain('Price is required for non-market orders');
        });

        test('should validate leverage limits', async () => {
            const invalidOrder = {
                symbol: 'BTC-USD',
                type: OrderType.MARKET,
                side: OrderSide.BUY,
                quantity: 1,
                leverage: SECURITY_CONFIG.validation.maxLeverage + 1
            };

            mockRequest.json = jest.fn().mockResolvedValue(invalidOrder);
            const response = await validationMiddleware(mockRequest as NextRequest);
            expect(response.status).toBe(400);
            const body = await response.json();
            expect(body.details).toContain(expect.stringContaining('Leverage must be between'));
        });
    });
}); 