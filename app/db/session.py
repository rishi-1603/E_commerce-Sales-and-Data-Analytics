from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine, inspect, select, func
from app.core.config import settings
from app.models.base import Base
from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order, OrderItem
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger("commerce_api")

# Async Engine (for FastAPI request handlers)
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Sync Engine (for table creation, migrations, and CSV seeding)
sync_connect_args = {"check_same_thread": False} if "sqlite" in settings.SYNC_DATABASE_URL else {}
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False,
    connect_args=sync_connect_args
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def init_db():
    """
    Initializes the database schema and seeds initial data from CSVs if empty.
    Zero-config out of the box for recruiters and local development.
    """
    # 1. Create tables synchronously
    Base.metadata.create_all(bind=sync_engine)
    
    # 2. Check if database has orders
    inspector = inspect(sync_engine)
    if "orders" in inspector.get_table_names():
        with sync_engine.connect() as conn:
            from sqlalchemy import text
            count = conn.execute(text("SELECT COUNT(*) FROM orders")).scalar()
            if count and count > 0:
                logger.info(f"Database already seeded with {count} orders.")
                return

    # 3. Seed from data/raw/
    raw_dir = Path(__file__).resolve().parents[2] / "data" / "raw"
    if not (raw_dir / "customers.csv").exists():
        logger.warning(f"Raw data directory {raw_dir} not found; skipping seeding.")
        return

    logger.info("Seeding database from raw CSVs...")
    try:
        df_customers = pd.read_csv(raw_dir / "customers.csv")
        df_products = pd.read_csv(raw_dir / "products.csv")
        df_orders = pd.read_csv(raw_dir / "orders.csv")
        df_order_items = pd.read_csv(raw_dir / "order_items.csv")

        # Ingest in relational dependency order
        df_customers.to_sql("customers", sync_engine, if_exists="append", index=False)
        df_products.to_sql("products", sync_engine, if_exists="append", index=False)
        df_orders.to_sql("orders", sync_engine, if_exists="append", index=False)
        df_order_items.to_sql("order_items", sync_engine, if_exists="append", index=False)
        logger.info("Database seeding completed successfully.")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
