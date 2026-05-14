const { test, expect } = require('@playwright/test');

test('demo visualizer flow works', async ({ page }) => {
  await page.goto('/');

  // Click the Demo: Danny Israely button
  const demoButton = page.getByRole('button', { name: /Demo: Danny Israely/ });
  await expect(demoButton).toBeVisible();
  await demoButton.click();

  // Wait for the header to show Danny Israely (demo login succeeded)
  await expect(page.locator('#authHeader')).toContainText('Danny Israely', { timeout: 10000 });

  // Click the "Show all lectures in range" button
  const loadButton = page.getByRole('button', { name: 'הצג את כל ההרצאות בטווח' });
  await expect(loadButton).toBeVisible();
  await loadButton.click();

  // Wait for the lecture list to appear
  const lectureList = page.locator('#lectureList');
  await expect(lectureList).toBeVisible({ timeout: 15000 });

  // The demo date range (20/10 - 05/11) should show missed lectures
  // Wait for at least one "סימולציה" button to appear
  const vizButton = page.locator('button:has-text("סימולציה")').first();
  await expect(vizButton).toBeVisible({ timeout: 15000 });

  // Click the first visualizer button
  await vizButton.click();

  // Wait for the visualizer iframe to render inside #vizResult
  const vizIframe = page.locator('#vizResult iframe');
  await expect(vizIframe).toBeVisible({ timeout: 30000 });

  // Verify the iframe rendered actual interactive content (any topic-specific visualizer)
  const iframeBody = vizIframe.contentFrame().locator('body');
  await expect(iframeBody).not.toContainText('No preview available', { timeout: 15000 });
  await expect(iframeBody).not.toContainText('שגיאה', { timeout: 15000 });
  // Babel standalone compiles asynchronously; give it a few seconds
  await page.waitForTimeout(5000);
  // Expect some rendered DOM (buttons, inputs, or headings) inside the iframe
  const hasInteractiveElements = await vizIframe.evaluate(iframe => {
    const doc = iframe.contentDocument || iframe.contentWindow.document;
    return doc.querySelectorAll('button, input, h1, h2, h3, div[style]').length > 0;
  });
  expect(hasInteractiveElements).toBe(true);
});
