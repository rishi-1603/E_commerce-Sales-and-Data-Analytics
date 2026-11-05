from pathlib import Path
import pandas as pd
import pytest
from openpyxl import load_workbook
from scripts.build_excel_companion import build

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def workbook(tmp_path_factory):
    dest=tmp_path_factory.mktemp('excel')/'companion.xlsx'
    stats=build(dest)
    return load_workbook(dest, read_only=True, data_only=True), stats


def test_workbook_contains_real_data_not_a_pbix_claim(workbook):
    wb, stats=workbook
    assert set(wb.sheetnames)=={'Read Me','FactSales','DimCustomer','DimProduct','DimDate','MonthlyCheck'}
    assert stats['order_lines']==21066 and stats['customers']==2000 and stats['products']==150
    assert 'not a Power BI .pbix' in wb['Read Me']['B1'].value


def test_fact_dimension_keys_and_reconciliation(workbook):
    wb, stats=workbook
    m=pd.read_csv(ROOT/'data/processed/master_orders.csv')
    rows=list(wb['MonthlyCheck'].values)
    assert len(rows)-1==stats['months']
    assert sum(row[2] for row in rows[1:])==pytest.approx(m.line_total.sum(), abs=.01)
    assert stats['revenue']==pytest.approx(m.line_total.sum(),abs=.001)
    assert wb['FactSales'].max_row==len(m)+1
    assert wb['DimCustomer'].max_row==2001
    assert wb['DimProduct'].max_row==151
    assert 'email' not in [x.lower() for x in next(wb['DimCustomer'].values)]


def test_excel_text_formula_injection_is_escaped():
    from scripts.build_excel_companion import safe_cell
    for text in ['=1+1', '+123', '-cmd', '@formula']:
        assert safe_cell(text).startswith("'")
    assert safe_cell('safe text')=='safe text'


def test_committed_workbook_monthly_checks_match_current_source():
    wb = load_workbook(ROOT/'powerbi/Ecommerce_BI_Companion.xlsx', read_only=True, data_only=True)
    rows = list(wb['MonthlyCheck'].values)
    frame = pd.read_csv(ROOT/'data/processed/master_orders.csv', parse_dates=['order_date'])
    expected = frame.groupby(frame.order_date.dt.strftime('%Y-%m')).agg(
        orders=('order_id','nunique'), revenue=('line_total','sum'), gross_profit=('profit','sum'))
    assert len(rows) - 1 == len(expected)
    for month, orders, revenue, profit, aov in rows[1:]:
        row = expected.loc[month]
        assert orders == row.orders
        assert revenue == pytest.approx(row.revenue, abs=.005)
        assert profit == pytest.approx(row.gross_profit, abs=.005)
        assert aov == pytest.approx(row.revenue / row.orders, abs=.005)
