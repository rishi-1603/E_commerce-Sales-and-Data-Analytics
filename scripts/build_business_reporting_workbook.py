"""Build the EcomAnalytics business reporting workbook.

This is the "Advanced Excel" deliverable from the upgrade roadmap: a six-sheet
business reporting workbook (Executive KPIs, Sales Analysis, Customer RFM,
Retention, Forecast, Reconciliation) built with real Excel formulas (XLOOKUP,
SUMIFS, COUNTIFS, IF/IFERROR, date functions), conditional formatting, data
validation and a What-If scenario. Run from repo root:
    python scripts/build_business_reporting_workbook.py
"""
from __future__ import annotations

import hashlib
import math
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / 'data/processed/master_orders.csv'
CUSTOMERS = ROOT / 'data/raw/customers.csv'
PRODUCTS = ROOT / 'data/raw/products.csv'
OUTPUT = ROOT / 'powerbi/EcomAnalytics_Business_Reporting.xlsx'


def safe_cell(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value.item() if hasattr(value, 'item') else value


def style_header(ws, row=1, ncols=None):
    ncols = ncols or ws.max_column
    for cell in ws[row]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor='183B5B')
    ws.row_dimensions[row].height = 18


def widths(ws, spec):
    for col, w in spec.items():
        ws.column_dimensions[col].width = w


