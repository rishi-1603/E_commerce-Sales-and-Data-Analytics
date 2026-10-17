"""
inject_pricing_dashboard.py — generate the Pricing Lab + Win-Back pages
==============================================================================
WHY THIS EXISTS: the dashboard's numbers must come from the pipeline, never
from hand-typing (see tests/test_dashboard_consistency.py). This script reads
the two pricing artifacts and injects two new pages into the Chart.js
dashboard:

    Pricing Lab        — discount cost, margin erosion, break-even, and an
                         interactive discount simulator
    Win-Back Economics — campaign EV, sensitivity, tiered scenarios and a
                         budget-constrained worklist

The script is IDEMPOTENT: it strips any previous injection (between the
PRICING markers) and rewrites it, then syncs all three deployment copies.
Re-run it whenever reports/discount_analysis.json or
reports/winback_economics.json changes.

Inputs:
    reports/discount_analysis.json
    reports/winback_economics.json
Outputs (all identical):
    dashboard/dashboard.html
    dashboard/index.html
    index.html

Run:  python scripts/inject_pricing_dashboard.py
"""
import json
import os
import re
import shutil
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pricing_dashboard_templates import (  # noqa: E402
    DATA_END,
    DATA_START,
    JS,
    JS_END,
    JS_START,
    NAV,
    NAV_END,
    NAV_START,
    PAGE_END,
    PAGE_START,
    PAGES,
)

REPORTS = os.path.join(BASE, "reports")
# All deployment copies must stay byte-identical — the consistency test checks
# dashboard/dashboard.html, dashboard/index.html and the repo-root dashboard.html;
# index.html at the root is the fourth served copy.
COPIES = [
    os.path.join(BASE, "dashboard", "dashboard.html"),
    os.path.join(BASE, "dashboard", "index.html"),
    os.path.join(BASE, "dashboard.html"),
    os.path.join(BASE, "index.html"),
]


def strip_between(text: str, start: str, end: str) -> str:
    """Remove every occurrence of start..end (inclusive) plus one trailing newline."""
    while start in text:
        i = text.index(start)
        j = text.index(end, i) + len(end)
        if j < len(text) and text[j] == "\n":
            j += 1
        text = text[:i] + text[j:]
    return text


def strip_pricing_key(text: str) -> str:
    """Remove a previously injected `pricing: {...},` entry from the DATA object.

    Brace-matched (and string-aware) rather than comment-delimited, because a
    JS comment inside the DATA object breaks the repo's JS-to-JSON parser used
    by tests/test_dashboard_consistency.py.
    """
    while True:
        marker = "\n  pricing: "
        if marker not in text:
            return text
        i = text.index(marker)
        j = text.index("{", i)
        depth = 0
        in_str = False
        esc = False
        k = j
        while k < len(text):
            ch = text[k]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        break
            k += 1
        end = k + 1
        if end < len(text) and text[end] == ",":
            end += 1
        text = text[:i] + text[end:]


def validate_data_parses(html: str) -> None:
    """Fail loudly if the repo's own JS-to-JSON parser could not read DATA.

    tests/test_dashboard_consistency.py converts DATA with:
        - a regex that quotes unquoted keys: ([{,]\s*)([A-Za-z_]...)...
        - a global apostrophe -> double-quote replacement
        - trailing-comma removal
    Both of those transforms can corrupt innocent *string values* (an apostrophe,
    or a ", word: " sequence). This check runs the same algorithm before writing,
    so the injector can never ship a dashboard the test suite cannot parse.
    """
    import re as _re
    m = _re.search(r"const DATA = (\{.*?\});\s*\n\s*const C", html, _re.S)
    if not m:
        raise ValueError("DATA object not found after injection")
    raw = m.group(1)
    raw = _re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_ ]*?)\s*:", r'\1"\2":', raw)
    raw = raw.replace("'", '"')
    raw = _re.sub(r",\s*([\]}])", r"\1", raw)
    try:
        json.loads(raw)
    except json.JSONDecodeError as e:
        bad = raw.split("\n")[e.lineno - 1] if e.lineno <= len(raw.split("\n")) else ""
        raise ValueError(
            "Injected DATA would not parse under the repo's own parser "
            f"({e.msg} at line {e.lineno}, col {e.colno}).\n"
            f"Offending line: {bad[:300]}\n"
            "Likely cause: a string value containing an apostrophe, or a "
            "\", word: \" sequence, which the parser rewrites."
        ) from e


