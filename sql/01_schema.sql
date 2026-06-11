-- ============================================================
--  E-Commerce Analytics Database Schema
--  Compatible: PostgreSQL 14+ / SQLite 3
-- ============================================================

-- Drop if exists (for re-runs)
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

-- ── CUSTOMERS ────────────────────────────────────────────
CREATE TABLE customers (
    customer_id         VARCHAR(10)  PRIMARY KEY,
    first_name          VARCHAR(50)  NOT NULL,
    last_name           VARCHAR(50)  NOT NULL,
    email               VARCHAR(100) UNIQUE NOT NULL,
    region              VARCHAR(20),
    segment             VARCHAR(20),
    acquisition_channel VARCHAR(50),
    registration_date   DATE,
    age                 INT,
    gender              VARCHAR(10)
);

-- ── PRODUCTS ─────────────────────────────────────────────
CREATE TABLE products (
    product_id    VARCHAR(8)   PRIMARY KEY,
    product_name  VARCHAR(100) NOT NULL,
    category      VARCHAR(50),
    subcategory   VARCHAR(50),
    cost_price    DECIMAL(10,2),
    selling_price DECIMAL(10,2),
    stock_qty     INT,
    rating        DECIMAL(3,1),
    launch_date   DATE
);

-- ── ORDERS ───────────────────────────────────────────────
CREATE TABLE orders (
    order_id       VARCHAR(12)  PRIMARY KEY,
    customer_id    VARCHAR(10)  REFERENCES customers(customer_id),
    order_date     DATE,
    status         VARCHAR(20),
    payment_method VARCHAR(30),
    discount_pct   DECIMAL(5,2),
    shipping_cost  DECIMAL(8,2)
);

-- ── ORDER ITEMS ───────────────────────────────────────────
CREATE TABLE order_items (
    item_id      VARCHAR(20)  PRIMARY KEY,
    order_id     VARCHAR(12)  REFERENCES orders(order_id),
    product_id   VARCHAR(8)   REFERENCES products(product_id),
    quantity     INT,
    unit_price   DECIMAL(10,2),
    discount_pct DECIMAL(5,2),
    final_price  DECIMAL(10,2),
    line_total   DECIMAL(12,2),
    cost_total   DECIMAL(12,2)
);

-- ── INDEXES ───────────────────────────────────────────────
CREATE INDEX idx_orders_customer   ON orders(customer_id);
CREATE INDEX idx_orders_date       ON orders(order_date);
CREATE INDEX idx_orders_status     ON orders(status);
CREATE INDEX idx_items_order       ON order_items(order_id);
CREATE INDEX idx_items_product     ON order_items(product_id);
CREATE INDEX idx_customers_region  ON customers(region);
CREATE INDEX idx_customers_segment ON customers(segment);

-- ── LOAD DATA (PostgreSQL COPY syntax) ────────────────────
-- Adjust path to your CSV files location
-- \COPY customers     FROM 'data/raw/customers.csv'     CSV HEADER;
-- \COPY products      FROM 'data/raw/products.csv'      CSV HEADER;
-- \COPY orders        FROM 'data/raw/orders.csv'        CSV HEADER;
-- \COPY order_items   FROM 'data/raw/order_items.csv'   CSV HEADER;
