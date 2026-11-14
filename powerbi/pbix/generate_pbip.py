"""Generate the EcomAnalytics Power BI Project (.pbip) — semantic model in TMDL.

Creates:
  EcomAnalytics.pbip
  EcomAnalytics.SemanticModel/definition.pbism
  EcomAnalytics.SemanticModel/definition/model.tmdl
  EcomAnalytics.SemanticModel/definition/tables/*.tmdl
  EcomAnalytics.SemanticModel/definition/relationships.tmdl

DAX measures are copied verbatim from powerbi/dax_measures.md.
All TMDL files are tab-indented (TMDL requires tabs, not spaces).
"""
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
SM = os.path.join(HERE, 'EcomAnalytics.SemanticModel')
DEF = os.path.join(SM, 'definition')
TBL = os.path.join(DEF, 'tables')
DATA = os.path.join(HERE, 'data')

os.makedirs(TBL, exist_ok=True)


def lineage(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, 'ecomanalytics-' + name))


def data_path(fname):
    # forward slashes avoid M backslash escaping
    return f'{DATA.replace(os.sep, "/")}/{fname}'


def m_partition(table_name, fname, type_pairs):
    cols = ', '.join('{{"{0}", {1}}}'.format(c, t) for c, t in type_pairs)
    return f'''	partition {table_name} = m
		mode: import
		source =
				let
					Source = Csv.Document(File.Contents("{data_path(fname)}"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
					PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
					Typed = Table.TransformColumnTypes(PromotedHeaders, {{{cols}}}, "en-US")
				in
					Typed
'''


def column(name, dtype, hidden=False, summarize=None, fmt=None):
    lines = [f'\tcolumn {name}', f'\t\tdataType: {dtype}', f'\t\tlineageTag: {lineage("col-" + name)}']
    if hidden:
        lines.append('\t\tisHidden')
    if summarize:
        lines.append(f'\t\tsummarizeBy: {summarize}')
    if fmt:
        lines.append(f'\t\tformatString: {fmt}')
    lines.append(f'\t\tsourceColumn: {name}')
    lines.append('')
    lines.append(f'\t\tannotation SummarizationSetBy = Automatic')
    lines.append('')
    return '\n'.join(lines)


def measure(name, dax, fmt):
    dax_indented = '\n'.join('\t\t\t' + line if line else '' for line in dax.strip().splitlines())
    return f'''	measure '{name}' =
{dax_indented}
		formatString: {fmt}
		lineageTag: {lineage("measure-" + name)}
'''


# ---------------- Fact_Orders ----------------
fact_types = [
    ('order_date', 'type datetime'),
    ('quantity', 'Int64.Type'),
    ('unit_price', 'type number'),
    ('discount_pct', 'type number'),
    ('order_item_total', 'type number'),
    ('cost_total', 'type number'),
    ('profit', 'type number'),
    ('shipping_cost', 'type number'),
]

fact_dax = {
    'Total Revenue': ('''CALCULATE(
    SUM(Fact_Orders[order_item_total]),
    Fact_Orders[order_status] IN {"Delivered", "Processing"}
)''', '#,0.00'),
    'Delivered Revenue': ('''CALCULATE(
    SUM(Fact_Orders[order_item_total]),
    Fact_Orders[order_status] = "Delivered"
)''', '#,0.00'),
    'Total COGS': ('''CALCULATE(
    SUMX(
        Fact_Orders,
        Fact_Orders[quantity] * RELATED(Dim_Products[unit_cost])
    ),
    Fact_Orders[order_status] IN {"Delivered", "Processing"}
)''', '#,0.00'),
    'Gross Profit': ('[Total Revenue] - [Total COGS]', '#,0.00'),
    'Gross Margin %': ('DIVIDE([Gross Profit], [Total Revenue], 0)', '0.00%'),
    'Delivered Orders': ('''CALCULATE(
    DISTINCTCOUNT(Fact_Orders[order_id]),
    Fact_Orders[order_status] = "Delivered"
)''', '#,0'),
    'Return Rate %': ('''VAR TotalCompleted =
    CALCULATE(
        DISTINCTCOUNT(Fact_Orders[order_id]),
        Fact_Orders[order_status] IN {"Delivered", "Returned"}
    )
VAR ReturnedCount =
    CALCULATE(
        DISTINCTCOUNT(Fact_Orders[order_id]),
        Fact_Orders[order_status] = "Returned"
    )
RETURN
    DIVIDE(ReturnedCount, TotalCompleted, 0)''', '0.00%'),
    'Average Order Value': ('''DIVIDE(
    [Total Revenue],
    CALCULATE(
        DISTINCTCOUNT(Fact_Orders[order_id]),
        Fact_Orders[order_status] IN {"Delivered", "Processing"}
    ),
    0
)''', '#,0.00'),
    'Active Customers': ('''CALCULATE(
    DISTINCTCOUNT(Fact_Orders[customer_id]),
    Fact_Orders[order_status] IN {"Delivered", "Processing"}
)''', '#,0'),
    'MoM Revenue Change %': ('''VAR CurrentMonthRev = [Total Revenue]
VAR PrevMonthRev =
    CALCULATE(
        [Total Revenue],
        DATEADD(Dim_Calendar[Date], -1, MONTH)
    )
RETURN
    DIVIDE(CurrentMonthRev - PrevMonthRev, PrevMonthRev, 0)''', '+0.0%;-0.0%;0.0%'),
}

