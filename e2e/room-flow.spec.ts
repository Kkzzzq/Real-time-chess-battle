<<<<<<< HEAD
import { expect, test } from '@playwright/test'

test('lobby should render create/join controls', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /lobby/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /create/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /join/i })).toBeVisible()
})
=======
// Placeholder Playwright spec scaffold.
// TODO: create -> join -> ready -> start flow.
export {}
>>>>>>> origin/main
