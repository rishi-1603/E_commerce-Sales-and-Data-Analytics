from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List
from app.schemas.analytics import OverviewKPIResponse, SalesTrendResponse, SalesTrendItem
from app.schemas.product import TopProductResponse

class AnalyticsService:
    @staticmethod
    async def get_overview_kpis(
        db: AsyncSession, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> OverviewKPIResponse:
        """
        Calculates executive KPIs anchored to the authoritative valid_orders rule:
        Valid revenue = status NOT IN ('Cancelled', 'Returned') (Delivered + Processing only).
        Matches sql/03_kpi_analysis.sql
        """
        # Compatible across SQLite and PostgreSQL
        query_str = """
        WITH filtered_orders AS (
            SELECT order_id, customer_id, status, order_date
            FROM orders
            WHERE (:start_date IS NULL OR order_date >= :start_date)
              AND (:end_date IS NULL OR order_date <= :end_date)
        ),
        valid_orders_calc AS (
            SELECT 
                COUNT(DISTINCT fo.order_id) AS valid_order_count,
                COALESCE(SUM(oi.line_total), 0.0) AS valid_revenue
            FROM filtered_orders fo
            JOIN order_items oi ON fo.order_id = oi.order_id
            WHERE fo.status NOT IN ('Cancelled', 'Returned')
        ),
        overall_stats AS (
            SELECT 
                COUNT(*) AS total_orders,
                COUNT(DISTINCT customer_id) AS total_customers,
                SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_count,
                SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) AS delivered_count
            FROM filtered_orders
        )
        SELECT 
            vo.valid_revenue,
            os.total_orders,
            os.total_customers,
            CASE WHEN vo.valid_order_count > 0 
                 THEN ROUND(vo.valid_revenue / vo.valid_order_count, 2) 
                 ELSE 0.0 END AS avg_order_value,
            CASE WHEN os.total_orders > 0 
                 THEN ROUND(os.cancelled_count * 100.0 / os.total_orders, 2) 
                 ELSE 0.0 END AS cancellation_rate_pct,
            os.delivered_count AS delivered_orders_count
        FROM valid_orders_calc vo, overall_stats os;
        """
        result = await db.execute(text(query_str), {"start_date": start_date, "end_date": end_date})
        row = result.mappings().one()
        return OverviewKPIResponse(
            total_revenue=float(row["valid_revenue"]),
            total_orders=int(row["total_orders"]),
            total_customers=int(row["total_customers"]),
            avg_order_value=float(row["avg_order_value"]),
            cancellation_rate_pct=float(row["cancellation_rate_pct"]),
            delivered_orders_count=int(row["delivered_orders_count"])
        )

    @staticmethod
    async def get_monthly_trends(db: AsyncSession) -> SalesTrendResponse:
        """
        Computes monthly revenue and order volume trends.
        Matches sql/04_sales_analysis.sql
        """
        query_str = """
        SELECT 
            substr(o.order_date, 1, 7) AS period,
            COUNT(DISTINCT o.order_id) AS order_count,
            ROUND(SUM(oi.line_total), 2) AS total_revenue,
            ROUND(SUM(oi.line_total) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.status NOT IN ('Cancelled', 'Returned')
        GROUP BY substr(o.order_date, 1, 7)
        ORDER BY period ASC;
        """
        result = await db.execute(text(query_str))
        rows = result.mappings().all()
        items = [
            SalesTrendItem(
                period=str(r["period"]),
                total_revenue=float(r["total_revenue"]),
                order_count=int(r["order_count"]),
                avg_order_value=float(r["avg_order_value"])
            )
            for r in rows
        ]
        return SalesTrendResponse(granularity="monthly", trends=items)

    @staticmethod
    async def get_top_products(db: AsyncSession, limit: int = 10) -> List[TopProductResponse]:
        """
        Computes top products ranked by revenue with profit and margin metrics.
        Matches sql/06_product_analysis.sql
        """
        query_str = """
        SELECT 
            p.product_id,
            p.product_name,
            p.category,
            SUM(oi.quantity) AS total_units_sold,
            ROUND(SUM(oi.line_total), 2) AS total_revenue,
            ROUND(SUM(oi.line_total - (p.cost_price * oi.quantity)), 2) AS total_profit,
            ROUND((SUM(oi.line_total - (p.cost_price * oi.quantity)) * 100.0) / NULLIF(SUM(oi.line_total), 0), 2) AS profit_margin_pct
        FROM products p
        JOIN order_items oi ON p.product_id = oi.product_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.status NOT IN ('Cancelled', 'Returned')
        GROUP BY p.product_id, p.product_name, p.category
        ORDER BY total_revenue DESC
        LIMIT :limit;
        """
        result = await db.execute(text(query_str), {"limit": limit})
        rows = result.mappings().all()
        return [
            TopProductResponse(
                product_id=str(r["product_id"]),
                product_name=str(r["product_name"]),
                category=str(r["category"]),
                total_units_sold=int(r["total_units_sold"]),
                total_revenue=float(r["total_revenue"]),
                total_profit=float(r["total_profit"]),
                profit_margin_pct=float(r["profit_margin_pct"]) if r["profit_margin_pct"] is not None else 0.0
            )
            for r in rows
        ]