fact_tbl = f'''table Fact_Orders
	lineageTag: {lineage('table-Fact_Orders')}
{m_partition('Fact_Orders', 'Fact_Orders.csv', fact_types)}
{measure('Total Revenue', *fact_dax['Total Revenue'])}
{measure('Delivered Revenue', *fact_dax['Delivered Revenue'])}
{measure('Total COGS', *fact_dax['Total COGS'])}
{measure('Gross Profit', *fact_dax['Gross Profit'])}
{measure('Gross Margin %', *fact_dax['Gross Margin %'])}
{measure('Delivered Orders', *fact_dax['Delivered Orders'])}
{measure('Return Rate %', *fact_dax['Return Rate %'])}
{measure('Average Order Value', *fact_dax['Average Order Value'])}
{measure('Active Customers', *fact_dax['Active Customers'])}
{measure('MoM Revenue Change %', *fact_dax['MoM Revenue Change %'])}
{column('item_id', 'string', hidden=True, summarize='none')}
{column('order_id', 'string')}
{column('order_date', 'dateTime')}
{column('order_status', 'string')}
{column('customer_id', 'string', hidden=True, summarize='none')}
{column('product_id', 'string', hidden=True, summarize='none')}
{column('quantity', 'int64')}
{column('unit_price', 'double', summarize='none')}
{column('discount_pct', 'double', summarize='none', fmt='0.00%')}
{column('order_item_total', 'double')}
{column('cost_total', 'double')}
{column('profit', 'double')}
{column('payment_method', 'string', summarize='none')}
{column('shipping_cost', 'double')}
'''

# ---------------- Dim_Products ----------------
prod_types = [
    ('unit_cost', 'type number'),
    ('rating', 'type number'),
]
prod_tbl = f'''table Dim_Products
	lineageTag: {lineage('table-Dim_Products')}
{m_partition('Dim_Products', 'Dim_Products.csv', prod_types)}
{column('product_id', 'string', hidden=True, summarize='none')}
{column('product_name', 'string', summarize='none')}
{column('category', 'string', summarize='none')}
{column('subcategory', 'string', summarize='none')}
{column('unit_cost', 'double', summarize='none')}
{column('rating', 'double', summarize='none')}
'''

# ---------------- Dim_Customers ----------------
cust_types = [
    ('registration_date', 'type date'),
    ('age', 'Int64.Type'),
]
cust_tbl = f'''table Dim_Customers
	lineageTag: {lineage('table-Dim_Customers')}
{m_partition('Dim_Customers', 'Dim_Customers.csv', cust_types)}
{column('customer_id', 'string', hidden=True, summarize='none')}
{column('customer_name', 'string', summarize='none')}
{column('email', 'string', summarize='none', hidden=True)}
{column('region', 'string', summarize='none')}
{column('segment', 'string', summarize='none')}
{column('acquisition_channel', 'string', summarize='none')}
{column('registration_date', 'dateTime')}
{column('age', 'int64', summarize='none')}
{column('gender', 'string', summarize='none')}
'''

