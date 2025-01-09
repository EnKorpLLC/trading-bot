import WebSocket from 'ws';
import { logger } from '../utils/logger';

interface WebSocketMessage {
    type: string;
    data: any;
}

export function setupWebSocket(wss: WebSocket.Server): void {
    wss.on('connection', (ws: WebSocket) => {
        logger.info('New WebSocket connection established');

        // Send initial connection status
        ws.send(JSON.stringify({ type: 'connection', status: 'connected' }));

        // Handle incoming messages
        ws.on('message', async (message: string) => {
            try {
                const parsedMessage: WebSocketMessage = JSON.parse(message);
                await handleWebSocketMessage(ws, parsedMessage);
            } catch (error) {
                logger.error('Error handling WebSocket message:', error);
                ws.send(JSON.stringify({
                    type: 'error',
                    data: 'Invalid message format'
                }));
            }
        });

        // Handle client disconnection
        ws.on('close', () => {
            logger.info('Client disconnected');
        });

        // Handle errors
        ws.on('error', (error) => {
            logger.error('WebSocket error:', error);
        });
    });
}

async function handleWebSocketMessage(ws: WebSocket, message: WebSocketMessage): Promise<void> {
    switch (message.type) {
        case 'subscribe':
            await handleSubscription(ws, message.data);
            break;
        case 'unsubscribe':
            await handleUnsubscription(ws, message.data);
            break;
        case 'market_data':
            await handleMarketData(ws, message.data);
            break;
        default:
            ws.send(JSON.stringify({
                type: 'error',
                data: 'Unknown message type'
            }));
    }
}

async function handleSubscription(ws: WebSocket, data: any): Promise<void> {
    // Handle market data subscriptions
    try {
        // Implement subscription logic here
        ws.send(JSON.stringify({
            type: 'subscription_success',
            data: { channel: data.channel }
        }));
    } catch (error) {
        logger.error('Subscription error:', error);
        ws.send(JSON.stringify({
            type: 'subscription_error',
            data: 'Failed to subscribe'
        }));
    }
}

async function handleUnsubscription(ws: WebSocket, data: any): Promise<void> {
    // Handle market data unsubscriptions
    try {
        // Implement unsubscription logic here
        ws.send(JSON.stringify({
            type: 'unsubscription_success',
            data: { channel: data.channel }
        }));
    } catch (error) {
        logger.error('Unsubscription error:', error);
        ws.send(JSON.stringify({
            type: 'unsubscription_error',
            data: 'Failed to unsubscribe'
        }));
    }
}

async function handleMarketData(ws: WebSocket, data: any): Promise<void> {
    // Handle incoming market data
    try {
        // Implement market data handling logic here
        ws.send(JSON.stringify({
            type: 'market_data_processed',
            data: { status: 'success' }
        }));
    } catch (error) {
        logger.error('Market data processing error:', error);
        ws.send(JSON.stringify({
            type: 'market_data_error',
            data: 'Failed to process market data'
        }));
    }
} 