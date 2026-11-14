"""Export star-schema CSVs for the Power BI model.

Column names follow powerbi/dax_measures.md exactly so the DAX measures
match the model without edits:
  Fact_Orders[order_item_total], Fact_Orders[order_status], Dim_Products[unit_cost]
Keys stay as text (ORD..., CUST..., PROD...); numerics keep their native types.
"""
import pandas as pd
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'data')
os.makedirs(OUT, exist_ok=True)

m = pd.read_csv(r'C:\Users\user\portfolio-roadmaps\repos\ecom\data\processed\master_orders.csv')
c = pd.read_csv(r'C:\Users\user\portfolio-roadmaps\repos\ecom\data\raw\customers.csv')
p = pd.read_csv(r'C:\Users\user\portfolio-roadmaps\repos\ecom\data\raw\products.csv')

# ---- Fact_Orders (order-line grain) ----
fact = pd.DataFrame({
    'item_id': m['item_id'],
    'order_id': m['order_id'],
    'order_date': pd.to_datetime(m['order_date']).dt.strftime('%Y-%m-%d'),
    'order_status': m['status'],
    'customer_id': m['customer_id'],
    'product_id': m['product_id'],
    'quantity': m['quantity'].astype(int),
    'unit_price': m['unit_price'].astype(float),
    'discount_pct': m['discount_pct_x'].astype(float),
    'order_item_total': m['line_total'].astype(float),
    'cost_total': m['cost_total'].astype(float),
    'profit': m['profit'].astype(float),
    'payment_method': m['payment_method'],
    'shipping_cost': m['shipping_cost'].astype(float),
})
fact.to_csv(os.path.join(OUT, 'Fact_Orders.csv'), index=False, encoding='utf-8')

# ---- Dim_Products ----
dim_p = pd.DataFrame({
    'product_id': p['product_id'],
    'product_name': p['product_name'],
    'category': p['category'],
    'subcategory': p['subcategory'],
    'unit_cost': p['cost_price'].astype(float),
    'rating': p['rating'].astype(float),
})
dim_p.to_csv(os.path.join(OUT, 'Dim_Products.csv'), index=False, encoding='utf-8')

# ---- Dim_Customers ----
dim_c = pd.DataFrame({
    'customer_id': c['customer_id'],
    'customer_name': c['first_name'].fillna('') + ' ' + c['last_name'].fillna(''),
    'email': c['email'],
    'region': c['region'],
    'segment': c['segment'],
    'acquisition_channel': c['acquisition_channel'],
    'registration_date': pd.to_datetime(c['registration_date']).dt.strftime('%Y-%m-%d'),
    'age': c['age'].astype(int),
    'gender': c['gender'],
})
dim_c.to_csv(os.path.join(OUT, 'Dim_Customers.csv'), index=False, encoding='utf-8')

# ---- Dim_Calendar (full daily calendar spanning the fact range) ----
d = pd.date_range('2022-01-01', '2024-12-31', freq='D')
cal = pd.DataFrame({
    'Date': d.strftime('%Y-%m-%d'),
    'Year': d.year,
    'Quarter': 'Q' + d.quarter.astype(str),
    'MonthNumber': d.month,
    'MonthName': d.strftime('%b'),
})
cal.to_csv(os.path.join(OUT, 'Dim_Calendar.csv'), index=False, encoding='utf-8')

# sanity
print('fact rows:', len(fact), '| orders:', fact.order_id.nunique())
print('delivered:', fact[fact.order_status == 'Delivered'].order_id.nunique(),
      '| processing:', fact[fact.order_status == 'Processing'].order_id.nunique())
print('revenue check:', round(fact.order_item_total.sum(), 2))
print('profit check:', round(fact.profit.sum(), 2))
print('margin check:', round(fact.profit.sum() / fact.order_item_total.sum() * 100, 2))
print('customers:', fact.customer_id.nunique(), '| products:', fact.product_id.nunique())
print('aov check:', round(fact.order_item_total.sum() / fact.order_id.nunique(), 2))
print('calendar:', len(cal), 'days')
