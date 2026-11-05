"""Build a synthetic Power BI-ready Excel data-model companion.

This is an .xlsx data workbook, NOT a Power BI .pbix report. No personal
names/email are exported. Run from repo root: python scripts/build_excel_companion.py
"""
from __future__ import annotations

import hashlib
import math
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / 'data/processed/master_orders.csv'
CUSTOMERS = ROOT / 'data/raw/customers.csv'
PRODUCTS = ROOT / 'data/raw/products.csv'
OUTPUT = ROOT / 'powerbi/Ecommerce_BI_Companion.xlsx'


def safe_cell(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value.item() if hasattr(value, 'item') else value


def add_table(workbook, name, frame):
    sheet = workbook.create_sheet(name)
    sheet.append(list(frame.columns))
    for row in frame.itertuples(index=False, name=None):
        sheet.append([safe_cell(v) for v in row])
    sheet.freeze_panes = 'A2'
    tab = Table(displayName=name, ref=f'A1:{get_column_letter(len(frame.columns))}{len(frame)+1}')
    tab.tableStyleInfo = TableStyleInfo(name='TableStyleMedium2', showRowStripes=True)
    sheet.add_table(tab)
    for cell in sheet[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor='183B5B')
    for i, label in enumerate(frame.columns, 1):
        sheet.column_dimensions[get_column_letter(i)].width = min(28, max(14, len(label) + 4))
    return sheet


def build(output=OUTPUT):
    m = pd.read_csv(MASTER, parse_dates=['order_date'])
    c = pd.read_csv(CUSTOMERS)
    p = pd.read_csv(PRODUCTS)
    required = ['item_id', 'order_id', 'customer_id', 'product_id', 'order_date',
                'status', 'quantity', 'line_total', 'cost_total', 'profit']
    if not set(required).issubset(m.columns) or m[required].isna().any().any():
        raise ValueError('Master order lines have missing required data.')
    if not m.item_id.is_unique or not c.customer_id.is_unique or not p.product_id.is_unique:
        raise ValueError('Fact line or dimension keys are duplicated.')
    if not m.customer_id.isin(c.customer_id).all() or not m.product_id.isin(p.product_id).all():
        raise ValueError('Fact-to-dimension references do not reconcile.')
    if not m.status.isin(['Delivered', 'Processing']).all():
        raise ValueError('The workbook expects the project revenue population only.')
    for col in ['quantity', 'line_total', 'cost_total', 'profit']:
        if not pd.to_numeric(m[col], errors='coerce').map(math.isfinite).all():
            raise ValueError(f'{col} must be finite.')
    if not ((m.line_total - m.cost_total - m.profit).abs() < 0.001).all():
        raise ValueError('Line profit does not reconcile with revenue minus cost.')
    fact = m[required].rename(columns={'item_id':'Item_ID', 'order_id':'Order_ID', 'customer_id':'Customer_ID',
        'product_id':'Product_ID', 'order_date':'Order_Date', 'status':'Status', 'quantity':'Quantity',
        'line_total':'Revenue_INR', 'cost_total':'Cost_INR', 'profit':'Gross_Profit_INR'})
    customers = c[['customer_id', 'region', 'segment', 'acquisition_channel']].rename(columns={
        'customer_id':'Customer_ID', 'region':'Region', 'segment':'Segment', 'acquisition_channel':'Acquisition_Channel'})
    products = p[['product_id','product_name','category','subcategory']].rename(columns={
        'product_id':'Product_ID','product_name':'Product_Name','category':'Category','subcategory':'Subcategory'})
    dates = pd.DataFrame({'Date':pd.date_range(m.order_date.min().normalize(),m.order_date.max().normalize(),freq='D')})
    dates['Year'] = dates.Date.dt.year
    dates['Month_Number'] = dates.Date.dt.month
    dates['Year_Month'] = dates.Date.dt.strftime('%Y-%m')
    grouped = m.groupby(m.order_date.dt.to_period('M')).agg(
        Revenue_INR=('line_total','sum'), Gross_Profit_INR=('profit','sum'), Orders=('order_id','nunique')).reset_index()
    grouped['Month'] = grouped['order_date'].astype(str)
    grouped['AOV_INR'] = grouped['Revenue_INR'] / grouped['Orders']
    monthly = grouped[['Month','Orders','Revenue_INR','Gross_Profit_INR','AOV_INR']]
    wb = Workbook()
    info = wb.active; info.title = 'Read Me'
    rows = [
        ('E-Commerce BI companion', 'Synthetic sample; not a Power BI .pbix report.'),
        ('Fact grain', 'One valid order line. Delivered and Processing included; Cancelled and Returned excluded.'),
        ('Revenue', 'Sum FactSales[Revenue_INR]; INR, rounded display. Not accounting revenue.'),
        ('Orders', 'Distinct Order_ID in FactSales. Never count line rows as orders.'),
        ('Gross profit', 'Revenue_INR minus Cost_INR; not net income or incremental contribution.'),
        ('Relationships', 'FactSales Order_Date -> DimDate Date; Customer_ID -> DimCustomer; Product_ID -> DimProduct, many-to-one.'),
        ('Monthly checks', 'MonthlyCheck is an independently prepared aggregate for reconciliation; do not join it to FactSales.'),
        ('Privacy', 'No names or emails exported. Source data and customer identifiers are synthetic.'),
        ('Limitations', 'Static snapshot; no actual post-action outcomes, Power BI service deployment or validated causal effect.'),
        ('Source SHA256', hashlib.sha256(MASTER.read_bytes()).hexdigest()),
    ]
    for row in rows: info.append(row)
    info.column_dimensions['A'].width=25; info.column_dimensions['B'].width=105
    info.freeze_panes='A2'
    info['A1'].font=Font(bold=True,size=16,color='183B5B')
    add_table(wb,'FactSales',fact)
    add_table(wb,'DimCustomer',customers)
    add_table(wb,'DimProduct',products)
    add_table(wb,'DimDate',dates)
    add_table(wb,'MonthlyCheck',monthly)
    for name, col in [('FactSales','E'),('DimDate','A')]:
        for row in wb[name].iter_rows(min_row=2,min_col=ord(col)-64,max_col=ord(col)-64):
            row[0].number_format='yyyy-mm-dd'
    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
    out=Path(output);out.parent.mkdir(parents=True,exist_ok=True);wb.save(out)
    return {'path':str(out), 'order_lines':len(fact),'customers':len(customers),
            'products':len(products),'months':len(monthly),'revenue':float(m.line_total.sum())}


if __name__ == '__main__':
    print(build())
