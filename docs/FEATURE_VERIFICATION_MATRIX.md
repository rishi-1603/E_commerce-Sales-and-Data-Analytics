# Feature verification matrix

2026-10-30. PASS applies to the stated workflow, not every combination of inputs. Fresh production screenshots are genuine browser captures.

| Feature | Check | Status / boundary |
|---|---|---|
| Nine dashboard pages | Clicked each navigation destination; active page changed | PASS in browser |
| Pricing sliders | Changed volume-lift input to 80%; verdict changed to clears break-even | PASS |
| Win-back budget | Set budget to zero; worklist output changed | PASS |
| API read-only concurrency | 50 requests, concurrency 5, isolated SQLite | PASS for bounded local check; no production capacity claim |
| API writes/tests | Temporary test DB before engine import; original developer DB hash unchanged | PASS |
| SQL/AI guardrails | 37-case fallback benchmark and AST mutation/table/limit checks | PASS within authored scope |

## Accessibility
axe scans use WCAG2A/AA and WCAG2.1AA tags. Measured patch verification has zero detected violations at 1440×900 and 390×844, with 1 incomplete rule groups still requiring manual review. Live post-push scans also reported zero detected violations in the tested desktop/mobile states; incomplete rules remain manual-review items.
Keyboard focus smoke checks are not a screen-reader walkthrough. Not all chart semantics, every hidden state or assistive-technology behavior is certified.

## Performance
Warm browser rendering was observed; fixed waits used for UI screenshots are not latency measurements. A local API test used 50 read-only requests at concurrency 5: 0 errors, median 54.295 ms, p95 103.5 ms in this sandbox. This does not establish Streamlit session capacity, production cold-start bounds or real-user service levels.

## Not tested exhaustively
Every filter permutation, provider outage/rate-limit scenario and arbitrary question; unrestricted LLM narration; sustained production stress and real screen-reader behavior.
