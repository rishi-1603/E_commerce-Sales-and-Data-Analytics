"""Build a reconciled, descriptive product price/volume/mix bridge.

It assigns the price/quantity interaction to the realized-price term, and
isolates products present in only one period. It does not establish causation.
Run from the repo root to refresh both static dashboard data copies.
"""
from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / 'data/processed/master_orders.csv'


def load_source():
    return pd.read_csv(MASTER)


def analyze(frame: pd.DataFrame) -> dict:
    columns = ['item_id', 'order_id', 'product_id', 'order_date', 'status', 'quantity', 'line_total']
    if not isinstance(frame, pd.DataFrame) or not set(columns).issubset(frame.columns):
        raise ValueError('Required order-line fields are missing.')
    data = frame[columns].copy()
    if data.empty or data.isna().any().any() or data.item_id.duplicated().any():
        raise ValueError('Order lines must be present, complete and unique.')
    for col in ['item_id', 'order_id', 'product_id']:
        if not data[col].map(lambda value: isinstance(value, str) and bool(value.strip())).all():
            raise ValueError('Order-line identifiers must be non-empty text.')
    if not data.status.isin(['Delivered', 'Processing']).all():
        raise ValueError('The revenue population must contain Delivered + Processing only.')
    for col in ['quantity', 'line_total']:
        if data[col].map(lambda value: isinstance(value, bool)).any():
            raise ValueError('Boolean values are not valid quantities or revenue.')
        data[col] = pd.to_numeric(data[col], errors='coerce')
        if data[col].isna().any() or not data[col].map(math.isfinite).all():
            raise ValueError('Quantity and revenue must be finite.')
    if (data.quantity <= 0).any() or (data.quantity.mod(1) != 0).any() or (data.line_total < 0).any():
        raise ValueError('Quantity must be a positive whole number and revenue nonnegative.')
    dates = pd.to_datetime(data.order_date, errors='coerce')
    if dates.isna().any():
        raise ValueError('Every order line needs a valid date.')
    data['period'] = dates.dt.strftime('%Y-%m')
    periods = sorted(data.period.unique())
    if len(periods) < 2:
        raise ValueError('At least two observed months are needed.')
    previous, current = periods[-2:]
    data = data[data.period.isin([previous, current])].copy()
    groups = data.groupby(['period', 'product_id'], as_index=False).agg(quantity=('quantity', 'sum'), revenue=('line_total', 'sum'))
    # Independently execute fixed SQLite aggregation; SQL sees only these two periods.
    with sqlite3.connect(':memory:') as connection:
        data[['period', 'product_id', 'quantity', 'line_total']].to_sql('lines', connection, index=False)
        connection.execute('PRAGMA query_only = ON')
        sql = pd.read_sql_query('SELECT period, product_id, SUM(quantity) AS quantity, SUM(line_total) AS revenue FROM lines GROUP BY period, product_id ORDER BY period, product_id', connection)
    left = groups.sort_values(['period', 'product_id']).reset_index(drop=True)
    try:
        pd.testing.assert_frame_equal(left, sql, check_dtype=False, atol=1e-7, rtol=1e-10)
    except AssertionError:
        raise ValueError('SQL/pandas product aggregation does not reconcile.') from None
    by_prev = groups[groups.period.eq(previous)].set_index('product_id')
    by_curr = groups[groups.period.eq(current)].set_index('product_id')
    common = by_prev.index.intersection(by_curr.index)
    entered = by_curr.index.difference(by_prev.index)
    exited = by_prev.index.difference(by_curr.index)
    r0, r1 = float(by_prev.revenue.sum()), float(by_curr.revenue.sum())
    entry = float(by_curr.loc[entered, 'revenue'].sum())
    exit_effect = -float(by_prev.loc[exited, 'revenue'].sum())
    if len(common):
        a, b = by_prev.loc[common], by_curr.loc[common]
        q0, q1 = float(a.quantity.sum()), float(b.quantity.sum())
        p0, p1 = a.revenue / a.quantity, b.revenue / b.quantity
        average_prior = float(a.revenue.sum()) / q0
        volume = (q1-q0)*average_prior
        mix = q1 * (float((b.quantity / q1 * p0).sum()) - average_prior)
        price = float((b.quantity * (p1-p0)).sum())
        status = 'available'
    else:
        volume = mix = price = 0.0
        status = 'no_common_products'
    components = {'volume_inr': volume, 'mix_inr': mix, 'realized_price_inr': price,
                  'entry_inr': entry, 'exit_inr': exit_effect}
    residual = (r1-r0) - sum(components.values())
    if abs(residual) > 0.0001:
        raise ValueError('Price/volume/mix bridge does not reconcile.')
    return {
        'schema_version': 1, 'previous_period': previous, 'current_period': current,
        'previous_revenue_inr': r0, 'current_revenue_inr': r1, 'revenue_change_inr': r1-r0,
        'common_products': len(common), 'entered_products': len(entered), 'exited_products': len(exited),
        'components': components, 'common_product_bridge_status': status,
        'reconciliation': {'sql_pandas': 'PASS', 'sql_group_rows': len(sql), 'bridge_residual_inr': residual},
        'limitations': 'Synthetic data; realized unit price is revenue divided by units, including discount/mix effects within a product. This path-dependent arithmetic bridge is descriptive, not causal. New/exited products are separate. Observed calendar months are not certified complete.',
    }


def main():
    output = 'globalThis.BVDIE_PVM = ' + json.dumps(analyze(load_source()), ensure_ascii=False, allow_nan=False, sort_keys=True) + ';\n'
    for path in [ROOT / 'dashboard/revenue_pvm_data.js', ROOT / 'revenue_pvm_data.js']:
        path.write_text(output, encoding='utf-8')
    print('Wrote reconciled revenue bridge to both dashboard data copies.')


if __name__ == '__main__':
    main()
