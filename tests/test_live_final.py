"""
Playwright tests for live Vercel deployment - quick verification.
"""
import asyncio
import subprocess
import sys
from playwright.async_api import async_playwright

VERCEL_URL = "https://ecom-zeta-one.vercel.app/"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        errors = []
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))
        
        print(f"Loading live Vercel deployment: {VERCEL_URL}")
        try:
            await page.goto(VERCEL_URL, wait_until="networkidle", timeout=60000)
            print("✓ Live site loaded")
        except Exception as e:
            print(f"✗ Failed to load: {e}")
            await browser.close()
            return
        
        await page.wait_for_timeout(3000)
        
        # Check for KPI cards
        print("\n=== Checking KPI Cards ===")
        kpi_cards = await page.query_selector_all('.kpi-card')
        print(f"  Found {len(kpi_cards)} KPI cards")
        
        # Check specific KPI values are present
        kpi_checks = [
            ("₹5.93 Cr", "Revenue"),
            ("₹3.20 Cr", "Profit"),
            ("54.0%", "Margin"),
            ("9,933", "Orders"),
            ("1,991", "Customers"),
            ("5,968", "AOV"),
            ("9,312", "Delivered"),
            ("1,223", "Returned"),
            ("844", "Cancelled"),
            ("621", "Processing"),
            ("441", "Cooling-off"),
            ("₹1.30 Cr", "Win-back spend"),
            ("₹523", "EV/contact"),
            ("12.5%", "Break-even"),
            ("23.5%", "Churn rate"),
        ]
        
        page_content = await page.content()
        for value, label in kpi_checks:
            if value in page_content:
                print(f"  ✓ {label}: {value}")
            else:
                print(f"  ✗ {label}: {value} NOT FOUND")
        
        # Check for charts
        print("\n=== Checking Charts ===")
        chart_ids = [
            'ch_revtrend', 'ch_catrev', 'ch_status', 'ch_rfm_ovr',
            'ch_catcomp', 'ch_region', 'ch_rfm', 'ch_cohort',
            'ch_churnpie', 'ch_models', 'ch_bcg', 'ch_margin',
            'ch_forecast', 'ch_pricing_margin', 'ch_winback_sens'
        ]
        
        for cid in chart_ids:
            try:
                canvas = await page.query_selector(f'canvas#{cid}')
                if canvas:
                    is_visible = await canvas.is_visible()
                    if is_visible:
                        print(f"  ✓ Chart {cid}")
                    else:
                        print(f"  ⚠ Chart {cid} exists but not visible")
                else:
                    print(f"  ✗ Chart {cid} NOT FOUND")
            except Exception as e:
                print(f"  ✗ Chart {cid} error: {e}")
        
        # Navigation test
        print("\n=== Navigation Tests ===")
        nav_items = [
            ('overview', 'Overview'),
            ('sales', 'Sales Performance'),
            ('customers', 'Customer RFM'),
            ('cohorts', 'Retention & Cohorts'),
            ('churn', 'Churn Analysis'),
            ('products', 'Product Profitability'),
            ('forecast', 'Revenue Forecast'),
            ('quality', 'Data Quality'),
            ('insights', 'Business Insights'),
            ('ai', 'AI Analyst'),
            ('pricing', 'Pricing Lab'),
            ('winback', 'Win-Back Economics'),
        ]
        
        for nav_id, name in nav_items:
            try:
                await page.click(f'div.nav-item[onclick*="{nav_id}"]')
                await page.wait_for_timeout(500)
                page_el = await page.query_selector(f'.page[id*="{nav_id}"]')
                if page_el and await page_el.is_visible():
                    print(f"  ✓ Navigation to {name}")
                else:
                    print(f"  ✗ Navigation to {name} - page not visible")
            except Exception as e:
                print(f"  ✗ Navigation to {name} failed: {e}")
        
        # Console errors
        print(f"\nConsole errors: {len(console_errors)}")
        for err in console_errors:
            print(f"  ✗ {err}")
        
        await context.close()
        await browser.close()
        
        print(f"\n{'='*50}")
        if len(console_errors) == 0:
            print("✅ NO CONSOLE ERRORS")
        else:
            print(f"❌ {len(console_errors)} CONSOLE ERRORS")

if __name__ == "__main__":
    asyncio.run(main())