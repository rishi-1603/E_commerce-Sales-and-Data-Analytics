"""Author a professional 4-page report layout into the PBIP (PBIR format)."""
import json, os, shutil, uuid

ROOT = r'C:\\Users\\user\\portfolio-roadmaps\\repos\\ecom\\powerbi\\pbix'
REPORT = os.path.join(ROOT, 'EcomAnalytics.Report')
DEF = os.path.join(REPORT, 'definition')

VC_SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json'
PAGE_SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json'
PAGES_SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json'
REPORT_SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json'
VER_SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json'


def m(entity, prop):
    return {'field': {'Measure': {'Expression': {'SourceRef': {'Entity': entity}},
                                  'Property': prop}}, 'queryRef': f'{entity}.{prop}'}


def c(entity, prop):
    return {'field': {'Column': {'Expression': {'SourceRef': {'Entity': entity}},
                                 'Property': prop}}, 'queryRef': f'{entity}.{prop}'}


def a(entity, prop):
    return {'field': {'Aggregation': {'Expression': {'Column': {
        'Expression': {'SourceRef': {'Entity': entity}}, 'Property': prop}},
        'Function': 0}}, 'queryRef': f'Sum({entity}.{prop})', 'nativeQueryRef': f'Sum({prop})'}


def V(name, vtype, qstate, **opts):
    extra = {}
    for k, v in opts.items():
        if k == 'legend':
            extra['legend'] = {'projections': [c(v['entity'], v['prop'])]}
        elif k == 'objects':
            extra['objects'] = v
    base = {'$schema': VC_SCHEMA, 'name': name,
            'position': {'x': opts.get('_x', 0), 'y': opts.get('_y', 0),
                         'z': 0, 'height': opts.get('_h', 300), 'width': opts.get('_w', 300)},
            'visual': {'visualType': vtype, 'query': {'queryState': qstate}},
            'drillFilterOtherVisuals': True}
    base.update(extra)
    return base


