"""
Playwright tests for live Vercel deployment - cross-browser, responsive, full UI verification.
"""
import asyncio
import subprocess
import sys
from playwright.async_api import async_playwright

VERCEL_URL = "https://ecomanalytics-dashboard.vercel.app/"


async def main():
    async with async_playwright() as p:
        results = {
            "chromium": {"passed": 0, "failed": 0, "errors": []},
            "firefox": {"passed": 0, "failed": 0, "errors": []},
            "webkit": {"passed": 0, "failed": 0, "errors": []},
        }
        
        for browser_name in ["chromium", "firefox", "webkit"]:
            print(f"\n{'='*60}")
            print(f"TESTING {browser_name.upper()}")
            print(f"{'='*60}")
            
            browser = await getattr(p, browser_name).launch(headless=True)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()
            
            errors = []
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda exc: console_errors.append(str(exc)))
            
            print(f"Loading {VERCEL_URL}...")
            try:
                await page.goto(VERCEL_URL, wait_until="networkidle", timeout=60000)
                print(f"✓ {browser_name}: Live site loaded")
                results[browser_name]["passed"] += 1
            except Exception as e:
                print(f"✗ {browser_name}: Failed to load - {e}")
                results[browser_name]["failed"] += 1
                results[browser_name]["errors"].append(f"Load failed: {e}")
                await browser.close()
                continue
            
            await page.wait_for_timeout(3000)
            
            # Check KPI cards
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
                    results[browser_name]["passed"] += 1
                else:
                    print(f"  ✗ {label}: {value} NOT FOUND")
                    results[browser_name]["failed"] += 1
                    errors.append(f"Missing {label}: {value}")
            
            # Check charts
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
                            results[browser_name]["passed"] += 1
                        else:
                            print(f"  ⚠ Chart {cid} exists but not visible")
                    else:
                        print(f"  ✗ Chart {cid} NOT FOUND")
                        results[browser_name]["failed"] += 1
                        errors.append(f"Chart {cid} not found")
                except Exception as e:
                    results[browser_name]["failed"] += 1
                    errors.append(f"Chart {cid} error: {e}")
            
            # Navigation test
            nav_items = [
                ('overview', 'Overview'), ('sales', 'Sales Performance'),
                ('customers', 'Customer RFM'), ('cohorts', 'Retention & Cohorts'),
                ('churn', 'Churn Analysis'), ('products', 'Product Profitability'),
                ('forecast', 'Revenue Forecast'), ('quality', 'Data Quality'),
                ('insights', 'Business Insights'), ('ai', 'AI Analyst'),
                ('pricing', 'Pricing Lab'), ('winback', 'Win-Back Economics'),
            ]
            
            for nav_id, name in nav_items:
                try:
                    await page.click(f'div.nav-item[onclick*="{nav_id}"]')
                    await page.wait_for_timeout(500)
                    page_el = await page.query_selector(f'.page[id*="{nav_id}"]')
                    if page_el and await page_el.is_visible():
                        print(f"  ✓ Navigation to {name}")
                        results[browser_name]["passed"] += 1
                    else:
                        results[browser_name]["failed"] += 1
                        errors.append(f"Navigation to {name} - page not visible")
                except Exception as e:
                    results[browser_name]["failed"] += 1
                    errors.append(f"Navigation to {name} failed: {e}")
            
            # Console errors
            print(f"Console errors: {len(console_errors)}")
            for err in console_errors:
                print(f"  ✗ {err}")
                results[browser_name]["failed"] += 1
                results[browser_name]["errors"].append(f"Console: {err}")
            
            await context.close()
            await browser.close()
        
        # ============================================================
        # RESPONSIVE TESTING (Chromium only)
        # ============================================================
        print(f"\n{'='*60}")
        print("RESPONSIVE TESTING (Chromium)")
        print(f"{'='*60}")
        
        browser = await p.chromium.launch(headless=True)
        viewports = [
            {"width": 390, "height": 844, "name": "Mobile"},
            {"width": 768, "height": 1024, "name": "Tablet"},
            {"width": 1366, "height": 768, "name": "Laptop"},
            {"width": 1920, "height": 1080, "name": "Desktop"},
        ]
        
        for vp in viewports:
            context = await browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            page = await context.new_page()
            
            try:
                await page.goto(VERCEL_URL, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(2000)
                
                # Check for horizontal overflow
                overflow = await page.evaluate("document.body.scrollWidth > document.body.clientWidth")
                if overflow:
                    print(f"  ⚠ {vp['name']} ({vp['width']}x{vp['height']}): Horizontal overflow")
                else:
                    print(f"  ✓ {vp['name']} ({vp['width']}x{vp['height']}): No overflow")
                
                # Check sidebar
                sidebar = await page.query_selector(".sidebar")
                if sidebar:
                    is_visible = await sidebar.is_visible()
                    if is_visible:
                        print(f"  ✓ Sidebar visible at {vp['name']}")
                    else:
                        print(f"  ⚠ Sidebar hidden at {vp['name']} (expected for mobile)")
                else:
                    print(f"  ✗ Sidebar not found at {vp['name']}")
                    
            except Exception as e:
                print(f"  ✗ {vp['name']} error: {e}")
            
            await context.close()
        
        await browser.close()
        
        # ============================================================
        # SUMMARY
        # ============================================================
        print("\n" + "="*70)
        print("VERCEL LIVE DEPLOYMENT - CROSS-BROWSER & RESPONSIVE TEST SUMMARY")
        print("="*70)
        
        total_passed = sum(r["passed"] for r in results.values())
        total_failed = sum(r["failed"] for r in results.values())
        
        for browser_name, r in results.items():
            print(f"\n{browser_name.upper()}:")
            print(f"  Passed: {r['passed']}")
            print(f"  Failed: {r['failed']}")
            for err in r["errors"]:
                print(f"  - {err}")
        
        print(f"\nOVERALL: {total_passed} passed, {total_failed} failed")
        
        if total_failed == 0:
            print("\n✅ LIVE VERCEL DEPLOYMENT FULLY VERIFIED ACROSS ALL BROWSERS")
        else:
            print(f"\n⚠️  {total_failed} ISSUES FOUND - SEE ABOVE")

if __name__ == "__main__":
    asyncio.run(main())