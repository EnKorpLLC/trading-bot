import { test, expect } from '@playwright/test';
import { OrderType, OrderSide } from '@/types/trading';

test.describe('Trading Workflow', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to trading dashboard
        await page.goto('/trading');
        // Wait for the dashboard to load
        await page.waitForSelector('[data-testid="trading-dashboard"]');
    });

    test('should place a market order successfully', async ({ page }) => {
        // Fill order form
        await page.fill('[data-testid="symbol-input"]', 'BTC-USD');
        await page.selectOption('[data-testid="order-type-select"]', OrderType.MARKET);
        await page.selectOption('[data-testid="order-side-select"]', OrderSide.BUY);
        await page.fill('[data-testid="quantity-input"]', '1');

        // Submit order
        await page.click('[data-testid="submit-order-button"]');

        // Wait for success message
        const successMessage = await page.waitForSelector('[data-testid="order-success-message"]');
        expect(await successMessage.textContent()).toContain('Order submitted successfully');

        // Verify order appears in trade history
        await page.waitForSelector('[data-testid="trade-history-table"]');
        const tradeHistoryText = await page.textContent('[data-testid="trade-history-table"]');
        expect(tradeHistoryText).toContain('BTC-USD');
        expect(tradeHistoryText).toContain('MARKET');
        expect(tradeHistoryText).toContain('BUY');
    });

    test('should place a limit order successfully', async ({ page }) => {
        // Fill order form
        await page.fill('[data-testid="symbol-input"]', 'ETH-USD');
        await page.selectOption('[data-testid="order-type-select"]', OrderType.LIMIT);
        await page.selectOption('[data-testid="order-side-select"]', OrderSide.SELL);
        await page.fill('[data-testid="quantity-input"]', '1');
        await page.fill('[data-testid="price-input"]', '2000');

        // Submit order
        await page.click('[data-testid="submit-order-button"]');

        // Wait for success message
        const successMessage = await page.waitForSelector('[data-testid="order-success-message"]');
        expect(await successMessage.textContent()).toContain('Order submitted successfully');

        // Verify order appears in open orders
        await page.waitForSelector('[data-testid="open-orders-table"]');
        const openOrdersText = await page.textContent('[data-testid="open-orders-table"]');
        expect(openOrdersText).toContain('ETH-USD');
        expect(openOrdersText).toContain('LIMIT');
        expect(openOrdersText).toContain('SELL');
        expect(openOrdersText).toContain('2000');
    });

    test('should validate order inputs', async ({ page }) => {
        // Try to submit without required fields
        await page.click('[data-testid="submit-order-button"]');
        
        // Check for validation messages
        const errorMessages = await page.textContent('[data-testid="order-form-errors"]');
        expect(errorMessages).toContain('Symbol is required');
        expect(errorMessages).toContain('Quantity is required');

        // Try invalid quantity
        await page.fill('[data-testid="symbol-input"]', 'BTC-USD');
        await page.fill('[data-testid="quantity-input"]', '-1');
        await page.click('[data-testid="submit-order-button"]');
        
        const quantityError = await page.textContent('[data-testid="quantity-error"]');
        expect(quantityError).toContain('Quantity must be greater than 0');
    });

    test('should update position after order execution', async ({ page }) => {
        // Place market order
        await page.fill('[data-testid="symbol-input"]', 'BTC-USD');
        await page.selectOption('[data-testid="order-type-select"]', OrderType.MARKET);
        await page.selectOption('[data-testid="order-side-select"]', OrderSide.BUY);
        await page.fill('[data-testid="quantity-input"]', '1');
        await page.click('[data-testid="submit-order-button"]');

        // Wait for position update
        await page.waitForSelector('[data-testid="positions-table"]');
        const positionsText = await page.textContent('[data-testid="positions-table"]');
        expect(positionsText).toContain('BTC-USD');
        expect(positionsText).toContain('1');
    });

    test('should enforce risk management rules', async ({ page }) => {
        // Try to place order exceeding position limit
        await page.fill('[data-testid="symbol-input"]', 'BTC-USD');
        await page.selectOption('[data-testid="order-type-select"]', OrderType.MARKET);
        await page.selectOption('[data-testid="order-side-select"]', OrderSide.BUY);
        await page.fill('[data-testid="quantity-input"]', '1000'); // Large quantity

        await page.click('[data-testid="submit-order-button"]');

        // Check for risk management error
        const errorMessage = await page.waitForSelector('[data-testid="risk-error-message"]');
        expect(await errorMessage.textContent()).toContain('Exceeds maximum position size');
    });
}); 