# ---------------- Dim_Calendar ----------------
cal_types = [
    ('Date', 'type date'),
    ('Year', 'Int64.Type'),
    ('MonthNumber', 'Int64.Type'),
]
cal_tbl = f'''table Dim_Calendar
	lineageTag: {lineage('table-Dim_Calendar')}
{m_partition('Dim_Calendar', 'Dim_Calendar.csv', cal_types)}
{column('Date', 'dateTime', summarize='none')}
{column('Year', 'int64', summarize='none', fmt='0')}
{column('Quarter', 'string', summarize='none')}
{column('MonthNumber', 'int64', summarize='none', fmt='0', hidden=True)}
{column('MonthName', 'string', summarize='none')}
'''

# ---------------- relationships ----------------
rel = f'''relationship orders_products
	fromColumn: Fact_Orders.product_id
	toColumn: Dim_Products.product_id

relationship orders_customers
	fromColumn: Fact_Orders.customer_id
	toColumn: Dim_Customers.customer_id

relationship orders_calendar
	fromColumn: Fact_Orders.order_date
	toColumn: Dim_Calendar.Date
'''

# ---------------- model ----------------
model = f'''model Model
	culture: en-US
	defaultPowerBIDataSourceVersion: powerBI_V3
	sourceQueryCulture: en-US

	annotation PBI_QueryOrder = ["Fact_Orders","Dim_Products","Dim_Customers","Dim_Calendar"]
	annotation PBIDesktopVersion = "2.159.1231.0 (24.11)"
'''

# ---------------- write files ----------------
with open(os.path.join(DEF, 'model.tmdl'), 'w', encoding='utf-8') as f:
    f.write(model)
with open(os.path.join(TBL, 'Fact_Orders.tmdl'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(fact_tbl)
with open(os.path.join(TBL, 'Dim_Products.tmdl'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(prod_tbl)
with open(os.path.join(TBL, 'Dim_Customers.tmdl'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(cust_tbl)
with open(os.path.join(TBL, 'Dim_Calendar.tmdl'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(cal_tbl)
with open(os.path.join(DEF, 'relationships.tmdl'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(rel)

# definition.pbism
pbism = '''{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
  "version": "4.1",
  "settings": {}
}
'''
with open(os.path.join(SM, 'definition.pbism'), 'w', encoding='utf-8') as f:
    f.write(pbism)

# ---------------- Report folder (legacy report.json format) ----------------
REPORT = os.path.join(HERE, 'EcomAnalytics.Report')
os.makedirs(REPORT, exist_ok=True)

definition_pbir = '''{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/1.0.0/schema.json",
  "version": "1.0",
  "datasetReference": {
    "byPath": {
      "path": "../EcomAnalytics.SemanticModel"
    }
  }
}
'''
with open(os.path.join(REPORT, 'definition.pbir'), 'w', encoding='utf-8') as f:
    f.write(definition_pbir)

import uuid as _uuid
page_name = str(_uuid.uuid4())

report_json = '''{
  "settings": {
    "useEnhancedTooltips": true
  },
  "themeCollection": {
    "baseTheme": {
      "name": "CY24SU10",
      "reportVersionAtImport": "3.0.0",
      "type": "SharedResources"
    }
  },
  "sections": [
    {
      "name": "%s",
      "displayName": "Page 1",
      "visualContainers": [],
      "config": "{}",
      "displayOption": 1,
      "height": 720.0,
      "width": 1280.0
    }
  ]
}
''' % page_name
with open(os.path.join(REPORT, 'report.json'), 'w', encoding='utf-8') as f:
    f.write(report_json)

# .pbip
pbip = '''{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
  "version": "1.0",
  "artifacts": [
    {
      "report": {
        "path": "EcomAnalytics.Report"
      }
    }
  ]
}
'''
with open(os.path.join(HERE, 'EcomAnalytics.pbip'), 'w', encoding='utf-8') as f:
    f.write(pbip)

print('PBIP written to', HERE)
for root, dirs, files in os.walk(HERE):
    dirs[:] = [d for d in dirs if d != 'data']
    for fn in sorted(files):
        p = os.path.join(root, fn)
        print('  ', os.path.relpath(p, HERE), f'({os.path.getsize(p)} bytes)')
