"""Build the PBIR structure directly - simplified."""
import json, os, uuid

DEF = r'C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix\EcomAnalytics.Report\definition'
os.makedirs(DEF, exist_ok=True)

# core pieces
with open(os.path.join(DEF, 'version.json'), 'w', encoding='utf-8') as f:
    json.dump({'version': '2.0.0'}, f, indent=2)
with open(os.path.join(DEF, 'report.json'), 'w', encoding='utf-8') as f:
    json.dump({'themeCollection': {}}, f, indent=2)
with open(os.path.join(DEF, 'definition.pbir'), 'w', encoding='utf-8') as f:
    json.dump({'version': '4.0', 'datasetReference': {'byPath': {'path': '../EcomAnalytics.SemanticModel'}}}, f, indent=2)

# pages folder - 4 pages
pages_order = []
for p in ['p1', 'p2', 'p3', 'p4']:
    pd = os.path.join(DEF, 'pages', p)
    os.makedirs(os.path.join(pd, 'visuals'), exist_ok=True)
    pid = uuid.uuid4().hex
    pages_order.append(pid)
    with open(os.path.join(pd, 'page.json'), 'w', encoding='utf-8') as f:
        fname = {'p1': 'Executive Overview', 'p2': 'Sales Performance', 'p3': 'Customer Insights', 'p4': 'Order Operations'}[p]
        json.dump({'displayName': fname, 'displayOption': 'FitToPage', 'height': 720, 'width': 1280}, f, indent=2)
    # write a minimal visual.json
    vid = uuid.uuid4().hex[:16]
    with open(os.path.join(pd, 'visuals', vid + '.json'), 'w', encoding='utf-8') as f:
        json.dump({'visualType': 'card'}, f, indent=2)

# pages.json
with open(os.path.join(DEF, 'pages', 'pages.json'), 'w', encoding='utf-8') as f:
    json.dump({'pageOrder': pages_order, 'activePageName': pages_order[0]}, f, indent=2)

print('PBIR structure written successfully')