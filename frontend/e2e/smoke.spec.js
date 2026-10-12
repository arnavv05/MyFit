import { test, expect } from '@playwright/test';

// Why: Smoke tests verify core UI renders and hash routing functions end-to-end without deep mocking.
test.describe('Frontend Smoke Tests', () => {
  test('landing page loads and renders brand title', async ({ page }) => {
    await page.goto('/#/login');
    await expect(page).toHaveTitle(/Myfitness/i);
    await expect(page.locator('h1, h2, form').first()).toBeVisible();
  });

  test('login screen displays email and password inputs', async ({ page }) => {
    await page.goto('/#/login');
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
  });
});
