from pathlib import Path
import pandas as pd
import pytest
from openpyxl import load_workbook
from scripts.build_business_reporting_workbook import build

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def workbook(tmp_path_factory):
    dest = tmp_path_factory.mktemp('brw') / 'business_reporting.xlsx'
    stats = build(dest)
    return load_workbook(dest, read_only=True, data_only=True), stats, dest


def test_workbook_sheet_set_and_stats(workbook):
    wb, stats, _ = workbook
    expected = {'Read Me', 'Data', 'Customer Data', 'Executive KPIs', 'Sales Analysis',
                'Customer RFM', 'Retention', 'Forecast', 'Reconciliation'}
    assert set(wb.sheetnames) == expected
    assert stats['months'] == 36
    assert stats['categories'] == 5
    assert stats['segments'] == 3
    assert stats['revenue'] > 0


def test_executive_formulas_reference_data_sheet(workbook):
    wb, _, dest = workbook
    wbf = load_workbook(dest, data_only=False)
    assert wbf['Executive KPIs']['B3'].value == '=Data!B2'
    assert wbf['Executive KPIs']['D3'].value == '=Data!D2'


def test_reconciliation_status_formulas(workbook):
    wb, _, dest = workbook
    wbf = load_workbook(dest, data_only=False)
    rec = wbf['Reconciliation']
    # revenue row status formula present
    found = False
    for row in rec.iter_rows(min_row=3, max_row=rec.max_row):
        if row[3].value and isinstance(row[3].value, str) and row[3].value.startswith('=IF(ABS'):
            found = True
    assert found, 'reconciliation status formula missing'


def test_scenario_and_validation(workbook):
    wb, _, dest = workbook
    wbf = load_workbook(dest, data_only=False)
    fc = wbf['Forecast']
    # What-If growth cell exists with data validation
    assert fc['B' + str(fc.max_row - 3)].value == 0.05 or any(
        c.value == 0.05 for c in fc['B'])
    assert len(fc.data_validations.dataValidation) >= 1


def test_no_pii_exported(workbook):
    wb, _, _ = workbook
    cols = [str(c).lower() for c in next(wb['Customer Data'].values)]
    assert 'email' not in cols
    assert 'name' not in cols
