const { test, expect } = require('@playwright/test');

test('debug all features', async ({ page }) => {
  const consoleLogs = [];
  page.on('console', msg => consoleLogs.push({ type: msg.type(), text: msg.text() }));
  page.on('pageerror', err => consoleLogs.push({ type: 'error', text: err.message }));

  await page.goto('/');

  // Demo login
  await page.getByRole('button', { name: /Demo: Danny Israely/ }).click();
  await expect(page.locator('#authHeader')).toContainText('Danny Israely', { timeout: 10000 });

  // Load lectures
  await page.getByRole('button', { name: 'הצג את כל ההרצאות בטווח' }).click();
  await expect(page.locator('#lectureList')).toBeVisible({ timeout: 15000 });

  // Click first lecture to load content
  await page.locator('#lectureList button').first().click();
  await page.waitForTimeout(2000);

  // Click סימולציה on first lecture
  console.log('CLICKING SIMULATION');
  await page.locator('button:has-text("סימולציה")').first().click();
  await expect(page.locator('#vizResult iframe')).toBeVisible({ timeout: 60000 });
  await page.waitForTimeout(5000);

  // Check iframe content
  const vizText = await page.evaluate(() => {
    const iframe = document.querySelector('#vizResult iframe');
    if (!iframe) return 'NO IFRAME';
    const doc = iframe.contentDocument || iframe.contentWindow.document;
    return doc.body.innerText.substring(0, 200);
  });
  console.log('VIZ TEXT:', vizText);

  // Click בוחן on first lecture
  console.log('CLICKING TEST');
  await page.locator('button:has-text("בוחן")').first().click();
  await page.waitForTimeout(10000);

  // Check tester chat box
  const testerHTML = await page.evaluate(() => {
    return document.getElementById('testerChatBox')?.innerHTML?.substring(0, 500) || 'NO CHATBOX';
  });
  console.log('TESTER HTML:', testerHTML);

  // Print all console logs
  console.log('ALL CONSOLE LOGS:', JSON.stringify(consoleLogs, null, 2));
});