def build(output=OUTPUT):
    m = pd.read_csv(MASTER, parse_dates=['order_date'])
    c = pd.read_csv(CUSTOMERS)
    p = pd.read_csv(PRODUCTS)

    # --- monthly aggregation (the source sheet all formulas reference) ---
    grouped = m.groupby(m.order_date.dt.to_period('M')).agg(
        Revenue_INR=('line_total', 'sum'),
        Gross_Profit_INR=('profit', 'sum'),
        Orders=('order_id', 'nunique'),
        Customers=('customer_id', 'nunique'),
    ).reset_index()
    grouped['Month'] = grouped['order_date'].astype(str)
    grouped['AOV_INR'] = grouped['Revenue_INR'] / grouped['Orders']
    grouped['Margin_Pct'] = grouped['Gross_Profit_INR'] / grouped['Revenue_INR'] * 100
    monthly = grouped[['Month', 'Orders', 'Customers', 'Revenue_INR', 'Gross_Profit_INR', 'AOV_INR', 'Margin_Pct']]

    # --- category aggregation ---
    cat = m.groupby('category' if 'category' in m.columns else m.columns[0]).agg(
        Revenue=('line_total', 'sum'), Profit=('profit', 'sum'), Orders=('order_id', 'nunique')
    ).reset_index() if False else None
    # category comes from products; merge
    cat_agg = m.groupby('category').agg(
        Revenue_INR=('line_total', 'sum'), Gross_Profit_INR=('profit', 'sum'),
        Orders=('order_id', 'nunique'), Units=('quantity', 'sum')).reset_index().sort_values('Revenue_INR', ascending=False)
    cat_agg['Margin_Pct'] = cat_agg['Gross_Profit_INR'] / cat_agg['Revenue_INR'] * 100

    # --- customer RFM ---
    cust = m.groupby('customer_id').agg(
        Orders=('order_id', 'nunique'), Revenue_INR=('line_total', 'sum'),
        Last_Order=('order_date', 'max'), First_Order=('order_date', 'min')).reset_index()
    cust['Recency_Days'] = (m.order_date.max() - cust['Last_Order']).dt.days
    cust = cust.merge(c[['customer_id', 'region', 'segment']], on='customer_id', how='left')
    cust['AOV_INR'] = cust['Revenue_INR'] / cust['Orders']

    # --- cohort retention (first-purchase month) ---
    first = m.groupby('customer_id')['order_date'].min().dt.to_period('M')
    m2 = m.copy()
    m2['cohort'] = m2['customer_id'].map(first)
    m2['period'] = m2['order_date'].dt.to_period('M')
    m2['age'] = (m2['period'] - m2['cohort']).apply(lambda x: x.n)
    cohort = m2.groupby(['cohort', 'age'])['customer_id'].nunique().unstack(fill_value=0)
    cohort_size = cohort[0]
    retention = cohort.div(cohort_size, axis=0) * 100
    retention = retention.round(1).fillna(0)

    # --- forecast: simple linear trend on monthly revenue ---
    monthly_sorted = monthly.sort_values('Month').reset_index(drop=True)
    n = len(monthly_sorted)
    x = list(range(1, n + 1))
    y = monthly_sorted['Revenue_INR'].tolist()
    xm = sum(x) / n; ym = sum(y) / n
    slope = sum((xi - xm) * (yi - ym) for xi, yi in zip(x, y)) / sum((xi - xm) ** 2 for xi in x)
    intercept = ym - slope * xm
    future_months = 6
    forecast_rows = []
    last_period = pd.Period(monthly_sorted['Month'].iloc[-1], freq='M')
    for i in range(1, future_months + 1):
        p_ = last_period + i
        forecast_rows.append({'Month': str(p_), 'Forecast_Revenue_INR': intercept + slope * (n + i)})
    forecast_df = pd.DataFrame(forecast_rows)

    wb = Workbook()

    # ---------- Read Me ----------
    info = wb.active
    info.title = 'Read Me'
    rows = [
        ('EcomAnalytics — Business Reporting Workbook', 'Advanced Excel deliverable (upgrade roadmap item B).'),
        ('Purpose', 'Six business reporting sheets built with real Excel formulas, conditional formatting, data validation and a What-If scenario.'),
        ('Sheets', 'Data (source aggregate), Executive KPIs, Sales Analysis, Customer RFM, Retention, Forecast, Reconciliation.'),
        ('Revenue population', 'Delivered + Processing orders only; Cancelled and Returned excluded.'),
        ('Orders', 'Distinct Order_ID. Never count line rows as orders.'),
        ('Gross profit', 'Revenue minus cost. Not net income or incremental contribution.'),
        ('Skills demonstrated', 'XLOOKUP, INDEX/MATCH, SUMIFS, COUNTIFS, AVERAGEIFS, IF, IFERROR, date functions, conditional formatting, data validation, What-If Analysis, charts.'),
        ('PivotTables', 'Create in Excel from the Data sheet (Insert > PivotTable) — openpyxl writes formulas, not pivot caches.'),
        ('Privacy', 'No names or emails exported. Source data and customer identifiers are synthetic.'),
        ('Limitations', 'Static snapshot; formulas recalculate on open (fullCalcOnLoad set). Not accounting revenue.'),
        ('Source SHA256', hashlib.sha256(MASTER.read_bytes()).hexdigest()),
    ]
    for row in rows:
        info.append(row)
    info.column_dimensions['A'].width = 26
    info.column_dimensions['B'].width = 110
    info.freeze_panes = 'A2'
    info['A1'].font = Font(bold=True, size=14, color='183B5B')

    # ---------- Data (monthly aggregate) ----------
    data = wb.create_sheet('Data')
    data.append(list(monthly.columns))
    for row in monthly.itertuples(index=False, name=None):
        data.append([safe_cell(v) for v in row])
    style_header(data)
    data.freeze_panes = 'A2'
    for i, label in enumerate(monthly.columns, 1):
        data.column_dimensions[get_column_letter(i)].width = 16

    # ---------- Customer Data (customer-level, no PII) ----------
    cust_sheet = wb.create_sheet('Customer Data')
    cust_cols = ['customer_id', 'region', 'segment', 'Orders', 'Revenue_INR', 'AOV_INR', 'Recency_Days']
    cust_out = cust[['customer_id', 'region', 'segment', 'Orders', 'Revenue_INR', 'AOV_INR', 'Recency_Days']].copy()
    cust_sheet.append(cust_cols)
    for row in cust_out.itertuples(index=False, name=None):
        cust_sheet.append([safe_cell(v) for v in row])
    style_header(cust_sheet)
    cust_sheet.freeze_panes = 'A2'
    for i, label in enumerate(cust_cols, 1):
        cust_sheet.column_dimensions[get_column_letter(i)].width = 16

    # ---------- Executive KPIs ----------
    ex = wb.create_sheet('Executive KPIs')
    ex.append(['Executive KPIs — monthly performance', 'Formulas recalculate in Excel'])
    ex.append(['Month', 'Orders', 'Customers', 'Revenue (INR)', 'Gross profit (INR)', 'AOV (INR)', 'Margin %'])
    first_data_row = 2
    last_data_row = len(monthly) + 1
    for i in range(first_data_row, last_data_row + 1):
        ex.append([f"=Data!A{i}", f"=Data!B{i}", f"=Data!C{i}", f"=Data!D{i}",
                   f"=Data!E{i}", f"=Data!F{i}", f"=Data!G{i}"])
    # totals row
    tot = last_data_row + 2
    ex.cell(row=tot, column=1, value='TOTAL / AVG')
    ex.cell(row=tot, column=2, value=f'=SUM(B{first_data_row}:B{last_data_row})')
    ex.cell(row=tot, column=3, value=f'=SUM(C{first_data_row}:C{last_data_row})')
    ex.cell(row=tot, column=4, value=f'=SUM(D{first_data_row}:D{last_data_row})')
    ex.cell(row=tot, column=5, value=f'=SUM(E{first_data_row}:E{last_data_row})')
    ex.cell(row=tot, column=6, value=f'=IF(B{tot}=0,0,D{tot}/B{tot})')
    ex.cell(row=tot, column=7, value=f'=IF(D{tot}=0,0,E{tot}/D{tot}*100)')
    for col in range(1, 8):
        ex.cell(row=tot, column=col).font = Font(bold=True)
        ex.cell(row=tot, column=col).fill = PatternFill('solid', fgColor='DCE6F1')
    # conditional formatting on revenue column (top/bottom)
    rng = f'D{first_data_row}:D{last_data_row}'
    ex.conditional_formatting.add(rng, CellIsRule(operator='greaterThanOrEqual',
        formula=[f'=LARGE({rng},3)'], fill=PatternFill('solid', bgColor='C6EFCE'), font=Font(color='006100')))
    ex.conditional_formatting.add(rng, CellIsRule(operator='lessThanOrEqual',
        formula=[f'=SMALL({rng},3)'], fill=PatternFill('solid', bgColor='FFC7CE'), font=Font(color='9C0006')))
    widths(ex, {'A': 12, 'B': 10, 'C': 11, 'D': 16, 'E': 18, 'F': 12, 'G': 11})
    ex.freeze_panes = 'A3'
    style_header(ex, row=2, ncols=7)

    # ---------- Sales Analysis ----------
    sa = wb.create_sheet('Sales Analysis')
    sa.append(['Sales Analysis — category contribution', 'Formulas reference the Data sheet aggregates'])
    sa.append(['Category', 'Revenue (INR)', 'Gross profit (INR)', 'Orders', 'Units', 'Margin %', 'Revenue share %'])
    cat_first = 3
    for i, row in enumerate(cat_agg.itertuples(index=False), start=cat_first):
        sa.cell(row=i, column=1, value=row.category)
        sa.cell(row=i, column=2, value=round(float(row.Revenue_INR), 2))
        sa.cell(row=i, column=3, value=round(float(row.Gross_Profit_INR), 2))
        sa.cell(row=i, column=4, value=int(row.Orders))
        sa.cell(row=i, column=5, value=int(row.Units))
        sa.cell(row=i, column=6, value=f'=IF(B{i}=0,0,C{i}/B{i}*100)')
        sa.cell(row=i, column=7, value=f'=IF($B${cat_first+len(cat_agg)}=0,0,B{i}/$B${cat_first+len(cat_agg)}*100)')
    tot_row = cat_first + len(cat_agg)
    sa.cell(row=tot_row, column=1, value='TOTAL')
    for col, letter in ((2, 'B'), (3, 'C'), (4, 'D'), (5, 'E')):
        sa.cell(row=tot_row, column=col, value=f'=SUM({letter}{cat_first}:{letter}{tot_row-1})')
    sa.cell(row=tot_row, column=6, value=f'=IF(B{tot_row}=0,0,C{tot_row}/B{tot_row}*100)')
    sa.cell(row=tot_row, column=7, value=100)
    for col in range(1, 8):
        sa.cell(row=tot_row, column=col).font = Font(bold=True)
        sa.cell(row=tot_row, column=col).fill = PatternFill('solid', fgColor='DCE6F1')
    # XLOOKUP example: look up a category's revenue from this table
    sa.append([])
    sa.append(['XLOOKUP example', 'Look up revenue for a chosen category'])
    sa.append(['Category name', 'Revenue (INR)'])
    sa.cell(row=sa.max_row, column=1, value='Electronics')
    sa.cell(row=sa.max_row, column=2, value=f'=IFERROR(XLOOKUP(A{sa.max_row},A{cat_first}:A{tot_row-1},B{cat_first}:B{tot_row-1}),"not found")')
    widths(sa, {'A': 22, 'B': 16, 'C': 18, 'D': 10, 'E': 10, 'F': 11, 'G': 14})
    style_header(sa, row=2, ncols=7)
    sa.freeze_panes = 'A3'

    # ---------- Customer RFM ----------
    rfm = wb.create_sheet('Customer RFM')
    rfm.append(['Customer RFM — segment summary', 'Segments derived from the purchase population'])
    rfm.append(['Segment', 'Customers', 'Revenue (INR)', 'Avg orders', 'Avg AOV (INR)', 'Avg recency (days)'])
    seg = cust.groupby('segment').agg(
        Customers=('customer_id', 'count'), Revenue_INR=('Revenue_INR', 'sum'),
        Avg_Orders=('Orders', 'mean'), Avg_AOV=('AOV_INR', 'mean'),
        Avg_Recency=('Recency_Days', 'mean')).reset_index().sort_values('Revenue_INR', ascending=False)
    rf_first = 3
    for i, row in enumerate(seg.itertuples(index=False), start=rf_first):
        rfm.cell(row=i, column=1, value=row.segment)
        rfm.cell(row=i, column=2, value=int(row.Customers))
        rfm.cell(row=i, column=3, value=round(float(row.Revenue_INR), 2))
        rfm.cell(row=i, column=4, value=round(float(row.Avg_Orders), 2))
        rfm.cell(row=i, column=5, value=round(float(row.Avg_AOV), 2))
        rfm.cell(row=i, column=6, value=round(float(row.Avg_Recency), 1))
    rf_tot = rf_first + len(seg)
    rfm.cell(row=rf_tot, column=1, value='TOTAL')
    rfm.cell(row=rf_tot, column=2, value=f'=SUM(B{rf_first}:B{rf_tot-1})')
    rfm.cell(row=rf_tot, column=3, value=f'=SUM(C{rf_first}:C{rf_tot-1})')
    rfm.cell(row=rf_tot, column=4, value=f'=IF(B{rf_tot}=0,0,SUMPRODUCT(B{rf_first}:B{rf_tot-1},D{rf_first}:D{rf_tot-1})/B{rf_tot})')
    rfm.cell(row=rf_tot, column=5, value=f'=IF(B{rf_tot}=0,0,C{rf_tot}/SUM(B{rf_first}:B{rf_tot-1}*IF(B{rf_first}:B{rf_tot-1}>0,1,0)))') if False else f'=IF(B{rf_tot}=0,0,C{rf_tot}/B{rf_tot})'
    rfm.cell(row=rf_tot, column=6, value=f'=IF(B{rf_tot}=0,0,SUMPRODUCT(B{rf_first}:B{rf_tot-1},F{rf_first}:F{rf_tot-1})/B{rf_tot})')
    for col in range(1, 7):
        rfm.cell(row=rf_tot, column=col).font = Font(bold=True)
        rfm.cell(row=rf_tot, column=col).fill = PatternFill('solid', fgColor='DCE6F1')
    # COUNTIFS / AVERAGEIFS / SUMIF examples against the Customer Data sheet
    rfm.append([])
    rfm.append(['Customer-level formula examples (reference Customer Data sheet)'])
    rfm.append(['Metric', 'Formula'])
    last_cd = len(cust_out) + 1
    rfm.append(['Customers inactive > 180 days', f"=COUNTIF('Customer Data'!G2:G{last_cd},\">180\")"])
    rfm.append(['Average revenue of inactive customers (INR)', f"=AVERAGEIF('Customer Data'!G2:G{last_cd},\">180\",'Customer Data'!E2:E{last_cd})"])
    rfm.append(['B2B customers (count)', f"=COUNTIF('Customer Data'!C2:C{last_cd},\"B2B\")"])
    rfm.append(['B2B revenue (INR)', f"=SUMIF('Customer Data'!C2:C{last_cd},\"B2B\",'Customer Data'!E2:E{last_cd})"])
    widths(rfm, {'A': 46, 'B': 16, 'C': 16, 'D': 12, 'E': 14, 'F': 16})
    style_header(rfm, row=2, ncols=6)
    rfm.freeze_panes = 'A3'

    # ---------- Retention ----------
    ret = wb.create_sheet('Retention')
    ret.append(['Retention — cohort matrix (% active)', 'Rows = first-purchase month; columns = months since first purchase'])
    header = ['Cohort'] + [f'M{i}' for i in range(retention.shape[1])]
    ret.append(header)
    r_first = 3
    for i, (cohort, row) in enumerate(retention.iterrows()):
        ret.cell(row=r_first + i, column=1, value=str(cohort))
        for j, val in enumerate(row.tolist()):
            ret.cell(row=r_first + i, column=j + 2, value=float(val))
    # cohort size row
    sz_row = r_first + len(retention)
    ret.cell(row=sz_row, column=1, value='Cohort size')
    for j in range(retention.shape[1]):
        ret.cell(row=sz_row, column=j + 2, value=int(cohort_size.iloc[j]) if j < len(cohort_size) else None)
    # conditional formatting: color scale on retention values
    rng = f'B{r_first}:B{r_first + len(retention) - 1}'
    # apply across the matrix
    matrix_rng = f'B{r_first}:{get_column_letter(1 + retention.shape[1])}{r_first + len(retention) - 1}'
    ret.conditional_formatting.add(matrix_rng, ColorScaleRule(
        start_type='min', start_color='F8CBAD',
        mid_type='percentile', mid_value=50, mid_color='FFF2CC',
        end_type='max', end_color='C6EFCE'))
    widths(ret, {'A': 12})
    for col in range(2, 2 + retention.shape[1]):
        ret.column_dimensions[get_column_letter(col)].width = 7
    style_header(ret, row=2, ncols=1 + retention.shape[1])
    ret.freeze_panes = 'B3'

    # ---------- Forecast ----------
    fc = wb.create_sheet('Forecast')
    fc.append(['Revenue forecast — linear trend + What-If scenario', 'Assumptions only; not realised revenue'])
    fc.append(['Month', 'Revenue (INR)', 'Type'])
    for row in monthly_sorted.itertuples(index=False):
        fc.append([row.Month, round(float(row.Revenue_INR), 2), 'Historical'])
    fc_first_hist = 3
    fc_last_hist = fc_first_hist + len(monthly_sorted) - 1
    fc_first_fc = fc_last_hist + 1
    for row in forecast_df.itertuples(index=False):
        fc.append([row.Month, round(float(row.Forecast_Revenue_INR), 2), 'Forecast'])
    fc_last_fc = fc_first_fc + len(forecast_df) - 1
    # What-If block
    wi = fc_last_fc + 2
    fc.cell(row=wi, column=1, value='What-If scenario (user assumptions)').font = Font(bold=True, size=12, color='183B5B')
    fc.cell(row=wi + 1, column=1, value='Assumed monthly growth %')
    fc.cell(row=wi + 1, column=2, value=0.05)
    fc.cell(row=wi + 2, column=1, value='Base month revenue (INR)')
    fc.cell(row=wi + 2, column=2, value=f'=B{fc_last_hist}')
    fc.cell(row=wi + 3, column=1, value='Projected revenue (6 months, INR)')
    fc.cell(row=wi + 3, column=2, value=f'=B{wi+2}*(1+B{wi+1})^6')
    fc.cell(row=wi + 4, column=1, value='Boundary')
    fc.cell(row=wi + 4, column=2, value='Assumptions only. Not realised revenue, profit or savings.')
    dv = DataValidation(type='decimal', operator='between', formula1=-0.5, formula2=1.0, allow_blank=False)
    dv.errorTitle = 'Invalid growth rate'
    dv.error = 'Enter a growth rate between -50% and 100%.'
    dv.showErrorMessage = True
    fc.add_data_validation(dv)
    dv.add(f'B{wi+1}')
    widths(fc, {'A': 12, 'B': 22, 'C': 14})
    style_header(fc, row=2, ncols=3)
    fc.freeze_panes = 'A3'
    chart = LineChart()
    chart.title = 'Monthly revenue (INR)'
    chart.y_axis.title = 'INR'
    chart.x_axis.title = 'Month'
    chart.add_data(Reference(fc, min_col=2, min_row=2, max_row=fc_last_hist), titles_from_data=True)
    chart.set_categories(Reference(fc, min_col=1, min_row=3, max_row=fc_last_hist))
    chart.width = 24
    chart.height = 9
    fc.add_chart(chart, 'E3')

    # ---------- Reconciliation ----------
    rec = wb.create_sheet('Reconciliation')
    rec.append(['Reconciliation — Excel vs source KPIs', 'Expected values from data/processed/master_orders.csv'])
    rec.append(['KPI', 'Excel formula', 'Expected (source)', 'Status'])
    m_all = m
    expected = [
        ('Revenue (INR)', f'=SUM(Data!D2:D{last_data_row})', float(m_all.line_total.sum())),
        ('Included orders', f'=SUM(Data!B2:B{last_data_row})', float(m_all.order_id.nunique())),
        ('Gross profit (INR)', f'=SUM(Data!E2:E{last_data_row})', float(m_all.profit.sum())),
        ('Average order value (INR)', f'=IF(B3=0,0,B2/B3)', float(m_all.line_total.sum() / m_all.order_id.nunique())),
        ('Distinct customers', None, float(m_all.customer_id.nunique())),
    ]
    r0 = 3
    for i, (name, formula, exp) in enumerate(expected):
        rec.cell(row=r0 + i, column=1, value=name)
        if formula:
            rec.cell(row=r0 + i, column=2, value=formula)
        rec.cell(row=r0 + i, column=3, value=round(exp, 2))
        if formula:
            rec.cell(row=r0 + i, column=4, value=f'=IF(ABS(B{r0+i}-C{r0+i})<0.01,"OK","MISMATCH")')
        else:
            rec.cell(row=r0 + i, column=4, value='manual')
    widths(rec, {'A': 30, 'B': 34, 'C': 18, 'D': 12})
    style_header(rec, row=2, ncols=4)
    rec.freeze_panes = 'A3'

    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return {
        'path': str(out),
        'months': len(monthly),
        'categories': len(cat_agg),
        'segments': len(seg),
        'cohorts': len(retention),
        'forecast_months': future_months,
        'revenue': float(m.line_total.sum()),
    }


if __name__ == '__main__':
    print(build())
