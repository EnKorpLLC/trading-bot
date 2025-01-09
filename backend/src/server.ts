import express from 'express';
import { createServer } from 'http';
import WebSocket from 'ws';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import { setupRoutes } from './routes';
import { setupWebSocket } from './websocket';
import { initializeDatabase } from './database';
import { logger } from './utils/logger';

dotenv.config();

const app = express();
const server = createServer(app);
const wss = new WebSocket.Server({ server });

// Middleware
app.use(cors());
app.use(helmet());
app.use(express.json());

// Initialize components
setupRoutes(app);
setupWebSocket(wss);

const PORT = process.env.PORT || 3001;

async function startServer() {
    try {
        // Initialize database connection
        await initializeDatabase();

        // Start the server
        server.listen(PORT, () => {
            logger.info(`Server running on port ${PORT}`);
            logger.info('WebSocket server is ready');
        });
    } catch (error) {
        logger.error('Failed to start server:', error);
        process.exit(1);
    }
}

// Handle graceful shutdown
process.on('SIGTERM', () => {
    logger.info('SIGTERM received. Shutting down gracefully...');
    server.close(() => {
        logger.info('Server closed');
        process.exit(0);
    });
});

startServer(); 