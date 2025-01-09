import { Router } from 'express';
import { pool } from '../database';
import { logger } from '../utils/logger';
import { BackupRecord, BackupSchedule } from '../types';
import path from 'path';
import fs from 'fs/promises';
import crypto from 'crypto';

const router = Router();

// Create a new backup
router.post('/create', async (req, res) => {
    try {
        const userId = (req as any).user.id;
        const { type = 'full' } = req.body;

        // Create backup record
        const result = await pool.query<BackupRecord>(
            `INSERT INTO backups (
                user_id, type, status, storage_path, metadata
            ) VALUES ($1, $2, $3, $4, $5) 
            RETURNING *`,
            [
                userId,
                type,
                'pending',
                path.join(process.env.BACKUP_STORAGE_PATH!, `${userId}_${Date.now()}.bak`),
                JSON.stringify({ timestamp: new Date() })
            ]
        );

        const backup = result.rows[0];

        // Trigger backup process
        performBackup(backup.id).catch(error => {
            logger.error('Backup process failed:', error);
        });

        res.status(201).json(backup);
    } catch (error) {
        logger.error('Backup creation error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Get user's backups
router.get('/list', async (req, res) => {
    try {
        const userId = (req as any).user.id;

        const result = await pool.query<BackupRecord>(
            'SELECT * FROM backups WHERE user_id = $1 ORDER BY created_at DESC',
            [userId]
        );

        res.json(result.rows);
    } catch (error) {
        logger.error('Backups fetch error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Schedule backups
router.post('/schedule', async (req, res) => {
    try {
        const userId = (req as any).user.id;
        const { frequency, timeOfDay, retentionDays } = req.body;

        // Validate input
        if (!frequency || !timeOfDay || !retentionDays) {
            return res.status(400).json({ error: 'Missing required fields' });
        }

        // Create or update schedule
        const result = await pool.query<BackupSchedule>(
            `INSERT INTO backup_schedules (
                user_id, frequency, time_of_day, retention_days, is_active
            ) VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id) DO UPDATE
            SET frequency = $2, time_of_day = $3, retention_days = $4, is_active = $5
            RETURNING *`,
            [userId, frequency, timeOfDay, retentionDays, true]
        );

        res.json(result.rows[0]);
    } catch (error) {
        logger.error('Backup schedule error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Get backup schedule
router.get('/schedule', async (req, res) => {
    try {
        const userId = (req as any).user.id;

        const result = await pool.query<BackupSchedule>(
            'SELECT * FROM backup_schedules WHERE user_id = $1',
            [userId]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'No backup schedule found' });
        }

        res.json(result.rows[0]);
    } catch (error) {
        logger.error('Backup schedule fetch error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Restore from backup
router.post('/restore/:backupId', async (req, res) => {
    try {
        const userId = (req as any).user.id;
        const { backupId } = req.params;

        // Verify backup exists and belongs to user
        const backup = await pool.query<BackupRecord>(
            'SELECT * FROM backups WHERE id = $1 AND user_id = $2',
            [backupId, userId]
        );

        if (backup.rows.length === 0) {
            return res.status(404).json({ error: 'Backup not found' });
        }

        // Start restore process
        await performRestore(backup.rows[0]);

        res.json({ message: 'Restore process started' });
    } catch (error) {
        logger.error('Restore error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

async function performBackup(backupId: string): Promise<void> {
    try {
        // Update status to in_progress
        await pool.query(
            'UPDATE backups SET status = $1 WHERE id = $2',
            ['in_progress', backupId]
        );

        // Get backup details
        const result = await pool.query<BackupRecord>(
            'SELECT * FROM backups WHERE id = $1',
            [backupId]
        );

        const backup = result.rows[0];

        // Ensure backup directory exists
        await fs.mkdir(path.dirname(backup.storagePath), { recursive: true });

        // Get user data
        const userData = await pool.query(
            `SELECT json_build_object(
                'trades', (SELECT json_agg(t.*) FROM trades t WHERE user_id = $1),
                'orders', (SELECT json_agg(o.*) FROM orders o WHERE user_id = $1),
                'positions', (SELECT json_agg(p.*) FROM positions p WHERE user_id = $1)
            ) as data`,
            [backup.userId]
        );

        // Write backup file
        const backupData = JSON.stringify(userData.rows[0].data);
        await fs.writeFile(backup.storagePath, backupData);

        // Calculate checksum
        const checksum = crypto
            .createHash('sha256')
            .update(backupData)
            .digest('hex');

        // Update backup record
        await pool.query(
            `UPDATE backups 
            SET status = $1, 
                checksum = $2, 
                size_bytes = $3, 
                completed_at = CURRENT_TIMESTAMP 
            WHERE id = $4`,
            ['completed', checksum, Buffer.from(backupData).length, backupId]
        );

        logger.info(`Backup ${backupId} completed successfully`);
    } catch (error) {
        logger.error(`Backup ${backupId} failed:`, error);
        await pool.query(
            'UPDATE backups SET status = $1 WHERE id = $2',
            ['failed', backupId]
        );
    }
}

async function performRestore(backup: BackupRecord): Promise<void> {
    try {
        // Read backup file
        const backupData = await fs.readFile(backup.storagePath, 'utf-8');

        // Verify checksum
        const checksum = crypto
            .createHash('sha256')
            .update(backupData)
            .digest('hex');

        if (checksum !== backup.checksum) {
            throw new Error('Backup file corrupted');
        }

        const data = JSON.parse(backupData);

        // Start transaction
        const client = await pool.connect();
        try {
            await client.query('BEGIN');

            // Clear existing data
            await client.query(
                `DELETE FROM trades WHERE user_id = $1;
                 DELETE FROM orders WHERE user_id = $1;
                 DELETE FROM positions WHERE user_id = $1;`,
                [backup.userId]
            );

            // Restore data
            if (data.trades) {
                for (const trade of data.trades) {
                    await client.query(
                        `INSERT INTO trades 
                        (id, user_id, symbol, side, type, quantity, price, status, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
                        [trade.id, trade.user_id, trade.symbol, trade.side, trade.type,
                         trade.quantity, trade.price, trade.status, trade.created_at, trade.updated_at]
                    );
                }
            }

            if (data.orders) {
                for (const order of data.orders) {
                    await client.query(
                        `INSERT INTO orders 
                        (id, user_id, symbol, side, type, quantity, price, status, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
                        [order.id, order.user_id, order.symbol, order.side, order.type,
                         order.quantity, order.price, order.status, order.created_at, order.updated_at]
                    );
                }
            }

            if (data.positions) {
                for (const position of data.positions) {
                    await client.query(
                        `INSERT INTO positions 
                        (id, user_id, symbol, quantity, average_price, current_price, pnl, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
                        [position.id, position.user_id, position.symbol, position.quantity,
                         position.average_price, position.current_price, position.pnl,
                         position.created_at, position.updated_at]
                    );
                }
            }

            await client.query('COMMIT');
            logger.info(`Restore from backup ${backup.id} completed successfully`);
        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    } catch (error) {
        logger.error(`Restore from backup ${backup.id} failed:`, error);
        throw error;
    }
}

export const backupRoutes = router; 