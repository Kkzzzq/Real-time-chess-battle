<<<<<<< HEAD
import { expect, test } from '@playwright/test'

test('room route without session should fallback', async ({ page }) => {
  await page.goto('/room/invalid-match-id')
  await expect(page.locator('body')).toContainText(/(lobby|会话|reconnect|match|error)/i)
})
=======
// Placeholder Playwright spec scaffold.
// TODO: reconnect recovery flow.
export {}
>>>>>>> origin/main
