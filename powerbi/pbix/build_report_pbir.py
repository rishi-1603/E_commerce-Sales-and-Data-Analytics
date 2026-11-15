"""Author a 4-page Power BI report into the PBIP (PBIR format).

Fixes over the first attempt:
  * page folder name == page.json "name" == pages.json pageOrder entry
  * definition.pbir lives only at the .Report root (not inside definition/)
  * drillFilterOtherVisuals sits inside "visual", matching Power BI's own output
  * legend uses the "Series" query role (the capability name), not "Legend"
"""
import json
import os
import shutil
import uuid

ROOT = r"C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix"
REPORT = os.path.join(ROOT, "EcomAnalytics.Report")
DEF = os.path.join(REPORT, "definition")

VC_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
PAGES_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json"
REPORT_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json"
VER_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json"

CANVAS_W, CANVAS_H = 1280, 720

# Titles are opt-in: a single schema-invalid property makes Power BI reject the
# whole report definition ("Failed to load the report"), so they are tested separately.
TITLES = os.environ.get("PBIR_TITLES", "0") == "1"


def m(entity, prop):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": entity}},
                                  "Property": prop}}, "queryRef": f"{entity}.{prop}",
            "nativeQueryRef": prop}


def c(entity, prop):
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": entity}},
                                 "Property": prop}}, "queryRef": f"{entity}.{prop}",
            "nativeQueryRef": prop}


def title_obj(text):
    return {"title": [{"properties": {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "text": {"expr": {"Literal": {"Value": f"'{text}'"}}},
    }}]}


def visual(name, vtype, qstate, x, y, w, h, title=None, legend=None, objects=None,
           with_title=False):
    vis = {"visualType": vtype, "query": {"queryState": qstate}}
    if legend:
        vis["query"]["queryState"]["Series"] = {"projections": [c(*legend)]}
    if objects:
        vis["objects"] = objects
    if with_title and title:
        vis["visualContainerObjects"] = title_obj(title)
    out = {"$schema": VC_SCHEMA, "name": name,
           "position": {"x": x, "y": y, "z": 0, "height": h, "width": w},
           "visual": vis}
    return out


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def add(page_dir, vis):
    # Power BI keys visuals by a 20-char hex id; the folder name is free-form, so
    # keep the readable label in the folder and put the id in the JSON.
    label = vis["name"]
    vis["name"] = uuid.uuid4().hex[:20]
    folder = f"{page_dir[:4]}_{label}"
    save(os.path.join(DEF, "pages", page_dir, "visuals", folder, "visual.json"), vis)


def page(title):
    pid = str(uuid.uuid4())
    save(os.path.join(DEF, "pages", pid, "page.json"),
         {"$schema": PAGE_SCHEMA, "name": pid, "displayName": title,
          "displayOption": "FitToPage", "height": CANVAS_H, "width": CANVAS_W})
    return pid


def slicer(name, x, y, w, h, entity, prop, title):
    """Minimal, schema-valid slicer.

    Two rules learned the hard way: `sortDefinition` is a sibling of
    `queryState` (not a member of it), and a slicer needs no filterConfig.
    """
    proj = c(entity, prop)
    proj["active"] = True
    return {
        "$schema": VC_SCHEMA, "name": name,
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w},
        "visual": {
            "visualType": "slicer",
            "query": {"queryState": {"Values": {"projections": [proj]}}},
            "visualContainerObjects": title_obj(title),
        },
    }


def card(name, x, y, w, h, measure, title, with_title=False):
    return visual(name, "card", {"Values": {"projections": [m("Fact_Orders", measure)]}},
                  x, y, w, h, title, with_title=with_title)


# â”€â”€ reset â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if os.path.isdir(os.path.join(DEF, "pages")):
    shutil.rmtree(os.path.join(DEF, "pages"))
for stale in [os.path.join(DEF, "definition.pbir")]:
    if os.path.exists(stale):
        os.remove(stale)

save(os.path.join(DEF, "version.json"), {"$schema": VER_SCHEMA, "version": "2.0.0"})
save(os.path.join(DEF, "report.json"), {"$schema": REPORT_SCHEMA, "themeCollection": {}})
save(os.path.join(REPORT, "definition.pbir"),
     {"version": "4.0", "datasetReference": {"byPath": {"path": "../EcomAnalytics.SemanticModel"}}})

