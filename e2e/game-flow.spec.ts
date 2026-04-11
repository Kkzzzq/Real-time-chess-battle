<<<<<<< HEAD
import { expect, test } from '@playwright/test'

test('invalid game path should redirect or show error boundary', async ({ page }) => {
  await page.goto('/game/invalid-match-id')
  await expect(page.locator('body')).toContainText(/(lobby|会话|match|not found|错误)/i)
})
=======
// Placeholder Playwright spec scaffold.
// TODO: move -> unlock -> resign flow.
export {}
>>>>>>> origin/main
