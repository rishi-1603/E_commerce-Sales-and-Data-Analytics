-- ============================================================
--  01_database_schema.sql
--  E-Commerce Analytics — Data Warehouse Schema (PostgreSQL 14+)
--
--  Purpose : Create the 4-table star-style schema the entire
--            project (SQL + Python + dashboard) is built on.
--  Grain   : customers  = 1 row per customer
--            products   = 1 row per SKU
--            orders     = 1 row per order (header)
--            order_items= 1 row per product line within an order
--  Load    : \COPY commands at the bottom of this file.
-- ============================================================

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

-- ── DIMENSION: customers ──────────────────────────────────
CREATE TABLE customers (
    customer_id         VARCHAR(10)  PRIMARY KEY,
    first_name          VARCHAR(50)  NOT NULL,
    last_name           VARCHAR(50)  NOT NULL,
    email               VARCHAR(100) UNIQUE NOT NULL,
    region              VARCHAR(20),           -- North/South/East/West/Central
    segment             VARCHAR(20),           -- B2C / B2B / Enterprise
    acquisition_channel VARCHAR(50),           -- Organic, Paid, Social, ...
    registration_date   DATE,
    age                 INT,
    gender              VARCHAR(10)
);

-- ── DIMENSION: products ───────────────────────────────────
CREATE TABLE products (
    product_id    VARCHAR(8)   PRIMARY KEY,
    product_name  VARCHAR(100) NOT NULL,
    category      VARCHAR(50),                -- 5 categories
    subcategory   VARCHAR(50),
    cost_price    DECIMAL(10,2),              -- unit cost (INR)
    selling_price DECIMAL(10,2),              -- unit list price (INR)
    stock_qty     INT,
    rating        DECIMAL(3,1),
    launch_date   DATE
);

-- ── FACT: orders (header) ─────────────────────────────────
CREATE TABLE orders (
    order_id       VARCHAR(12)  PRIMARY KEY,
    customer_id    VARCHAR(10)  REFERENCES customers(customer_id),
    order_date     DATE,
    status         VARCHAR(20),               -- Delivered/Returned/Cancelled/Processing
    payment_method VARCHAR(30),
    discount_pct   DECIMAL(5,2),              -- 0 / 5 / 10 / 15 / 20 %
    shipping_cost  DECIMAL(8,2)
);

-- ── FACT: order_items (line grain — the money table) ──────
CREATE TABLE order_items (
    item_id      VARCHAR(20)  PRIMARY KEY,
    order_id     VARCHAR(12)  REFERENCES orders(order_id),
    product_id   VARCHAR(8)   REFERENCES products(product_id),
    quantity     INT,
    unit_price   DECIMAL(10,2),               -- pre-discount
    discount_pct DECIMAL(5,2),
    final_price  DECIMAL(10,2),               -- post-discount unit price
    line_total   DECIMAL(12,2),               -- final_price * quantity
    cost_total   DECIMAL(12,2)                -- cost_price * quantity
);

-- ── INDEXES (join & filter columns) ───────────────────────
CREATE INDEX idx_orders_customer   ON orders(customer_id);
CREATE INDEX idx_orders_date       ON orders(order_date);
CREATE INDEX idx_orders_status     ON orders(status);
CREATE INDEX idx_items_order       ON order_items(order_id);
CREATE INDEX idx_items_product     ON order_items(product_id);
CREATE INDEX idx_customers_region  ON customers(region);
CREATE INDEX idx_customers_segment ON customers(segment);

-- ── LOAD DATA (run from the repo root inside psql) ─────────
-- \COPY customers  FROM 'data/raw/customers.csv'  CSV HEADER;
-- \COPY products   FROM 'data/raw/products.csv'   CSV HEADER;
-- \COPY orders     FROM 'data/raw/orders.csv'     CSV HEADER;
-- \COPY order_items FROM 'data/raw/order_items.csv' CSV HEADER;

-- ── OPTIONAL: the "clean order" view all analysis uses ────
-- (Business rule: Cancelled and Returned orders are excluded
--  from revenue/profit metrics everywhere in this project.)
CREATE OR REPLACE VIEW valid_orders AS
SELECT o.*
FROM orders o
WHERE o.status NOT IN ('Cancelled', 'Returned');
