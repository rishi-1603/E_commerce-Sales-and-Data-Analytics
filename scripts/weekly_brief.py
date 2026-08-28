"""
weekly_brief.py — grounded weekly retention brief
==================================================
This is the RESPONSIBLE AI layer of the project. It generates a short,
boardroom-style weekly brief by letting an LLM **narrate a pre-computed fact
sheet** — never letting it invent numbers.

GROUNDING RULES (enforced in the system prompt):
  1. The model may ONLY use facts present in reports/fact_sheet.json.
  2. If a figure is not in the fact sheet, it must say "not available".
  3. It must clearly separate:
        [Data-validated finding]  — directly supported by the fact sheet
        [Investigation hypothesis] — a possible next step, NOT a proven fact
  4. It must not present correlation as causation.

USAGE:
    # With an OpenAI-compatible API key (uses openai package if installed):
    OPENAI_API_KEY=...  python scripts/weekly_brief.py

    # Without any API key — emits a deterministic brief built from the facts
    # alone (proves the narrative is fully reconstructable from the data):
    python scripts/weekly_brief.py

This fallback is intentional: it demonstrates that the LLM is assembling
verified facts, not generating them. The same fact sheet always yields a
consistent, checkable brief.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS_PATH = os.path.join(BASE, "reports", "fact_sheet.json")

SYSTEM_PROMPT = """You are a precise analytics assistant writing a ONE-PAGE
weekly retention brief for an e-commerce leadership team.

STRICT GROUNDING RULES:
- You may ONLY use facts present in the provided FACT SHEET.
- If a number is not in the fact sheet, write "not available". NEVER invent,
  estimate, or round numbers that are not given.
- Do not present correlation as causation.
- Structure the brief as:
    1) Headline (one sentence)
    2) KPI snapshot (only figures from the fact sheet)
    3) Data-validated findings (each tagged [Data-validated])
    4) Suggested investigation areas (each tagged [Investigation hypothesis])
    5) One recommended next action with its owner
- Keep it under 220 words. Plain business language, no jargon."""


def load_facts():
    if not os.path.exists(FACTS_PATH):
        print("ERROR: reports/fact_sheet.json not found.")
        print("Run:  python scripts/build_context.py   first.")
        sys.exit(1)
    with open(FACTS_PATH) as f:
        return json.load(f)


def llm_brief(facts):
    """Call an OpenAI-compatible endpoint if a key + client are available."""
    try:
        from openai import OpenAI
    except ImportError:
        return None
    if not os.environ.get("OPENAI_API_KEY"):
        return None
    client = OpenAI()
    user_prompt = ("FACT SHEET (the ONLY source of truth):\n```json\n"
                   + json.dumps(facts, indent=2, ensure_ascii=False)
                   + "\n```\n\nWrite the weekly brief now.")
    resp = client.chat.completions.create(
        model=os.environ.get("BRIEF_MODEL", "gpt-4o-mini"),
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": user_prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content


def fallback_brief(facts):
    """Deterministic brief assembled purely from the fact sheet."""
    s, c, f = facts["sales"], facts["churn"], facts["forecast"]
    top_seg = facts["segments"]["by_segment"][0]
    lines = [
        "# Weekly Retention Brief (grounded, no-LLM fallback)",
        f"_{facts['generated_at']} · auto-assembled from verified fact sheet_",
        "",
        "## Headline",
        f"Cooling-off risk is concentrated in **{c['cooling_off_customers']}** "
        f"customers worth **{c['historical_spend_of_cooling_off']}** of "
        "historical spend; a measured win-back is the priority this week.",
        "",
        "## KPI snapshot",
        f"- Revenue to date: **{s['total_revenue']}** (margin "
        f"{s['gross_margin_pct']}%)",
        f"- Churn rate: **{c['overall_churn_rate_pct']}%** "
        f"({c['model_note']})",
        f"- {f['horizon_months']}-month revenue projection: "
        f"**{f['total_projected']}**",
        "",
        "## Data-validated findings",
        f"- [Data-validated] Top value segment is **{top_seg['segment']}** "
        f"with {top_seg['customers']} customers and {top_seg['historical_spend']} "
        "of historical spend.",
        f"- [Data-validated] Softest forecast month is **{f['softest_month']}**; "
        f"caveat: {f['caveat']}.",
        f"- [Data-validated] {c['spend_disclaimer'].capitalize()} for the "
        f"cooling-off group.",
        "",
        "## Investigation hypotheses (NOT proven)",
        "- [Investigation hypothesis] Test whether the cooling-off segment "
        "responds to a tiered win-back vs. a holdout control group.",
        "- [Investigation hypothesis] Check if the softest forecast month "
        "aligns with a known seasonal driver (needs external context).",
        "",
        "## Recommended next action",
        "Owner: **CRM/Retention Lead** — launch a tiered win-back on the "
        "cooling-off segment with a 20% randomized holdout; measure 90-day "
        "reactivation revenue (treated − control).",
        "",
        "---",
        "_Every figure above is traceable to reports/fact_sheet.json. "
        "Re-run `python scripts/build_context.py` to refresh._",
    ]
    return "\n".join(lines)


def main():
    facts = load_facts()
    brief = llm_brief(facts)
    source = "LLM (OpenAI-compatible)"
    if brief is None:
        brief = fallback_brief(facts)
        source = "deterministic fallback (no API key / openai not installed)"

    out = os.path.join(BASE, "reports", "weekly_brief.md")
    with open(out, "w") as fh:
        fh.write(brief + "\n")
    print(f"Weekly brief generated via {source}")
    print(f"Written to: {out}")
    print("\n" + "-" * 60 + "\n" + brief)


if __name__ == "__main__":
    main()
