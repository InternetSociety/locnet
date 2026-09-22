import { expect, test } from '@playwright/test';

import { signIn } from './fixtures';


test('keeps the application public and rejects invalid credentials at the unlinked login', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole('link', { name: 'API', exact: true })).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Admin Panel' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: /Sign out/ })).toHaveCount(0);
  const navigationBox = await page.getByRole('navigation').boundingBox();
  const introduction = page
    .getByText('The Community Network Builder is an application', { exact: false })
    .first();
  await expect(introduction).toBeVisible();
  const introductionBox = await introduction.boundingBox();
  if (!navigationBox || !introductionBox) {
    throw new Error('Expected the navigation and introduction to have layout boxes');
  }
  expect(introductionBox.y - (navigationBox.y + navigationBox.height)).toBeGreaterThanOrEqual(16);

  await page.goto('/login');
  await page.getByLabel('Email').fill('user-e2e@example.com');
  await page.getByLabel('Password').fill('incorrect-password');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('alert')).toContainText(
    'Invalid email, password, or account status',
  );
});


test('signs in, opens protected API documentation, and signs out', async ({
  page,
}) => {
  await signIn(page);
  await expect(page.getByRole('link', { name: 'API', exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Admin Panel' })).toHaveCount(0);
  const signOut = page.getByRole('button', { name: /Sign out/ });
  await expect(signOut).toHaveCSS('border-style', 'solid');
  await expect(signOut).toHaveCSS('background-color', 'rgb(255, 255, 255)');
  await page.goto('/docs');
  await expect(page).toHaveTitle(/Community Network Builder API/);

  await page.goto('/');
  await page.getByRole('button', { name: /Sign out/ }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole('button', { name: /Sign out/ })).toHaveCount(0);
});


test('administrator can create a user and enable API access', async ({ page }) => {
  await signIn(
    page,
    process.env.E2E_ADMIN_EMAIL ?? 'admin-e2e@example.com',
    process.env.E2E_ADMIN_PASSWORD ?? 'admin-password',
  );
  await expect(page.getByRole('link', { name: 'Admin Panel' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'API', exact: true })).toHaveCount(0);
  await page.goto('/docs');
  await expect(page).toHaveTitle(/Community Network Builder API/);
  await page.goto('/manage-users');

  const email = `playwright-${Date.now()}@example.com`;
  await page.getByLabel('Email').last().fill(email);
  await page.getByLabel('Password').last().fill('playwright-password');
  await page.getByRole('button', { name: 'Create user' }).click();
  await expect(page).toHaveURL(/\/manage-users$/);

  const row = page.getByRole('row').filter({ hasText: email });
  await row.getByRole('button', { name: 'Enable API' }).click();
  await expect(page.getByRole('heading', { name: `API token for ${email}` })).toBeVisible();
  await expect(page.getByLabel('API token')).not.toHaveValue('');
});
