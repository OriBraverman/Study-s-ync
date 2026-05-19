const { test, expect } = require('@playwright/test');

test('check console for errors', async ({ page }) => {
  const logs = [];
  page.on('console', msg => logs.push(`${msg.type()}: ${msg.text()}`));
  page.on('pageerror', err => logs.push(`PAGEERROR: ${err.message}`));

  await page.goto('/');
  
  // Click demo
  await page.getByRole('button', { name: /Demo: Danny Israely/ }).click();
  await expect(page.locator('#authHeader')).toContainText('Danny Israely', { timeout: 10000 });

  // Load lectures
  await page.getByRole('button', { name: 'הצג את כל ההרצאות בטווח' }).click();
  await expect(page.locator('#lectureList')).toBeVisible({ timeout: 15000 });

  // Click simulation
  await page.locator('button:has-text("סימולציה")').first().click();
  await page.waitForTimeout(10000);

  // Check if viz iframe has content
  const vizHasContent = await page.evaluate(() => {
    const iframe = document.querySelector('#vizResult iframe');
    if (!iframe) return 'NO IFRAME';
    const doc = iframe.contentDocument || iframe.contentWindow.document;
    return doc.body.innerText.length > 0 ? 'HAS CONTENT' : 'EMPTY';
  });
  console.log('VIZ STATUS:', vizHasContent);

  // Click test
  await page.locator('button:has-text("בוחן")').first().click();
  await page.waitForTimeout(5000);

  // Check tester chat
  const testerHasContent = await page.evaluate(() => {
    const chatBox = document.getElementById('testerChatBox');
    return chatBox ? chatBox.innerText.length > 0 : 'NO CHATBOX';
  });
  console.log('TESTER STATUS:', testerHasContent);

  console.log('ALL LOGS:');
  logs.forEach(l => console.log(l));
});