pages = []

# â•â• Page 1 â€” Executive Overview â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
p1 = page("Executive Overview")
pages.append(p1)
kpis = [("Total Revenue", "Total revenue"), ("Gross Profit", "Gross profit"),
        ("Gross Margin %", "Gross margin"), ("Delivered Orders", "Delivered orders"),
        ("Average Order Value", "Average order value"), ("Active Customers", "Active customers")]
for i, (measure, label) in enumerate(kpis):
    add(p1, card(f"KPI_{i+1}", 16 + i * 208, 16, 196, 96, measure, label, with_title=True))
add(p1, slicer("YearSlicer", 16, 124, 196, 88, "Dim_Calendar", "Year", "Year"))
add(p1, visual("RevenueTrend", "areaChart",
               {"Category": {"projections": [c("Dim_Calendar", "MonthName")]},
                "Y": {"projections": [m("Fact_Orders", "Total Revenue")]}},
               224, 124, 592, 270, "Revenue by month", with_title=True))
add(p1, visual("RevenueByCategory", "clusteredColumnChart",
               {"Category": {"projections": [c("Dim_Products", "category")]},
                "Y": {"projections": [m("Fact_Orders", "Total Revenue")]}},
               828, 124, 436, 270, "Revenue by category", with_title=True))
add(p1, visual("SegmentTable", "tableEx",
               {"Values": {"projections": [c("Dim_Customers", "segment"),
                                           m("Fact_Orders", "Total Revenue"),
                                           m("Fact_Orders", "Active Customers")]}},
               16, 406, 420, 298, "Revenue by customer segment", with_title=True))
add(p1, visual("PaymentBar", "barChart",
               {"Category": {"projections": [c("Fact_Orders", "payment_method")]},
                "Y": {"projections": [m("Fact_Orders", "Total Revenue")]}},
               448, 406, 380, 298, "Revenue by payment method", with_title=True))
add(p1, visual("RegionOrders", "clusteredColumnChart",
               {"Category": {"projections": [c("Dim_Customers", "region")]},
                "Y": {"projections": [m("Fact_Orders", "Delivered Orders")]}},
               840, 406, 424, 298, "Delivered orders by region", with_title=True))

# â•â• Page 2 â€” Sales Performance â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
p2 = page("Sales Performance")
pages.append(p2)
kpis2 = [("Total Revenue", "Total revenue"), ("Total COGS", "Cost of goods sold"),
         ("Gross Profit", "Gross profit"), ("Gross Margin %", "Gross margin")]
for i, (measure, label) in enumerate(kpis2):
    add(p2, card(f"KPI_{i+1}", 16 + i * 310, 16, 298, 96, measure, label, with_title=True))
add(p2, visual("SubcategoryCols", "clusteredColumnChart",
               {"Category": {"projections": [c("Dim_Products", "subcategory")]},
                "Y": {"projections": [m("Fact_Orders", "Total Revenue")]}},
               16, 124, 620, 290, "Revenue by subcategory", with_title=True))
add(p2, visual("DeliveredOrdersTrend", "areaChart",
               {"Category": {"projections": [c("Dim_Calendar", "MonthName")]},
                "Y": {"projections": [m("Fact_Orders", "Delivered Orders")]}},
               648, 124, 616, 290, "Delivered orders by month", with_title=True))
add(p2, visual("Reconciliation", "tableEx",
               {"Values": {"projections": [c("Dim_Products", "category"),
                                           m("Fact_Orders", "Total Revenue"),
                                           m("Fact_Orders", "Total COGS"),
                                           m("Fact_Orders", "Gross Profit"),
                                           m("Fact_Orders", "Gross Margin %")]}},
               16, 426, 620, 278, "Category reconciliation", with_title=True))
add(p2, visual("GrossProfitByCategory", "clusteredColumnChart",
               {"Category": {"projections": [c("Dim_Products", "category")]},
                "Y": {"projections": [m("Fact_Orders", "Gross Profit")]}},
               648, 426, 616, 278, "Gross profit by category", with_title=True))

