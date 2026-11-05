from pathlib import Path
import pandas as pd
import pytest
from scripts.build_revenue_pvm import analyze, load_source

ROOT=Path(__file__).resolve().parents[1]


def fixture():
 return pd.DataFrame([
  {'item_id':'a0','order_id':'o1','product_id':'A','order_date':'2024-01-10','status':'Delivered','quantity':10,'line_total':100.0},
  {'item_id':'b0','order_id':'o2','product_id':'B','order_date':'2024-01-11','status':'Delivered','quantity':10,'line_total':200.0},
  {'item_id':'a1','order_id':'o3','product_id':'A','order_date':'2024-02-10','status':'Delivered','quantity':15,'line_total':180.0},
  {'item_id':'c1','order_id':'o4','product_id':'C','order_date':'2024-02-11','status':'Processing','quantity':5,'line_total':150.0},
 ])


def test_bridge_reconciles_with_new_and_exited_products():
 r=analyze(fixture())
 assert r['components']['volume_inr']==pytest.approx(50)
 assert r['components']['mix_inr']==pytest.approx(0)
 assert r['components']['realized_price_inr']==pytest.approx(30)
 assert r['components']['entry_inr']==pytest.approx(150)
 assert r['components']['exit_inr']==pytest.approx(-200)
 assert r['revenue_change_inr']==pytest.approx(30)
 assert r['reconciliation']['sql_pandas']=='PASS'
 assert r['reconciliation']['bridge_residual_inr']==pytest.approx(0,abs=1e-8)


def test_rejects_bad_quantities_and_duplicate_lines():
 bad=fixture();bad.loc[0,'quantity']=0
 with pytest.raises(ValueError):analyze(bad)
 bad=fixture();bad.loc[0,'item_id']=bad.loc[1,'item_id']
 with pytest.raises(ValueError):analyze(bad)


def test_current_dataset_and_committed_embed_reconcile():
 import json,re
 result=analyze(load_source())
 text=(ROOT/'dashboard/revenue_pvm_data.js').read_text(encoding='utf8')
 match=re.fullmatch(r'globalThis\.BVDIE_PVM = (.*);\n',text)
 assert match
 embedded=json.loads(match.group(1))
 assert embedded==result
 assert result['reconciliation']['sql_pandas']=='PASS'
 assert abs(result['reconciliation']['bridge_residual_inr'])<1e-6
 assert (ROOT/'revenue_pvm_data.js').read_bytes()==(ROOT/'dashboard/revenue_pvm_data.js').read_bytes()


def test_mix_and_price_are_separated_under_defined_ordering():
 f=pd.DataFrame([
  {'item_id':'a0','order_id':'o1','product_id':'A','order_date':'2024-01-10','status':'Delivered','quantity':10,'line_total':100.0},
  {'item_id':'b0','order_id':'o2','product_id':'B','order_date':'2024-01-10','status':'Delivered','quantity':10,'line_total':200.0},
  {'item_id':'a1','order_id':'o3','product_id':'A','order_date':'2024-02-10','status':'Delivered','quantity':15,'line_total':180.0},
  {'item_id':'b1','order_id':'o4','product_id':'B','order_date':'2024-02-10','status':'Delivered','quantity':5,'line_total':100.0},
 ])
 result=analyze(f)
 assert result['components']['volume_inr']==pytest.approx(0)
 assert result['components']['mix_inr']==pytest.approx(-50)
 assert result['components']['realized_price_inr']==pytest.approx(30)
 assert result['revenue_change_inr']==pytest.approx(-20)


def test_invalid_period_data_and_nonfinite_values_refuse():
 f=fixture();f.loc[0,'line_total']=float('nan')
 with pytest.raises(ValueError):analyze(f)
 f=fixture();f['order_date']='2024-01-01'
 with pytest.raises(ValueError):analyze(f)


def test_pvm_dashboard_asset_has_nested_route():
 import json
 config=json.loads((ROOT/'dashboard/vercel.json').read_text(encoding='utf8'))
 assert {'source':'/dashboard/revenue_pvm_data.js','destination':'/revenue_pvm_data.js'} in config['rewrites']
 assert 'src="revenue_pvm_data.js"' in (ROOT/'dashboard/dashboard.html').read_text(encoding='utf8')