def S(name, x, y, w, h, entity, prop):
    proj = c(entity, prop); proj['active'] = True
    qs = {'Values': {'projections': [proj]}, 'sortDefinition': {'isDefaultSort': True}}
    ob = {'data': [{'properties': {'mode': {'expr': {'Literal': {'Value': "'Basic'"}}}}}]}
    return {'$schema': VC_SCHEMA, 'name': name,
            'position': {'x': x, 'y': y, 'z': 0, 'height': h, 'width': w},
            'visual': {'visualType': 'slicer', 'query': {'queryState': qs}, 'objects': ob},
            'drillFilterOtherVisuals': True,
            'filterConfig': {'filters': [{'name': uuid.uuid4().hex[:20],
                 'field': proj['field'], 'type': 'Categorical'}]}


def Save(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(o, f, indent=2)


def Page(t):
    pid = str(uuid.uuid4())
    Save(os.path.join(DEF, 'pages', pid, 'page.json'),
         {'$schema': PAGE_SCHEMA, 'name': pid, 'displayName': t,
          'displayOption': 'FitToPage', 'height': 720, 'width': 1280})
    return pid


# ── RESET definition core pieces ────────────────────────────────────────
if os.path.isdir(DEF):
    if os.path.isdir(os.path.join(DEF, 'pages')):
        shutil.rmtree(os.path.join(DEF, 'pages'))
    for p in ['version.json', 'report.json', 'definition.pbir']:
        fp = os.path.join(DEF, p)
        if os.path.exists(fp): os.remove(fp)

Save(os.path.join(DEF, 'version.json'), {'$schema': VER_SCHEMA, 'version': '2.0.0'})
Save(os.path.join(DEF, 'report.json'), {'$schema': REPORT_SCHEMA, 'themeCollection': {}})
Save(os.path.join(DEF, 'definition.pbir'),
     {'version': '4.0',
      'datasetReference': {'byPath': {'path': '../EcomAnalytics.SemanticModel'}}})

# ── Page 1: Executive Overview ──────────────────────────────────────────
p1 = Page('Executive Overview')
# 6 KPI cards
Save(os.path.join(DEF, 'pages', p1[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('KPI_1', 'card', m('Fact_Orders', 'Total Revenue'), _x=40, _y=40, _h=100, _w=190))
Save(os.path.join(DEF, 'pages', p1[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('KPI_2', 'card', m('Fact_Orders', 'Gross Profit'), _x=260, _y=40, _h=100, _w=190))
Save(os.path.join(DEF, 'pages', p1[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('KPI_3', 'card', m('Fact_Orders', 'Gross Margin %'), _x=480, _y=40, _h=100, _w=190))
Save(os.path.join(DEF, 'pages', p1[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('KPI_4', 'card', m('Fact_Orders', 'Delivered Orders'), _x=700, _y=40, _h=100, _w=190))
Save(os.path.join(DEF, 'pages', p1[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('KPI_5', 'card', m('Fact_Orders', 'Average Order Value'), _x=920, _y=40, _h=100, _w=190))
Save(os.path.join(DEF, 'pages', p1[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('KPI_6', 'card', m('Fact_Orders', 'Active Customers'), _x=1140, _y=40, _h=100, _w=190))
# Year slicer (canonical Values role)
Save(os.path.join(DEF, 'pages', p1[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     S('YearSlicer', 980, 150, 280, 110, 'Dim_Calendar', 'Year'))
# Revenue line chart
Save(os.path.join(DEF, 'pages', p1[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('RevenueLine', 'lineChart',
       {'Category': {'projections': [c('Dim_Calendar', 'MonthName')]},
        'Y': {'projections': [m('Fact_Orders', 'Total Revenue')]}},
       _x=40, _y=170, _h=280, _w=620,
       legend={'entity': 'Fact_Orders', 'prop': 'Total Revenue'}))
# Category revenue clustered column
Save(os.path.join(DEF, 'pages', p1[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('RevenueByCat', 'clusteredColumnChart',
       {'Category': {'projections': [c('Dim_Products', 'category')]},
        'Y': {'projections': [m('Fact_Orders', 'Total Revenue')]}},
       _x=660, _y=170, _h=280, _w=300))
# Payment method bar
Save(os.path.join(DEF, 'pages', p1[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('PaymentsBar', 'barChart',
       {'Category': {'projections': [c('Fact_Orders', 'payment_method')]},
        'Y': {'projections': [m('Fact_Orders', 'Total Revenue')]}},
       _x=40, _y=470, _h=230, _w=400))
# Segment table
Save(os.path.join(DEF, 'pages', p1[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('SegmentTable', 'tableEx',
       {'Values': {'projections': [c('Dim_Customers', 'segment'),
                    m('Fact_Orders', 'Total Revenue'),
                    m('Fact_Orders', 'Active Customers')]}}),
       _x=440, _y=470, _h=230, _w=400))
# Region delivered orders
Save(os.path.join(DEF, 'pages', p1[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('RegionOrders', 'clusteredColumnChart',
       {'Category': {'projections': [c('Dim_Customers', 'region')]},
        'Y': {'projections': [m('Fact_Orders', 'Delivered Orders')]}},
       _x=860, _y=470, _h=230, _w=400))

# ── Page 2: Sales Performance ───────────────────────────────────────────
p2 = Page('Sales Performance')
Save(os.path.join(DEF, 'pages', p2[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('SubcategoryCols', 'clusteredColumnChart',
       {'Category': {'projections': [c('Dim_Products', 'subcategory')]},
        'Y': {'projections': [m('Fact_Orders', 'Total Revenue')]}},
       _x=20, _y=30, _h=330, _w=620))
Save(os.path.join(DEF, 'pages', p2[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('DeliveredMOM', 'lineChart',
       {'Category': {'projections': [c('Dim_Calendar', 'MonthName')]},
        'Y': {'projections': [m('Fact_Orders', 'Delivered Orders')]}},
       _x=660, _y=30, _h=330, _w=600))
Save(os.path.join(DEF, 'pages', p2[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('Reconciliation', 'tableEx',
       {'Values': {'projections': [c('Dim_Products', 'category'),
                    m('Fact_Orders', 'Total Revenue'),
                    m('Fact_Orders', 'Total COGS'),
                    m('Fact_Orders', 'Gross Profit'),
                    m('Fact_Orders', 'Gross Margin %')]}},
       _x=20, _y=380, _h=320, _w=620))
Save(os.path.join(DEF, 'pages', p2[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('GrossByCat', 'clusteredColumnChart',
       {'Category': {'projections': [c('Dim_Products', 'category')]},
        'Y': {'projections': [m('Fact_Orders', 'Gross Profit')]}},
       _x=660, _y=380, _h=320, _w=600))

# ── Page 3: Customer Insights ───────────────────────────────────────────
p3 = Page('Customer Insights')
Save(os.path.join(DEF, 'pages', p3[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('SegBar', 'barChart',
       {'Category': {'projections': [c('Dim_Customers', 'segment')]},
        'Y': {'projections': [m('Fact_Orders', 'Total Revenue')]}},
       _x=20, _y=30, _h=330, _w=400))
Save(os.path.join(DEF, 'pages', p3[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('RegionBar', 'barChart',
       {'Category': {'projections': [c('Dim_Customers', 'region')]},
        'Y': {'projections': [m('Fact_Orders', 'Total Revenue')]}},
       _x=440, _y=30, _h=330, _w=400))
Save(os.path.join(DEF, 'pages', p3[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('AcqCols', 'clusteredColumnChart',
       {'Category': {'projections': [c('Dim_Customers', 'acquisition_channel')]},
        'Y': {'projections': [m('Fact_Orders', 'Total Revenue')]}},
       _x=860, _y=30, _h=330, _w=400))
Save(os.path.join(DEF, 'pages', p3[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('TopCustomers', 'tableEx',
       {'Values': {'projections': [c('Dim_Customers', 'customer_name'),
                    m('Fact_Orders', 'Total Revenue'),
                    m('Fact_Orders', 'Delivered Orders')]}},
       _x=20, _y=380, _h=320, _w=620))
Save(os.path.join(DEF, 'pages', p3[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('ReturnRateLine', 'lineChart',
       {'Category': {'projections': [c('Dim_Calendar', 'MonthName')]},
        'Y': {'projections': [m('Fact_Orders', 'Return Rate %')]}},
       _x=660, _y=380, _h=320, _w=600))

# ── Page 4: Order Operations ────────────────────────────────────────────
p4 = Page('Order Operations')
Save(os.path.join(DEF, 'pages', p4[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('StackedMonth', 'columnChart',
       {'Category': {'projections': [c('Dim_Calendar', 'MonthName')]},
        'Y': {'projections': [a('Fact_Orders', 'order_item_total')]},
        'Legend': {'projections': [c('Fact_Orders', 'order_status')]}},
       _x=20, _y=30, _h=330, _w=620))
Save(os.path.join(DEF, 'pages', p4[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('StatusBars', 'clusteredColumnChart',
       {'Category': {'projections': [c('Fact_Orders', 'order_status')]},
        'Y': {'projections': [a('Fact_Orders', 'order_item_total')]}},
       _x=660, _y=30, _h=330, _w=600))
# 3 KPI cards on P4
Save(os.path.join(DEF, 'pages', p4[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('KPI_P4_1', 'card', m('Fact_Orders', 'Return Rate %'), _x=40, _y=380, _h=320, _w=200))
Save(os.path.join(DEF, 'pages', p4[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('KPI_P4_2', 'card', m('Fact_Orders', 'Delivered Orders'), _x=260, _y=380, _h=320, _w=200))
Save(os.path.join(DEF, 'pages', p4[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('KPI_P4_3', 'card', m('Fact_Orders', 'Delivered Revenue'), _x=480, _y=380, _h=320, _w=200))
# Shipping cost line
Save(os.path.join(DEF, 'pages', p4[:8], 'visuals',
        uuid.uuid4().hex[:16], 'visual.json'),
     V('ShippingLine', 'lineChart',
       {'Category': {'projections': [c('Dim_Calendar', 'MonthName')]},
        'Y': {'projections': [a('Fact_Orders', 'shipping_cost')]}},
       _x=680, _y=380, _h=320, _w=580))

# ── pages.json ──────────────────────────────────────────────────────────
Save(os.path.join(DEF, 'pages', 'pages.json'),
     {'$schema': PAGES_SCHEMA,
      'pageOrder': [p1, p2, p3, p4],
      'activePageName': p1})

print('PBIR report written: 4 professional pages')
print(f'files in definition/: {len([f for _, _, files in os.walk(DEF) for f in files])}')
for pid in [p1[:8], p2[:8], p3[:8], p4[:8]]:
    pj = os.path.join(DEF, 'pages', pid, 'page.json')
    assert os.path.exists(pj), f'Missing page.json for {pid}'
print('All 4 pages have page.json ✓')