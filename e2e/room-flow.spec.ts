import { expect, test } from '@playwright/test'

test('lobby should render create/join controls', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('body')).toContainText(/(lobby|room|match|player)/i)
  await expect(page.getByRole('button').first()).toBeVisible()
  await expect(page.getByRole('textbox').first()).toBeVisible()
})
