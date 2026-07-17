import pandas as pd
from datetime import datetime
from models.models import QuotationHeader, QuotationDetail, Customer, Product, SalesUser, QuoteStatus


def quotations_dataframe(db):
    """Trả về DataFrame tổng hợp toàn bộ báo giá kèm giá trị, KH, NV."""
    rows = []
    for h in db.query(QuotationHeader).all():
        rows.append({
            "id": h.id,
            "quote_no": h.quote_no,
            "customer": h.customer.name if h.customer else "",
            "customer_group": h.customer.group if h.customer else "",
            "region": h.customer.region if h.customer else "",
            "sales_rep": h.sales_rep.full_name if h.sales_rep else "",
            "quote_date": h.quote_date,
            "valid_until": h.valid_until,
            "status": h.status.value if h.status else "",
            "grand_total": h.grand_total,
            "is_expired": (h.valid_until and h.valid_until < datetime.utcnow()
                           and h.status not in (QuoteStatus.WON, QuoteStatus.LOST)),
        })
    return pd.DataFrame(rows)


def kpi_summary(db):
    df = quotations_dataframe(db)
    if df.empty:
        return {
            "total_quotes": 0, "total_value": 0, "win_rate": 0, "lost_rate": 0,
            "expected_revenue": 0, "avg_close_days": 0, "overdue_count": 0,
        }

    total_quotes = len(df)
    total_value = df["grand_total"].sum()
    won = df[df["status"] == QuoteStatus.WON.value]
    lost = df[df["status"] == QuoteStatus.LOST.value]
    decided = len(won) + len(lost)
    win_rate = (len(won) / decided * 100) if decided else 0
    lost_rate = (len(lost) / decided * 100) if decided else 0

    open_statuses = [QuoteStatus.SENT.value, QuoteStatus.NEGOTIATING.value,
                      QuoteStatus.APPROVED.value, QuoteStatus.PENDING_MANAGER.value,
                      QuoteStatus.PENDING_DIRECTOR.value]
    pipeline_df = df[df["status"].isin(open_statuses)]
    expected_revenue = pipeline_df["grand_total"].sum() * (win_rate / 100 if win_rate else 0.3)

    overdue_count = int(df["is_expired"].sum())

    return {
        "total_quotes": total_quotes,
        "total_value": total_value,
        "win_rate": round(win_rate, 1),
        "lost_rate": round(lost_rate, 1),
        "expected_revenue": round(expected_revenue, 0),
        "pipeline_value": round(pipeline_df["grand_total"].sum(), 0),
        "overdue_count": overdue_count,
    }


def top_customers(db, n=5):
    df = quotations_dataframe(db)
    if df.empty:
        return pd.DataFrame()
    return (df.groupby("customer")["grand_total"].sum()
            .sort_values(ascending=False).head(n).reset_index())


def top_sales_reps(db, n=5):
    df = quotations_dataframe(db)
    if df.empty:
        return pd.DataFrame()
    won = df[df["status"] == QuoteStatus.WON.value]
    grp = df.groupby("sales_rep").agg(
        so_bao_gia=("id", "count"), gia_tri=("grand_total", "sum")
    ).reset_index()
    win_count = won.groupby("sales_rep")["id"].count().rename("won_count")
    grp = grp.merge(win_count, on="sales_rep", how="left").fillna(0)
    grp["win_rate_%"] = (grp["won_count"] / grp["so_bao_gia"] * 100).round(1)
    return grp.sort_values("gia_tri", ascending=False).head(n)


def top_products(db, n=5):
    rows = []
    for d in db.query(QuotationDetail).all():
        if d.product:
            rows.append({"product": d.product.name, "revenue": d.line_total, "qty": d.qty})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    return (df.groupby("product").agg(qty=("qty", "sum"), revenue=("revenue", "sum"))
            .sort_values("revenue", ascending=False).head(n).reset_index())


def pipeline_by_status(db):
    df = quotations_dataframe(db)
    if df.empty:
        return pd.DataFrame()
    return df.groupby("status")["grand_total"].agg(["count", "sum"]).reset_index()


def revenue_forecast_next_month(db):
    """Dự báo đơn giản: pipeline value * xác suất theo trạng thái."""
    df = quotations_dataframe(db)
    if df.empty:
        return 0
    weights = {
        QuoteStatus.PENDING_MANAGER.value: 0.2,
        QuoteStatus.PENDING_DIRECTOR.value: 0.25,
        QuoteStatus.APPROVED.value: 0.4,
        QuoteStatus.SENT.value: 0.5,
        QuoteStatus.NEGOTIATING.value: 0.7,
    }
    forecast = 0
    for status, w in weights.items():
        subset = df[df["status"] == status]
        forecast += subset["grand_total"].sum() * w
    return round(forecast, 0)
