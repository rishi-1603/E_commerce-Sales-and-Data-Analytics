const { chromium } = require('playwright');
const fs = require('fs');

async function captureScreenshots() {
  if (!fs.existsSync('docs/screenshots')) {
    fs.mkdirSync('docs/screenshots', { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto('https://ecomanalytics-dashboard.vercel.app/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  await page.screenshot({ path: 'docs/screenshots/web_overview.png', fullPage: false });
  console.log('Captured web_overview.png');

  const pages = [
    { name: 'web_sales', click: "[onclick*=\"nav('sales'\"]", waitFor: '#page-sales' },
    { name: 'web_customers', click: "[onclick*=\"nav('customers'\"]", waitFor: '#page-customers' },
    { name: 'web_cohorts', click: "[onclick*=\"nav('cohorts'\"]", waitFor: '#page-cohorts' },
    { name: 'web_churn', click: "[onclick*=\"nav('churn'\"]", waitFor: '#page-churn' },
    { name: 'web_products', click: "[onclick*=\"nav('products'\"]", waitFor: '#page-products' },
    { name: 'web_forecast', click: "[onclick*=\"nav('forecast'\"]", waitFor: '#page-forecast' },
    { name: 'web_quality', click: "[onclick*=\"nav('quality'\"]", waitFor: '#page-quality' },
    { name: 'web_insights', click: "[onclick*=\"nav('insights'\"]", waitFor: '#page-insights' },
    { name: 'web_ai', click: "[onclick*=\"nav('ai'\"]", waitFor: '#page-ai' },
    { name: 'web_pricing', click: "[onclick*=\"nav('pricing'\"]", waitFor: '#page-pricing' },
    { name: 'web_winback', click: "[onclick*=\"nav('winback'\"]", waitFor: '#page-winback' },
  ];

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('https://ecomanalytics-dashboard.vercel.app/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  for (const p of pages) {
    try {
      await page.click(p.click, { timeout: 5000 });
      await page.waitForSelector(p.waitFor, { timeout: 5000 });
      await page.waitForTimeout(2000);
      await page.screenshot({ path: `docs/screenshots/web_${p.name}.png`, fullPage: false });
      console.log(`Captured ${p.name}.png`);
    } catch (err) {
      console.error(`Failed ${p.name}: ${err.message}`);
    }
  }

  await browser.close();
  console.log('All screenshots captured!');
}

captureScreenshots().catch(console.error);