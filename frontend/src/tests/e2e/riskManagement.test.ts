import { test, expect } from '@playwright/test';

test.describe('Risk Management Workflow', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to risk management page
        await page.goto('/trading');
        // Wait for the risk management section to load
        await page.waitForSelector('[data-testid="risk-management-panel"]');
    });

    test('should update risk settings successfully', async ({ page }) => {
        // Click edit button
        await page.click('[data-testid="edit-risk-settings-button"]');

        // Update risk parameters
        await page.fill('[data-testid="max-position-size-input"]', '0.15');
        await page.fill('[data-testid="risk-per-trade-input"]', '0.02');
        await page.fill('[data-testid="max-daily-loss-input"]', '0.03');

        // Save changes
        await page.click('[data-testid="save-risk-settings-button"]');

        // Verify success message
        const successMessage = await page.waitForSelector('[data-testid="settings-success-message"]');
        expect(await successMessage.textContent()).toContain('Risk settings updated successfully');

        // Verify updated values are displayed
        const maxPositionSize = await page.textContent('[data-testid="max-position-size-value"]');
        const riskPerTrade = await page.textContent('[data-testid="risk-per-trade-value"]');
        const maxDailyLoss = await page.textContent('[data-testid="max-daily-loss-value"]');

        expect(maxPositionSize).toContain('15.0%');
        expect(riskPerTrade).toContain('2.0%');
        expect(maxDailyLoss).toContain('3.0%');
    });

    test('should validate risk parameter inputs', async ({ page }) => {
        // Click edit button
        await page.click('[data-testid="edit-risk-settings-button"]');

        // Try invalid values
        await page.fill('[data-testid="max-position-size-input"]', '1.5'); // Over 100%
        await page.fill('[data-testid="risk-per-trade-input"]', '-0.01'); // Negative value
        
        // Try to save
        await page.click('[data-testid="save-risk-settings-button"]');

        // Check error messages
        const errors = await page.textContent('[data-testid="risk-settings-errors"]');
        expect(errors).toContain('Maximum position size cannot exceed 100%');
        expect(errors).toContain('Risk per trade must be positive');
    });

    test('should display current risk metrics', async ({ page }) => {
        // Wait for risk metrics to load
        await page.waitForSelector('[data-testid="risk-metrics-panel"]');

        // Verify metrics are displayed
        const metricsPanel = await page.textContent('[data-testid="risk-metrics-panel"]');
        expect(metricsPanel).toContain('Current Risk');
        expect(metricsPanel).toContain('Exposure');
        expect(metricsPanel).toContain('Margin Usage');
    });

    test('should enforce risk limits on order placement', async ({ page }) => {
        // Navigate to order entry
        await page.click('[data-testid="order-entry-tab"]');

        // Wait for order form
        await page.waitForSelector('[data-testid="order-entry-form"]');

        // Try to place order exceeding risk limits
        await page.fill('[data-testid="symbol-input"]', 'BTC-USD');
        await page.fill('[data-testid="quantity-input"]', '100'); // Large position
        await page.click('[data-testid="submit-order-button"]');

        // Check risk validation message
        const riskWarning = await page.waitForSelector('[data-testid="risk-warning-message"]');
        expect(await riskWarning.textContent()).toContain('Exceeds risk limits');

        // Verify risk metrics update
        const riskMetrics = await page.textContent('[data-testid="risk-metrics-panel"]');
        expect(riskMetrics).toContain('Potential Risk:');
    });

    test('should track daily loss limit', async ({ page }) => {
        // Check initial daily loss display
        const initialLoss = await page.textContent('[data-testid="daily-loss-display"]');
        expect(initialLoss).toBeDefined();

        // Place losing trade
        await page.click('[data-testid="order-entry-tab"]');
        await page.fill('[data-testid="symbol-input"]', 'BTC-USD');
        await page.fill('[data-testid="quantity-input"]', '1');
        await page.click('[data-testid="submit-order-button"]');

        // Verify daily loss updates
        await page.waitForSelector('[data-testid="daily-loss-display"]');
        const updatedLoss = await page.textContent('[data-testid="daily-loss-display"]');
        expect(updatedLoss).not.toEqual(initialLoss);
    });
}); 