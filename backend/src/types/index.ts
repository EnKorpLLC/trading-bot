export interface User {
    id: string;
    email: string;
    password: string;
    createdAt: Date;
    updatedAt: Date;
}

export interface Trade {
    id: string;
    userId: string;
    symbol: string;
    side: 'buy' | 'sell';
    type: 'market' | 'limit';
    quantity: number;
    price: number;
    status: 'pending' | 'filled' | 'cancelled';
    createdAt: Date;
    updatedAt: Date;
}

export interface Position {
    id: string;
    userId: string;
    symbol: string;
    quantity: number;
    averagePrice: number;
    currentPrice: number;
    pnl: number;
    createdAt: Date;
    updatedAt: Date;
}

export interface Order {
    id: string;
    userId: string;
    symbol: string;
    side: 'buy' | 'sell';
    type: 'market' | 'limit' | 'stop' | 'take_profit' | 'trailing_stop';
    quantity: number;
    price: number;
    stopPrice?: number;
    trailingDistance?: number;
    status: 'pending' | 'filled' | 'cancelled';
    createdAt: Date;
    updatedAt: Date;
}

export interface BackupSchedule {
    id: string;
    userId: string;
    frequency: 'daily' | 'weekly' | 'monthly';
    timeOfDay: string;
    retentionDays: number;
    isActive: boolean;
    lastRun: Date | null;
    nextRun: Date;
    createdAt: Date;
    updatedAt: Date;
}

export interface BackupRecord {
    id: string;
    userId: string;
    type: 'full' | 'incremental';
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    sizeBytes: number;
    checksum: string;
    storagePath: string;
    metadata: Record<string, any>;
    createdAt: Date;
    completedAt: Date | null;
} 