import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / 'dashboard/decision_engine.js'


def node(expression):
    code = f"const e=require({json.dumps(str(JS))}); console.log(JSON.stringify({expression}));"
    result=subprocess.run(['node','-e',code],capture_output=True,text=True,check=True)
    return json.loads(result.stdout)


def test_revenue_bridge_reconciles_exactly():
    bridge=node('e.revenueBridge(1000, 1500, 10, 12)')
    assert bridge['volume_effect'] == pytest.approx(200)
    assert bridge['basket_effect'] == pytest.approx(300)
    assert bridge['total_change'] == pytest.approx(500)
    assert bridge['volume_effect'] + bridge['basket_effect'] == pytest.approx(500)


def test_dashboard_latest_month_values_reconcile_with_master():
    master=pd.read_csv(ROOT/'data/processed/master_orders.csv',parse_dates=['order_date'])
    grouped=master.groupby(master.order_date.dt.to_period('M')).agg(revenue=('line_total','sum'),orders=('order_id','nunique'))
    older,newer=grouped.iloc[-2],grouped.iloc[-1]
    bridge=node(f"e.revenueBridge({older.revenue},{newer.revenue},{older.orders},{newer.orders})")
    assert bridge['total_change'] == pytest.approx(newer.revenue-older.revenue)
    assert bridge['volume_effect']+bridge['basket_effect'] == pytest.approx(bridge['total_change'])


def test_scenario_distinguishes_assumptions_and_break_even():
    result=node('e.scenario(100, 200, 5000)')
    assert result['base']['net_inr']==15000
    assert result['low']['net_inr']==5000
    assert result['high']['net_inr']==25000
    assert result['break_even_incremental_orders']==25


def test_zero_contribution_has_no_finite_break_even():
    assert node('e.scenario(100, 0, 5000)')['break_even_incremental_orders'] is None


def test_invalid_numbers_are_refused():
    assert node('(()=>{try{e.scenario(-1, 2, 3);return false}catch(e){return true}})()')
    assert node('(()=>{try{e.scenario(1, Infinity, 3);return false}catch(e){return true}})()')
    assert node('(()=>{try{e.revenueBridge(1,2,0,1);return false}catch(e){return true}})()')


def test_record_preserves_unobserved_status_and_html_safe_input():
    r=node("e.makeRecord({previous:1000,current:1500,previousOrders:10,currentOrders:12,incrementalOrders:100,contributionPerOrder:200,campaignCost:5000,action:'<img src=x onerror=alert(1)>',kpi:'Incremental orders'})")
    assert r['decision']['status']=='proposed'
    assert r['observed_outcome'] is None
    assert r['project']=='ecommerce'
    assert 'modeled' in r['limitations'].lower()


def test_ui_assets_and_all_served_copies_remain_in_sync():
    assert (ROOT/'dashboard/decision_engine.js').read_bytes() == (ROOT/'decision_engine.js').read_bytes()
    html=(ROOT/'dashboard/dashboard.html').read_text(encoding='utf-8')
    assert 'id="bv-form"' in html and 'src="decision_engine.js"' in html
    for path in ['dashboard/index.html','index.html','dashboard.html']:
        assert (ROOT/path).read_text(encoding='utf-8')==html


def test_bridge_uses_embedded_display_totals_without_silent_mismatch():
    import re
    html=(ROOT/'dashboard/dashboard.html').read_text(encoding='utf8')
    text=re.search(r'const DATA = (\{.*?\});\s*\n\s*const C',html,re.S).group(1)
    text=re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_ ]*?)\s*:',r'\1"\2":',text).replace("'",'"')
    text=re.sub(r',\s*([\]}])',r'\1',text)
    mom=json.loads(text)['decision']['mom']
    data=pd.read_csv(ROOT/'data/processed/master_orders.csv',parse_dates=['order_date'])
    monthly=data.groupby(data.order_date.dt.to_period('M')).agg(revenue=('line_total','sum'),orders=('order_id','nunique'))
    for offset in (0,1):
        row=monthly.iloc[-2+offset]
        assert mom['revenue'][offset] == pytest.approx(row.revenue, abs=.51)
        assert mom['orders'][offset] == int(row.orders)


def test_revenue_bridge_sql_and_dashboard_reconcile():
    import sqlite3
    import re
    frame=pd.read_csv(ROOT/'data/processed/master_orders.csv',usecols=['order_date','order_id','line_total'])
    with sqlite3.connect(':memory:') as db:
        frame.to_sql('lines',db,index=False)
        rows=db.execute("SELECT substr(order_date,1,7), sum(line_total), count(distinct order_id) FROM lines GROUP BY 1 ORDER BY 1 DESC LIMIT 2").fetchall()
    html=(ROOT/'dashboard/dashboard.html').read_text(encoding='utf8')
    text=re.search(r'const DATA = (\{.*?\});\s*\n\s*const C',html,re.S).group(1)
    text=re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_ ]*?)\s*:',r'\1"\2":',text).replace("'",'"')
    text=re.sub(r',\s*([\]}])',r'\1',text)
    mom=json.loads(text)['decision']['mom']
    assert [x[0] for x in rows]==[mom['label'],mom['prev_label']]
    assert [x[2] for x in rows]==list(reversed(mom['orders']))
    for sql_row,dash_total in zip(rows,reversed(mom['revenue'])):
        assert sql_row[1] == pytest.approx(dash_total,abs=.51)


def test_pricing_renderer_is_inside_inline_dashboard_script():
    html=(ROOT/'dashboard/dashboard.html').read_text(encoding='utf8')
    inline_start=html.index('<script>\nconst GRD')
    inline_end=html.index('</script>',inline_start)
    marker=html.index('// PRICING_JS_START')
    external=html.index('<script src="decision_engine.js"></script>')
    assert inline_start < marker < inline_end < external


def test_nested_dashboard_alias_resolves_decision_asset_in_vercel_config():
    config=json.loads((ROOT/'dashboard/vercel.json').read_text(encoding='utf-8'))
    routes={rule['source']:rule['destination'] for rule in config['rewrites']}
    assert routes['/dashboard/decision_engine.js']=='/decision_engine.js'
    assert (ROOT/'dashboard/decision_engine.js').is_file()
