import { Router } from 'express';
import { pool } from '../database';
import { logger } from '../utils/logger';
import { Order, Position, Trade } from '../types';

const router = Router();

// Place a new order
router.post('/orders', async (req, res) => {
    try {
        const userId = (req as any).user.id;
        const { symbol, side, type, quantity, price, stopPrice, trailingDistance } = req.body;

        // Validate input
        if (!symbol || !side || !type || !quantity) {
            return res.status(400).json({ error: 'Missing required fields' });
        }

        // Create order
        const result = await pool.query<Order>(
            `INSERT INTO orders (
                user_id, symbol, side, type, quantity, price, stop_price, trailing_distance, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) 
            RETURNING *`,
            [userId, symbol, side, type, quantity, price, stopPrice, trailingDistance, 'pending']
        );

        const order = result.rows[0];
        res.status(201).json(order);
    } catch (error) {
        logger.error('Order creation error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Get user's orders
router.get('/orders', async (req, res) => {
    try {
        const userId = (req as any).user.id;
        const { status } = req.query;

        let query = 'SELECT * FROM orders WHERE user_id = $1';
        const params = [userId];

        if (status) {
            query += ' AND status = $2';
            params.push(status as string);
        }

        query += ' ORDER BY created_at DESC';

        const result = await pool.query<Order>(query, params);
        res.json(result.rows);
    } catch (error) {
        logger.error('Orders fetch error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Cancel an order
router.post('/orders/:orderId/cancel', async (req, res) => {
    try {
        const userId = (req as any).user.id;
        const { orderId } = req.params;

        const result = await pool.query<Order>(
            'UPDATE orders SET status = $1 WHERE id = $2 AND user_id = $3 AND status = $4 RETURNING *',
            ['cancelled', orderId, userId, 'pending']
        );

        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'Order not found or already executed' });
        }

        res.json(result.rows[0]);
    } catch (error) {
        logger.error('Order cancellation error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Get user's positions
router.get('/positions', async (req, res) => {
    try {
        const userId = (req as any).user.id;

        const result = await pool.query<Position>(
            'SELECT * FROM positions WHERE user_id = $1',
            [userId]
        );

        res.json(result.rows);
    } catch (error) {
        logger.error('Positions fetch error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Get user's trade history
router.get('/trades', async (req, res) => {
    try {
        const userId = (req as any).user.id;
        const { symbol, limit = 50, offset = 0 } = req.query;

        let query = 'SELECT * FROM trades WHERE user_id = $1';
        const params = [userId];

        if (symbol) {
            query += ' AND symbol = $2';
            params.push(symbol as string);
        }

        query += ' ORDER BY created_at DESC LIMIT $' + (params.length + 1) + ' OFFSET $' + (params.length + 2);
        params.push(limit as string, offset as string);

        const result = await pool.query<Trade>(query, params);
        res.json(result.rows);
    } catch (error) {
        logger.error('Trades fetch error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

export const tradingRoutes = router; 