def fmt_inr(x: float) -> str:
    """Indian-format rupees with lakh/crore for large values."""
    if abs(x) >= 1e7:
        return f"₹{x / 1e7:.2f} Cr"
    if abs(x) >= 1e5:
        return f"₹{x / 1e5:.2f} L"
    return f"₹{x:,.0f}"


def build_data_block(d: dict, w: dict) -> str:
    """The JS object injected into `const DATA = { ... }`."""
    rrs = w["parameters"]["recovery_rate"]
    payload = {
        "discount": {
            "depths": [r["discount"] for r in d["margin_curve"]],
            "margin_pct_of_list": [r["margin_pct_of_list"] for r in d["margin_curve"]],
            "margin_rate": [r["margin_rate"] for r in d["margin_curve"]],
            "break_even_lift": [r["break_even_volume_lift"] for r in d["break_even"]],
            "share_of_items": [r["share_of_items"] for r in d["break_even"]],
            "volume_response_detected": d["headline"]["volume_response_detected"],
            "kruskal_p": d["discount_response"]["kruskal_wallis_p"],
            "break_even_at_20": d["headline"]["break_even_lift_at_20pct"],
            "margin_recovered_cap10": d["headline"]["margin_recovered_by_10pct_cap"],
        },
        "winback": {
            "customers": w["pool"]["customers"],
            "historical_spend": w["pool"]["historical_spend_inr"],
            "mean_churn_p": w["pool"]["mean_churn_probability"],
            "ev_per_contact": w["baseline_campaign"]["expected_profit_per_contact"],
            "ev_total": w["baseline_campaign"]["expected_profit_total"],
            "break_even_p": w["break_even"]["break_even_churn_probability"],
            "bayes_threshold": w["bayes_threshold_cross_check"]["churn_model_bayes_threshold"],
            "consistent": w["bayes_threshold_cross_check"]["consistent"],
            "contact_cost": w["parameters"]["contact_cost_inr"],
            "recovery_rate": rrs,
            "retained_value": w["parameters"]["retained_value_inr"],
            "sensitivity": [
                {"r": s["recovery_rate"], "c": s["contact_cost"],
                 "profit": s["profit_per_contact"]}
                for s in w["sensitivity"]
            ],
            "tiers": [
                {"name": t["scenario"][:1], "label": t["scenario"],
                 "audience": t.get("audience", 0),
                 "profit": t.get("expected_profit_total", 0)}
                for t in w["tiered_scenarios"]
            ],
            "worklist": w["budget_worklist"],
        },
    }
    return "\n  pricing: " + json.dumps(payload, separators=(",", ":")) + ","


def build_pages(d: dict, w: dict) -> str:
    cap10 = d["repricing_scenarios"]["cap_10"]
    mapping = {
        "__P_KW__": d["discount_response"]["kruskal_wallis_p"],
        "__P_VOL__": "NO" if not d["headline"]["volume_response_detected"] else "YES",
        "__P_BE20__": round(d["headline"]["break_even_lift_at_20pct"] * 100, 1),
        "__P_MREC__": fmt_inr(cap10["margin_recovered"]),
        "__P_MPCT__": round(cap10["margin_recovered_pct_of_total"] * 100, 1),
        "__P_LINES__": f"{cap10['lines_affected']:,}",
        "__W_CUST__": w["pool"]["customers"],
        "__W_HIST__": fmt_inr(w["pool"]["historical_spend_inr"]),
        "__W_EVPC__": fmt_inr(w["baseline_campaign"]["expected_profit_per_contact"]),
        "__W_EVTOT__": fmt_inr(w["baseline_campaign"]["expected_profit_total"]),
        "__W_RATE__": round(w["parameters"]["recovery_rate"] * 100),
        "__W_BEP__": round(w["break_even"]["break_even_churn_probability"] * 100, 1),
    }
    out = PAGES
    for k, v in mapping.items():
        out = out.replace(k, str(v))
    return out


