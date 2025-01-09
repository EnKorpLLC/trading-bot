import { Position, Order, Trade, RiskSettings, TradingStrategy } from '@/types/trading';

interface BackupData {
    timestamp: string;
    userId: string;
    positions: Position[];
    orders: Order[];
    trades: Trade[];
    riskSettings: RiskSettings;
    strategies: TradingStrategy[];
    metadata: {
        version: string;
        checksum: string;
        backupType: 'full' | 'incremental';
    };
}

export class BackupService {
    private readonly API_URL = process.env.NEXT_PUBLIC_API_URL;

    public async createBackup(userId: string): Promise<string> {
        try {
            const response = await fetch(`${this.API_URL}/backup/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ userId })
            });

            if (!response.ok) {
                throw new Error('Failed to create backup');
            }

            const { backupId } = await response.json();
            return backupId;
        } catch (error) {
            console.error('Backup creation failed:', error);
            throw error;
        }
    }

    public async getBackups(userId: string): Promise<BackupData[]> {
        try {
            const response = await fetch(
                `${this.API_URL}/backup/list?userId=${userId}`
            );

            if (!response.ok) {
                throw new Error('Failed to fetch backups');
            }

            return response.json();
        } catch (error) {
            console.error('Failed to fetch backups:', error);
            throw error;
        }
    }

    public async restoreBackup(backupId: string): Promise<void> {
        try {
            const response = await fetch(`${this.API_URL}/backup/restore`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ backupId })
            });

            if (!response.ok) {
                throw new Error('Failed to restore backup');
            }
        } catch (error) {
            console.error('Backup restoration failed:', error);
            throw error;
        }
    }

    public async exportData(userId: string, format: 'json' | 'csv' = 'json'): Promise<Blob> {
        try {
            const response = await fetch(
                `${this.API_URL}/backup/export?userId=${userId}&format=${format}`
            );

            if (!response.ok) {
                throw new Error('Failed to export data');
            }

            return response.blob();
        } catch (error) {
            console.error('Data export failed:', error);
            throw error;
        }
    }

    public async scheduleBackup(
        userId: string,
        schedule: {
            frequency: 'daily' | 'weekly' | 'monthly';
            time: string;
            retentionDays: number;
        }
    ): Promise<void> {
        try {
            const response = await fetch(`${this.API_URL}/backup/schedule`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ userId, schedule })
            });

            if (!response.ok) {
                throw new Error('Failed to schedule backup');
            }
        } catch (error) {
            console.error('Failed to schedule backup:', error);
            throw error;
        }
    }

    public async verifyBackup(backupId: string): Promise<{
        isValid: boolean;
        details: {
            timestamp: string;
            size: number;
            checksum: string;
            integrityCheck: boolean;
        };
    }> {
        try {
            const response = await fetch(
                `${this.API_URL}/backup/verify/${backupId}`
            );

            if (!response.ok) {
                throw new Error('Failed to verify backup');
            }

            return response.json();
        } catch (error) {
            console.error('Backup verification failed:', error);
            throw error;
        }
    }

    public async deleteBackup(backupId: string): Promise<void> {
        try {
            const response = await fetch(`${this.API_URL}/backup/${backupId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete backup');
            }
        } catch (error) {
            console.error('Backup deletion failed:', error);
            throw error;
        }
    }
} 