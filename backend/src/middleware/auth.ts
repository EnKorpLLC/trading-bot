import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { logger } from '../utils/logger';

interface AuthenticatedRequest extends Request {
    user?: {
        id: string;
        email: string;
    };
}

export function authMiddleware(req: AuthenticatedRequest, res: Response, next: NextFunction): void {
    try {
        const authHeader = req.headers.authorization;
        if (!authHeader) {
            res.status(401).json({ error: 'No authorization header' });
            return;
        }

        const token = authHeader.split(' ')[1];
        if (!token) {
            res.status(401).json({ error: 'No token provided' });
            return;
        }

        const jwtSecret = process.env.JWT_SECRET;
        if (!jwtSecret) {
            logger.error('JWT_SECRET is not defined');
            res.status(500).json({ error: 'Internal server error' });
            return;
        }

        const decoded = jwt.verify(token, jwtSecret) as {
            id: string;
            email: string;
        };

        req.user = decoded;
        next();
    } catch (error) {
        if (error instanceof jwt.JsonWebTokenError) {
            res.status(401).json({ error: 'Invalid token' });
        } else {
            logger.error('Auth middleware error:', error);
            res.status(500).json({ error: 'Internal server error' });
        }
    }
} 