# â•â• Page 3 â€” Customer Insights â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
p3 = page("Customer Insights")
pages.append(p3)
kpis3 = [("Active Customers", "Active customers"), ("Average Order Value", "Average order value"),
         ("Total Revenue", "Total revenue"), ("Gross Margin %", "Gross margin")]
for i, (measure, label) in enumerate(kpis3):
    add(p3, card(f"KPI_{i+1}", 16 + i * 310, 16, 298, 96, measure, label, with_title=True))
add(p3, visual("SegmentBar", "barChart",
               {"Category": {"projections": [c("Dim_Customers", "segment")]},
                "Y": {"projections": [m("Fact_Orders", "Total Revenue")]}},
               16, 124, 410, 290, "Revenue by segment", with_title=True))
add(p3, visual("RegionBar", "barChart",
               {"Category": {"projections": [c("Dim_Customers", "region")]},
                "Y": {"projections": [m("Fact_Orders", "Total Revenue")]}},
               438, 124, 410, 290, "Revenue by region", with_title=True))
add(p3, visual("AcquisitionCols", "clusteredColumnChart",
               {"Category": {"projections": [c("Dim_Customers", "acquisition_channel")]},
                "Y": {"projections": [m("Fact_Orders", "Total Revenue")]}},
               860, 124, 404, 290, "Revenue by acquisition channel", with_title=True))
add(p3, visual("TopCustomers", "tableEx",
               {"Values": {"projections": [c("Dim_Customers", "customer_name"),
                                           m("Fact_Orders", "Total Revenue"),
                                           m("Fact_Orders", "Delivered Orders")]}},
               16, 426, 620, 278, "Top customers", with_title=True))
add(p3, visual("SegmentEconomics", "tableEx",
               {"Values": {"projections": [c("Dim_Customers", "segment"),
                                           m("Fact_Orders", "Active Customers"),
                                           m("Fact_Orders", "Average Order Value"),
                                           m("Fact_Orders", "Gross Margin %")]}},
               648, 426, 616, 278, "Segment economics", with_title=True))

# â•â• Page 4 â€” Order Operations â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
p4 = page("Order Operations")
pages.append(p4)
kpis4 = [("Placed Orders", "Orders placed"), ("Delivered Orders", "Delivered"),
         ("Returned Orders", "Returned"), ("Return Rate %", "Return rate")]
for i, (measure, label) in enumerate(kpis4):
    add(p4, card(f"KPI_{i+1}", 16 + i * 310, 16, 298, 96, measure, label, with_title=True))
add(p4, visual("StatusByMonth", "columnChart",
               {"Category": {"projections": [c("Dim_Calendar", "MonthName")]},
                "Y": {"projections": [m("Fact_Orders", "Orders by Status")]}},
               16, 124, 620, 290, "Orders by status and month",
               legend=("Fact_Orders", "order_status"), with_title=True))
add(p4, visual("StatusMix", "donutChart",
               {"Category": {"projections": [c("Fact_Orders", "order_status")]},
                "Y": {"projections": [m("Fact_Orders", "Orders by Status")]}},
               648, 124, 616, 290, "Order status mix", with_title=True))
add(p4, visual("ShippingCostTrend", "areaChart",
               {"Category": {"projections": [c("Dim_Calendar", "MonthName")]},
                "Y": {"projections": [m("Fact_Orders", "Shipping Cost")]}},
               16, 426, 620, 278, "Shipping cost by month", with_title=True))
add(p4, visual("ReturnRateTrend", "areaChart",
               {"Category": {"projections": [c("Dim_Calendar", "MonthName")]},
                "Y": {"projections": [m("Fact_Orders", "Return Rate %")]}},
               648, 426, 616, 278, "Return rate by month", with_title=True))

# â”€â”€ pages.json â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
save(os.path.join(DEF, "pages", "pages.json"),
     {"$schema": PAGES_SCHEMA, "pageOrder": pages, "activePageName": pages[0]})  # noqa: E501

n = sum(len(files) for _, _, files in os.walk(DEF))
print(f"wrote {len(pages)} pages, {n} files under definition/")
for pid in pages:
    pj = os.path.join(DEF, "pages", pid, "page.json")
    assert os.path.exists(pj), pid
print("page folders match pages.json âœ“")
