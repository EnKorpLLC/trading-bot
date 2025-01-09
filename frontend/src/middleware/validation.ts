import { NextRequest, NextResponse } from 'next/server';
import { SECURITY_CONFIG } from '@/config/security';
import { OrderRequest, OrderType, OrderSide } from '@/types/trading';

interface ValidationRule {
    validate: (value: any) => boolean;
    message: string;
}

const VALIDATION_RULES = {
    symbol: {
        validate: (value: string) => SECURITY_CONFIG.validation.allowedSymbols.includes(value),
        message: `Symbol must be one of: ${SECURITY_CONFIG.validation.allowedSymbols.join(', ')}`
    },
    orderType: {
        validate: (value: string) => Object.values(OrderType).includes(value as OrderType),
        message: `Order type must be one of: ${Object.values(OrderType).join(', ')}`
    },
    orderSide: {
        validate: (value: string) => Object.values(OrderSide).includes(value as OrderSide),
        message: `Order side must be one of: ${Object.values(OrderSide).join(', ')}`
    },
    quantity: {
        validate: (value: number) => value > 0 && value <= SECURITY_CONFIG.validation.maxOrderSize,
        message: `Quantity must be between 0 and ${SECURITY_CONFIG.validation.maxOrderSize}`
    },
    price: {
        validate: (value: number) => value > 0,
        message: 'Price must be greater than 0'
    },
    leverage: {
        validate: (value: number) => value > 0 && value <= SECURITY_CONFIG.validation.maxLeverage,
        message: `Leverage must be between 0 and ${SECURITY_CONFIG.validation.maxLeverage}`
    }
};

function sanitizeInput(input: string): string {
    // Remove any potentially dangerous characters
    return input.replace(/[<>{}]/g, '');
}

function validateOrderRequest(order: OrderRequest): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Validate required fields
    if (!order.symbol) {
        errors.push('Symbol is required');
    } else if (!VALIDATION_RULES.symbol.validate(order.symbol)) {
        errors.push(VALIDATION_RULES.symbol.message);
    }

    if (!order.type) {
        errors.push('Order type is required');
    } else if (!VALIDATION_RULES.orderType.validate(order.type)) {
        errors.push(VALIDATION_RULES.orderType.message);
    }

    if (!order.side) {
        errors.push('Order side is required');
    } else if (!VALIDATION_RULES.orderSide.validate(order.side)) {
        errors.push(VALIDATION_RULES.orderSide.message);
    }

    if (!order.quantity) {
        errors.push('Quantity is required');
    } else if (!VALIDATION_RULES.quantity.validate(order.quantity)) {
        errors.push(VALIDATION_RULES.quantity.message);
    }

    // Validate conditional fields
    if (order.type !== OrderType.MARKET) {
        if (!order.price) {
            errors.push('Price is required for non-market orders');
        } else if (!VALIDATION_RULES.price.validate(order.price)) {
            errors.push(VALIDATION_RULES.price.message);
        }
    }

    if (order.leverage && !VALIDATION_RULES.leverage.validate(order.leverage)) {
        errors.push(VALIDATION_RULES.leverage.message);
    }

    return {
        isValid: errors.length === 0,
        errors
    };
}

export async function validationMiddleware(req: NextRequest) {
    try {
        // Check request body size
        const contentLength = parseInt(req.headers.get('content-length') || '0');
        const maxSize = parseInt(SECURITY_CONFIG.validation.maxRequestBodySize);
        
        if (contentLength > maxSize) {
            return new NextResponse(
                JSON.stringify({ error: 'Request body too large' }),
                { status: 413 }
            );
        }

        // Only validate POST/PUT requests
        if (['POST', 'PUT'].includes(req.method || '')) {
            const body = await req.json();

            // Sanitize all string inputs
            Object.keys(body).forEach(key => {
                if (typeof body[key] === 'string') {
                    body[key] = sanitizeInput(body[key]);
                }
            });

            // Validate order requests
            if (req.nextUrl.pathname.startsWith('/api/trading/orders')) {
                const validation = validateOrderRequest(body);
                if (!validation.isValid) {
                    return new NextResponse(
                        JSON.stringify({ 
                            error: 'Validation failed',
                            details: validation.errors
                        }),
                        { status: 400 }
                    );
                }
            }

            // Create new request with sanitized body
            const newRequest = new Request(req.url, {
                method: req.method,
                headers: req.headers,
                body: JSON.stringify(body)
            });

            return NextResponse.next({
                request: newRequest
            });
        }

        return NextResponse.next();
    } catch (error) {
        console.error('Validation middleware error:', error);
        return new NextResponse(
            JSON.stringify({ error: 'Invalid request body' }),
            { status: 400 }
        );
    }
} 