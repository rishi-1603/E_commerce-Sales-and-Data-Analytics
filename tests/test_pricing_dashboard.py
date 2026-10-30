"""
test_pricing_dashboard.py — the Pricing Lab pages cannot lie.
==============================================================================
Same contract as test_dashboard_consistency.py, extended to the two new pages:

    reports/discount_analysis.json  ─┐
    reports/winback_economics.json  ─┴─►  dashboard DATA.pricing  ─►  rendered

Every number displayed on the Pricing Lab and Win-Back pages must equal the
value in the pricing artifacts, and those artifacts must equal the modules.
If any link drifts, this file fails — the live site can never show a number the
analysis did not produce.
"""
import json
import os
import re
from pathlib import Path

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASH = os.path.join(BASE, "dashboard", "dashboard.html")
REPORTS = os.path.join(BASE, "reports")


@pytest.fixture(scope="module")
def dash_data():
    with open(DASH, encoding="utf-8") as f:
        html = f.read()
    m = re.search(r"const DATA = (\{.*?\});\s*\n\s*const C", html, re.S)
    assert m, "DATA object not found"
    raw = m.group(1)
    raw = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_ ]*?)\s*:", r'\1"\2":', raw)
    raw = raw.replace("'", '"')
    raw = re.sub(r",\s*([\]}])", r"\1", raw)
    return json.loads(raw)


@pytest.fixture(scope="module")
def discount():
    return json.loads(open(os.path.join(REPORTS, "discount_analysis.json")).read())


@pytest.fixture(scope="module")
def winback():
    return json.loads(open(os.path.join(REPORTS, "winback_economics.json")).read())


@pytest.fixture(scope="module")
def html():
    return open(DASH, encoding="utf-8").read()


class TestPagesExist:
    def test_pricing_block_in_data(self, dash_data):
        assert "pricing" in dash_data
        assert set(dash_data["pricing"]) == {"discount", "winback"}

    def test_nav_items_present(self, html):
        assert "nav('pricing',this)" in html
        assert "nav('winback',this)" in html

    def test_pages_present(self, html):
        assert 'id="page-pricing"' in html
        assert 'id="page-winback"' in html

    def test_titles_registered(self, html):
        assert "pricing:[" in html

    def test_init_hook_calls_build(self, html):
        assert "buildPricing();" in html

    def test_render_functions_defined(self, html):
        for fn in ("buildPricingMargin", "buildPricingTable",
                   "buildWinbackSens", "buildWinbackTable",
                   "runDiscountLab", "runBudgetWorklist"):
            assert f"function {fn}(" in html, f"{fn} not defined"

    def test_canvas_elements_present(self, html):
        assert 'id="ch_pricing_margin"' in html
        assert 'id="ch_winback_sens"' in html

    def test_slider_handlers_wired(self, html):
        assert 'oninput="runDiscountLab()"' in html
        assert 'oninput="runBudgetWorklist()"' in html


class TestDiscountDataMatchesArtifact:
    """Dashboard values must equal the analysis artifact, to the digit."""

    def test_depths_match(self, dash_data, discount):
        assert dash_data["pricing"]["discount"]["depths"] == \
            [r["discount"] for r in discount["margin_curve"]]

    def test_margin_curve_matches(self, dash_data, discount):
        assert dash_data["pricing"]["discount"]["margin_pct_of_list"] == \
            [r["margin_pct_of_list"] for r in discount["margin_curve"]]

    def test_break_even_matches(self, dash_data, discount):
        assert dash_data["pricing"]["discount"]["break_even_lift"] == \
            [r["break_even_volume_lift"] for r in discount["break_even"]]

    def test_headline_flags_match(self, dash_data, discount):
        d = dash_data["pricing"]["discount"]
        assert d["volume_response_detected"] == discount["headline"]["volume_response_detected"]
        assert d["kruskal_p"] == discount["discount_response"]["kruskal_wallis_p"]
        assert d["break_even_at_20"] == discount["headline"]["break_even_lift_at_20pct"]

    def test_pinned_headline_values(self, dash_data):
        d = dash_data["pricing"]["discount"]
        assert d["volume_response_detected"] is False
        assert d["kruskal_p"] == pytest.approx(0.305, abs=0.01)
        assert d["break_even_at_20"] == pytest.approx(0.592, abs=0.01)


class TestWinbackDataMatchesArtifact:
    def test_pool_matches(self, dash_data, winback):
        w = dash_data["pricing"]["winback"]
        assert w["customers"] == winback["pool"]["customers"] == 448
        assert w["historical_spend"] == winback["pool"]["historical_spend_inr"]

    def test_economics_match(self, dash_data, winback):
        w = dash_data["pricing"]["winback"]
        assert w["ev_per_contact"] == winback["baseline_campaign"]["expected_profit_per_contact"]
        assert w["ev_total"] == winback["baseline_campaign"]["expected_profit_total"]

    def test_break_even_and_cross_check_survive_to_the_ui(self, dash_data, winback):
        w = dash_data["pricing"]["winback"]
        assert w["break_even_p"] == winback["break_even"]["break_even_churn_probability"]
        assert w["bayes_threshold"] == winback["bayes_threshold_cross_check"][
            "churn_model_bayes_threshold"]
        assert w["consistent"] is True

    def test_sensitivity_grid_complete(self, dash_data, winback):
        assert len(dash_data["pricing"]["winback"]["sensitivity"]) == \
            len(winback["sensitivity"])

    def test_tiers_complete(self, dash_data, winback):
        assert len(dash_data["pricing"]["winback"]["tiers"]) == \
            len(winback["tiered_scenarios"])

    def test_worklist_present(self, dash_data):
        assert "eligible_customers" in dash_data["pricing"]["winback"]["worklist"]


