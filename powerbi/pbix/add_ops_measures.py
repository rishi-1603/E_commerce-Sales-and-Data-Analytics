"""Rewrite the order-operations measures as single-line TMDL expressions.

TMDL is indentation-sensitive; multi-line expressions with mixed tabs/spaces
trigger 'Parsing error type - Indentation'. Single-line bodies are unambiguous.
"""
import re
import uuid

PATH = r"C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix\EcomAnalytics.SemanticModel\definition\tables\Fact_Orders.tmdl"

MEASURES = [
    ("Placed Orders", "DISTINCTCOUNT(Fact_Orders[order_id])", "#,0"),
    ("Orders by Status", "DISTINCTCOUNT(Fact_Orders[order_id])", "#,0"),
    ("Returned Orders",
     'CALCULATE(DISTINCTCOUNT(Fact_Orders[order_id]), Fact_Orders[order_status] = "Returned")', "#,0"),
    ("Cancelled Orders",
     'CALCULATE(DISTINCTCOUNT(Fact_Orders[order_id]), Fact_Orders[order_status] = "Cancelled")', "#,0"),
    ("Processing Orders",
     'CALCULATE(DISTINCTCOUNT(Fact_Orders[order_id]), Fact_Orders[order_status] = "Processing")', "#,0"),
    ("Delivery Rate %", "DIVIDE([Delivered Orders], [Placed Orders], 0)", "0.00%"),
    ("Return Rate %", "DIVIDE([Returned Orders], [Placed Orders], 0)", "0.00%"),
    ("Shipping Cost",
     'CALCULATE(SUM(Fact_Orders[shipping_cost]), Fact_Orders[order_status] IN {"Delivered", "Processing"})', "#,0.00"),
    ("Units Sold",
     'CALCULATE(SUM(Fact_Orders[quantity]), Fact_Orders[order_status] IN {"Delivered", "Processing"})', "#,0"),
]

with open(PATH, encoding="utf-8") as f:
    tmdl = f.read()

for name, _, _ in MEASURES:
    tmdl = re.sub(rf"\n\tmeasure '{re.escape(name)}' =.*?(?=\n\tmeasure |\n\tcolumn )", "",
                  tmdl, flags=re.S)

block = "".join(
    f"\n\tmeasure '{name}' = {expr}\n"
    f"\t\tformatString: {fmt}\n"
    f"\t\tlineageTag: {uuid.uuid4()}\n"
    for name, expr, fmt in MEASURES
)

idx = tmdl.index("\n\tcolumn item_id")
tmdl = tmdl[:idx] + block + tmdl[idx:]

with open(PATH, "w", encoding="utf-8", newline="\n") as f:
    f.write(tmdl)

# sanity: no measure header may end with '=' (i.e. body must be inline)
bad = [ln for ln in tmdl.splitlines() if ln.startswith("\tmeasure ") and ln.rstrip().endswith("=")]
print("multi-line measure headers:", bad)
print("measures:", len(re.findall(r"^\tmeasure ", tmdl, flags=re.M)))
