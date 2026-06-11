"""
E-Commerce Analytics — Synthetic Dataset Generator
Generates 4 CSV files: customers, products, orders, order_items
Run: python generate_data.py
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

random.seed(42)
np.random.seed(42)

N_CUSTOMERS = 2000
N_PRODUCTS  = 150
N_ORDERS    = 12000
START_DATE  = datetime(2022, 1, 1)
END_DATE    = datetime(2024, 12, 31)

categories = {
    "Electronics":   ["Smartphone","Laptop","Tablet","Headphones","Smartwatch","Camera","Speaker","Monitor"],
    "Clothing":      ["T-Shirt","Jeans","Jacket","Dress","Sneakers","Boots","Hoodie","Shorts"],
    "Home & Garden": ["Sofa","Lamp","Blender","Coffee Maker","Rug","Curtains","Plant Pot","Bookshelf"],
    "Sports":        ["Yoga Mat","Dumbbell Set","Running Shoes","Cycling Helmet","Tennis Racket","Football","Backpack","Water Bottle"],
    "Beauty":        ["Moisturizer","Perfume","Lipstick","Foundation","Shampoo","Face Mask","Eye Cream","Sunscreen"],
}

regions   = ["North","South","East","West","Central"]
segments  = ["B2C","B2B","Enterprise"]
channels  = ["Organic Search","Paid Search","Social Media","Email","Direct","Referral","Affiliate"]
payments  = ["Credit Card","Debit Card","PayPal","UPI","Net Banking","Wallet"]
status_w  = {"Delivered":0.78,"Returned":0.10,"Cancelled":0.07,"Processing":0.05}

first_names = ["Aarav","Priya","Rahul","Sneha","Vikram","Ananya","Arjun","Pooja","Rohit","Divya",
               "Amit","Kavya","Suresh","Meera","Nikhil","Anjali","Sanjay","Shreya","Kiran","Deepa",
               "James","Emma","Oliver","Sophia","William","Ava","Liam","Isabella","Noah","Mia"]
last_names  = ["Sharma","Patel","Singh","Kumar","Mehta","Gupta","Joshi","Shah","Verma","Reddy",
               "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson","Taylor"]

def rand_date(s, e):
    delta = int((e - s).total_seconds())
    return s + timedelta(seconds=random.randint(0, delta))

def weighted_choice(d):
    keys, weights = zip(*d.items())
    return random.choices(keys, weights=weights)[0]

# ── CUSTOMERS ────────────────────────────────────────────
customers = []
for i in range(1, N_CUSTOMERS + 1):
    reg_date = rand_date(START_DATE, END_DATE - timedelta(days=30))
    customers.append({
        "customer_id":       f"CUST{i:05d}",
        "first_name":        random.choice(first_names),
        "last_name":         random.choice(last_names),
        "email":             f"user{i}@email.com",
        "region":            random.choice(regions),
        "segment":           random.choices(segments, weights=[70, 20, 10])[0],
        "acquisition_channel": random.choice(channels),
        "registration_date": reg_date.strftime("%Y-%m-%d"),
        "age":               random.randint(18, 65),
        "gender":            random.choice(["Male", "Female", "Other"]),
    })
df_customers = pd.DataFrame(customers)

# ── PRODUCTS ─────────────────────────────────────────────
products = []
pid = 1
all_items = [(cat, item) for cat, items in categories.items() for item in items]
while len(products) < N_PRODUCTS:
    cat, item = all_items[pid % len(all_items)]
    cost  = round(random.uniform(5, 800), 2)
    price = round(cost * random.uniform(1.2, 3.5), 2)
    products.append({
        "product_id":    f"PROD{pid:04d}",
        "product_name":  f"{item} {random.choice(['Pro','Plus','Elite','Basic','Ultra'])}",
        "category":      cat,
        "subcategory":   item,
        "cost_price":    cost,
        "selling_price": price,
        "stock_qty":     random.randint(0, 500),
        "rating":        round(random.uniform(2.5, 5.0), 1),
        "launch_date":   rand_date(START_DATE - timedelta(days=365), END_DATE).strftime("%Y-%m-%d"),
    })
    pid += 1
df_products = pd.DataFrame(products)

# ── ORDERS + ORDER ITEMS ──────────────────────────────────
orders, order_items = [], []
oid = 1
discount_opts    = [0, 0.05, 0.10, 0.15, 0.20]
discount_weights = [40, 25, 20, 10, 5]

for _ in range(N_ORDERS):
    cust    = random.choice(customers)
    reg_dt  = datetime.strptime(cust["registration_date"], "%Y-%m-%d")
    order_dt = rand_date(reg_dt, END_DATE)
    status   = weighted_choice(status_w)
    discount = random.choices(discount_opts, weights=discount_weights)[0]

    orders.append({
        "order_id":       f"ORD{oid:07d}",
        "customer_id":    cust["customer_id"],
        "order_date":     order_dt.strftime("%Y-%m-%d"),
        "status":         status,
        "payment_method": random.choice(payments),
        "discount_pct":   discount,
        "shipping_cost":  round(random.uniform(0, 15), 2),
    })

    n_items   = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
    sel_prods = random.sample(range(len(df_products)), min(n_items, len(df_products)))
    for idx in sel_prods:
        prod  = df_products.iloc[idx]
        qty   = random.randint(1, 5)
        base  = prod["selling_price"]
        final = round(base * (1 - discount), 2)
        order_items.append({
            "item_id":      f"ITEM{oid:07d}{idx:03d}",
            "order_id":     f"ORD{oid:07d}",
            "product_id":   prod["product_id"],
            "quantity":     qty,
            "unit_price":   base,
            "discount_pct": discount,
            "final_price":  final,
            "line_total":   round(final * qty, 2),
            "cost_total":   round(prod["cost_price"] * qty, 2),
        })
    oid += 1

df_orders      = pd.DataFrame(orders)
df_order_items = pd.DataFrame(order_items)

# ── SAVE ──────────────────────────────────────────────────
out = os.path.dirname(os.path.abspath(__file__))
df_customers.to_csv(f"{out}/customers.csv",     index=False)
df_products.to_csv(f"{out}/products.csv",       index=False)
df_orders.to_csv(f"{out}/orders.csv",           index=False)
df_order_items.to_csv(f"{out}/order_items.csv", index=False)

print("Dataset generated successfully!")
print(f"  customers.csv   : {len(df_customers):,} rows")
print(f"  products.csv    : {len(df_products):,} rows")
print(f"  orders.csv      : {len(df_orders):,} rows")
print(f"  order_items.csv : {len(df_order_items):,} rows")
