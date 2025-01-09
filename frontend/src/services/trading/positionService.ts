import { query } from '@/utils/db';
import { Position, Trade, OrderSide } from '@/types/trading';

export class PositionService {
    public async getPosition(userId: string, symbol: string): Promise<Position | null> {
        const result = await query(
            `SELECT * FROM positions 
            WHERE user_id = $1 AND symbol = $2 AND status = 'OPEN'`,
            [userId, symbol]
        );

        return result.rows[0] || null;
    }

    public async getAllPositions(userId: string): Promise<Position[]> {
        const result = await query(
            `SELECT * FROM positions 
            WHERE user_id = $1 AND status = 'OPEN'
            ORDER BY created_at DESC`,
            [userId]
        );

        return result.rows;
    }

    public async updatePosition(trade: Trade): Promise<Position> {
        const { userId, symbol, side, quantity, price } = trade;
        
        try {
            // Start transaction
            await query('BEGIN');

            // Get existing position or create new one
            let position = await this.getPosition(userId, symbol);
            const isNewPosition = !position;

            if (isNewPosition) {
                // Create new position
                const result = await query(
                    `INSERT INTO positions (
                        user_id, symbol, quantity, average_entry_price,
                        unrealized_pnl, realized_pnl, last_trade_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *`,
                    [userId, symbol, 0, 0, 0, 0, trade.id]
                );
                position = result.rows[0];
            }

            // Calculate new position details
            const signedQuantity = side === OrderSide.BUY ? quantity : -quantity;
            const newQuantity = (position.quantity || 0) + signedQuantity;

            // Calculate new average entry price
            let newAveragePrice = position.average_entry_price || 0;
            if (side === OrderSide.BUY && newQuantity > 0) {
                newAveragePrice = (
                    (position.quantity * position.average_entry_price) +
                    (quantity * price)
                ) / newQuantity;
            }

            // Update position
            const result = await query(
                `UPDATE positions 
                SET quantity = $1,
                    average_entry_price = $2,
                    last_trade_id = $3,
                    status = $4
                WHERE id = $5
                RETURNING *`,
                [
                    newQuantity,
                    newAveragePrice,
                    trade.id,
                    newQuantity === 0 ? 'CLOSED' : 'OPEN',
                    position.id
                ]
            );

            // Commit transaction
            await query('COMMIT');

            return result.rows[0];
        } catch (error) {
            // Rollback transaction on error
            await query('ROLLBACK');
            throw error;
        }
    }

    public async calculateUnrealizedPnL(position: Position, currentPrice: number): Promise<number> {
        return position.quantity * (currentPrice - position.average_entry_price);
    }
} 