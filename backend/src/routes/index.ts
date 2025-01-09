import { Express } from 'express';
import { authMiddleware } from '../middleware/auth';
import { backupRoutes } from './backup';
import { tradingRoutes } from './trading';
import { userRoutes } from './user';

export function setupRoutes(app: Express): void {
    // Health check route
    app.get('/api/health', (req, res) => {
        res.status(200).json({ status: 'ok' });
    });

    // API routes
    app.use('/api/auth', userRoutes);
    app.use('/api/trading', authMiddleware, tradingRoutes);
    app.use('/api/backup', authMiddleware, backupRoutes);

    // Error handling middleware
    app.use((err: any, req: any, res: any, next: any) => {
        console.error(err.stack);
        res.status(500).json({
            error: 'Internal Server Error',
            message: process.env.NODE_ENV === 'development' ? err.message : undefined
        });
    });
} 