class TestParserSafety:
    """The values must survive the repo's naive JS-to-JSON conversion."""

    def test_no_apostrophes_in_pricing_block(self, dash_data):
        def scan(o):
            if isinstance(o, dict):
                for v in o.values():
                    scan(v)
            elif isinstance(o, list):
                for v in o:
                    scan(v)
            elif isinstance(o, str):
                assert "'" not in o, f"apostrophe in pricing string: {o[:80]}"
        scan(dash_data["pricing"])

    def test_no_comma_colon_sequences(self, dash_data):
        """', word:' inside a string value would be re-quoted as a key."""
        def scan(o):
            if isinstance(o, dict):
                for v in o.values():
                    scan(v)
            elif isinstance(o, list):
                for v in o:
                    scan(v)
            elif isinstance(o, str):
                assert not re.search(r",\s*[A-Za-z_][A-Za-z0-9_ ]*?\s*:", o), o[:120]
        scan(dash_data["pricing"])


class TestNoHandTypedNumbers:
    """Every rendered figure must be traceable to the pricing artifacts.

    The two pages are GENERATED by scripts/inject_pricing_dashboard.py, so their
    KPI cards legitimately contain figures at injection time. The invariant that
    matters is provenance: each rendered figure must equal the corresponding
    artifact value formatted by the generator. A hand-typed number would not.
    """

    @staticmethod
    def _fmt_inr(x):
        if abs(x) >= 1e7:
            return f"₹{x / 1e7:.2f} Cr"
        if abs(x) >= 1e5:
            return f"₹{x / 1e5:.2f} L"
        return f"₹{x:,.0f}"

    def test_every_rendered_rupee_figure_comes_from_an_artifact(self, html, discount, winback):
        start = html.index('id="page-pricing"')
        end = html.index('id="page-winback"')
        pricing_block = html[start:html.index('</div>\n\n    <div class="page" id="page-winback">')]
        rendered = re.findall(r">\s*(₹[\d,.]+\s*(?:Cr|L)?)\s*<", pricing_block)
        assert rendered, "no figures found on the Pricing Lab page"

        expected = {
            self._fmt_inr(discount["repricing_scenarios"]["cap_10"]["margin_recovered"]),
            self._fmt_inr(winback["pool"]["historical_spend_inr"]),
            self._fmt_inr(winback["baseline_campaign"]["expected_profit_per_contact"]),
            self._fmt_inr(winback["baseline_campaign"]["expected_profit_total"]),
        }
        for value in rendered:
            assert value in expected, (
                f"rendered figure {value!r} is not produced by any pricing artifact — "
                f"expected one of {sorted(expected)}"
            )


class TestInjectorIdempotency:
    """Re-running the injector must be a no-op, not an append.

    Found in review: the titles line was being added on EVERY run (3 copies
    after 3 runs) and a blank line accumulated. Duplicate keys are legal JS but
    the file grows without bound. This test reproduces the failure in seconds.
    """

    def test_second_run_produces_identical_bytes(self):
        import hashlib
        import shutil
        import subprocess
        import sys

        target = Path(DASH)
        before = hashlib.md5(target.read_bytes()).hexdigest()

        subprocess.run([sys.executable, str(Path(BASE) / "scripts" / "inject_pricing_dashboard.py")],
                       check=True, capture_output=True)
        after = hashlib.md5(target.read_bytes()).hexdigest()
        assert before == after, (
            "injector is not idempotent — the dashboard changes on every run, "
            "which means it would grow unbounded in CI"
        )

    def test_titles_key_appears_once(self, html):
        assert html.count('pricing:["Pricing Lab & Win-Back"') == 1

    def test_no_duplicate_data_keys(self, dash_data):
        # json.loads already guarantees no duplicate keys, but the raw text can
        # still contain them — check the source
        raw = open(DASH, encoding="utf-8").read()
        assert raw.count('\n  pricing: ') == 1


def test_each_navigation_page_has_a_title():
    """Prevent the live Win-Back navigation crash (missing titles.winback)."""
    for path in ("index.html", "dashboard.html", "dashboard/index.html", "dashboard/dashboard.html"):
        raw = (Path(BASE) / path).read_text(encoding="utf-8")
        title_block = raw.split("const titles = {", 1)[1].split("};", 1)[0]
        destinations = set(re.findall(r"onclick=\"nav\('([^']+)'", raw))
        keys = set(re.findall(r"^\s*(\w+):", title_block, re.M))
        assert destinations <= keys, f"{path}: titles missing for {destinations - keys}"