def inject(path: str, data_block: str, pages: str) -> None:
    with open(path, encoding="utf-8") as f:
        html = f.read()

    # 1. strip any previous injection (idempotent)
    html = strip_between(html, NAV_START, NAV_END)
    html = strip_between(html, PAGE_START, PAGE_END)
    html = strip_pricing_key(html)
    html = strip_between(html, JS_START, JS_END)

    # 2. nav — before the Skills group
    nav_anchor = '    <div class="nav-item" style="cursor:default;opacity:0.7"><span style="font-size:11px">🐍 Python'
    assert nav_anchor in html, "nav anchor not found"
    html = html.replace(nav_anchor, NAV + "\n" + nav_anchor, 1)

    # 3. pages — before the script block
    page_anchor = "<script>\nconst GRD"
    assert page_anchor in html, "page anchor not found"
    # Normalise the whitespace immediately before the anchor, then insert.
    # This is what makes repeated runs byte-identical: strip_between removes the
    # block but leaves its trailing newlines behind, and without this the file
    # would grow one blank line per run.
    html = re.sub(r"\n*" + re.escape(page_anchor),
                  "\n\n" + page_anchor.replace("\\", "\\\\"), html, count=1)
    html = html.replace(page_anchor, pages + "\n\n" + page_anchor, 1)

    # 4. DATA — inject the pricing key before DATA closes
    head, tail = html.split("\nconst C = {", 1)
    idx = head.rfind("\n};")
    assert idx > 0, "DATA closing brace not found"
    head = head[:idx + 1] + data_block + head[idx + 1:]
    html = head + "\nconst C = {" + tail

    # 5. titles (idempotent: remove a previously injected pricing title first)
    pricing_title = 'pricing:["Pricing Lab & Win-Back","Discount Cost · Break-Even · Campaign Economics"]'
    while pricing_title in html:
        i = html.index(pricing_title)
        # swallow the preceding ",\n  " that was added with it
        start = i
        if html[max(0, start - 4):start] == ',\n  ':
            start -= 4
        end = i + len(pricing_title)
        html = html[:start] + html[end:]

    old_title = 'forecast:["Revenue Forecast","Holt-Winters + Linear Ensemble · Jan–Jun 2025"]'
    assert old_title in html, "titles anchor not found"
    html = html.replace(
        old_title,
        old_title + ',\n  pricing:["Pricing Lab & Win-Back","Discount Cost · Break-Even · Campaign Economics"]',
        1)

    # 6. init hook (idempotent: drop a previous call line first)
    html = html.replace("  renderSegActions();\n  buildPricing();\n});",
                        "  renderSegActions();\n});")
    init_anchor = "  renderSegActions();\n});"
    assert init_anchor in html, "init anchor not found"
    html = html.replace(init_anchor, "  renderSegActions();\n  buildPricing();\n});", 1)

    # 7. renderer functions before the closing script tag
    idx = html.rfind("</script>")
    html = html[:idx] + JS + "\n" + html[idx:]

    validate_data_parses(html)   # never write a dashboard the tests cannot parse

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def main() -> None:
    with open(os.path.join(REPORTS, "discount_analysis.json")) as f:
        d = json.load(f)
    with open(os.path.join(REPORTS, "winback_economics.json")) as f:
        w = json.load(f)

    data_block = build_data_block(d, w)
    pages = build_pages(d, w)

    inject(COPIES[0], data_block, pages)
    print(f"injected {os.path.relpath(COPIES[0], BASE)}")

    for c in COPIES[1:]:
        shutil.copyfile(COPIES[0], c)
    print(f"synced all {len(COPIES)} deployment copies")

    print(f"\nPricing Lab: break-even @20% = "
          f"+{d['headline']['break_even_lift_at_20pct']:.1%}, margin recoverable "
          f"(10% cap) = ₹{d['headline']['margin_recovered_by_10pct_cap']:,.0f}")
    print(f"Win-Back: EV per contact = "
          f"₹{w['baseline_campaign']['expected_profit_per_contact']:,.0f}, campaign total = "
          f"₹{w['baseline_campaign']['expected_profit_total']:,.0f}, break-even p = "
          f"{w['break_even']['break_even_churn_probability']:.2%}")


if __name__ == "__main__":
    main()
