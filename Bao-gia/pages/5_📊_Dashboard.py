import streamlit as st
import plotly.express as px
import pandas as pd
from database.db import get_session
from models.models import SalesUser, RoleEnum
from services import kpi_service as kpi
from auth.session import require_login

st.set_page_config(page_title="Dashboard - QUOTEFLOW OS", page_icon="📊", layout="wide")

current_user = require_login()
db = get_session()

role_view = {
    RoleEnum.CEO: "Dashboard CEO",
    RoleEnum.SALES_DIRECTOR: "Dashboard Giám đốc Kinh doanh",
    RoleEnum.SALES_MANAGER: "Dashboard Trưởng phòng",
    RoleEnum.SALESMAN: "Dashboard Nhân viên Kinh doanh",
}.get(current_user.role, "Dashboard")

st.title(f"📊 {role_view}")

s = kpi.kpi_summary(db)
c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(
    f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; min-height: 80px;">
        <span style="font-size: 13px; color: #64748B; font-weight: 500;">Tổng số báo giá</span><br>
        <span style="font-size: 20px; color: #1E293B; font-weight: 700;">{s["total_quotes"]}</span>
    </div>
    """,
    unsafe_allow_html=True
)
c2.markdown(
    f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; min-height: 80px;">
        <span style="font-size: 13px; color: #64748B; font-weight: 500;">Tổng giá trị</span><br>
        <span style="font-size: 19px; color: #1E293B; font-weight: 700; white-space: nowrap;">{s['total_value']:,.0f} đ</span>
    </div>
    """,
    unsafe_allow_html=True
)
c3.markdown(
    f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; min-height: 80px;">
        <span style="font-size: 13px; color: #64748B; font-weight: 500;">Win Rate</span><br>
        <span style="font-size: 20px; color: #16A34A; font-weight: 700;">{s["win_rate"]}%</span>
    </div>
    """,
    unsafe_allow_html=True
)
c4.markdown(
    f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; min-height: 80px;">
        <span style="font-size: 13px; color: #64748B; font-weight: 500;">Lost Rate</span><br>
        <span style="font-size: 20px; color: #DC2626; font-weight: 700;">{s["lost_rate"]}%</span>
    </div>
    """,
    unsafe_allow_html=True
)
c5.markdown(
    f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; min-height: 80px;">
        <span style="font-size: 13px; color: #64748B; font-weight: 500;">Báo giá quá hạn</span><br>
        <span style="font-size: 20px; color: {'#DC2626' if s['overdue_count'] > 0 else '#1E293B'}; font-weight: 700;">{s["overdue_count"]}</span>
    </div>
    """,
    unsafe_allow_html=True
)

c6, c7 = st.columns(2)
c6.markdown(
    f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px 16px; border-radius: 8px; min-height: 80px; margin-top: 15px;">
        <span style="font-size: 13px; color: #64748B; font-weight: 500;">Giá trị Pipeline đang mở</span><br>
        <span style="font-size: 20px; color: #1E293B; font-weight: 700; white-space: nowrap;">{s.get('pipeline_value',0):,.0f} đ</span>
    </div>
    """,
    unsafe_allow_html=True
)
c7.markdown(
    f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px 16px; border-radius: 8px; min-height: 80px; margin-top: 15px;">
        <span style="font-size: 13px; color: #64748B; font-weight: 500;">Dự báo doanh thu sắp tới</span><br>
        <span style="font-size: 20px; color: #1E293B; font-weight: 700; white-space: nowrap;">{kpi.revenue_forecast_next_month(db):,.0f} đ</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("🔻 Pipeline theo trạng thái")
    pdf_ = kpi.pipeline_by_status(db)
    if not pdf_.empty:
        fig = px.bar(pdf_, x="status", y="sum", text="count",
                     labels={"status": "Trạng thái", "sum": "Giá trị (đ)"},
                     color="status", title=None)
        fig.update_traces(texttemplate="%{text} báo giá", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu.")

with col2:
    st.subheader("🏆 Top khách hàng theo giá trị báo giá")
    top_c = kpi.top_customers(db, n=8)
    if not top_c.empty:
        fig2 = px.pie(top_c, names="customer", values="grand_total", hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu.")

col3, col4 = st.columns(2)
with col3:
    st.subheader("📦 Top sản phẩm bán chạy")
    top_p = kpi.top_products(db, n=8)
    if not top_p.empty:
        fig3 = px.bar(top_p, x="product", y="revenue", labels={"product": "Sản phẩm", "revenue": "Doanh thu"})
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu.")

with col4:
    st.subheader("👤 Top nhân viên kinh doanh")
    top_r = kpi.top_sales_reps(db, n=8)
    if not top_r.empty:
        top_r_display = top_r.rename(columns={
            "sales_rep": "Nhân viên", "so_bao_gia": "Số báo giá",
            "gia_tri": "Giá trị (đ)", "won_count": "Số đơn thắng", "win_rate_%": "Win Rate %"
        })
        top_r_display["Giá trị (đ)"] = top_r_display["Giá trị (đ)"].apply(lambda x: f"{x:,.0f}")
        st.dataframe(top_r_display, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có dữ liệu.")

st.divider()
st.subheader("📈 Xu hướng báo giá theo thời gian")
df = kpi.quotations_dataframe(db)
if not df.empty:
    df["month"] = pd.to_datetime(df["quote_date"]).dt.to_period("M").astype(str)
    trend = df.groupby("month")["grand_total"].sum().reset_index()
    fig4 = px.line(trend, x="month", y="grand_total", markers=True,
                    labels={"month": "Tháng", "grand_total": "Giá trị báo giá (đ)"})
    st.plotly_chart(fig4, use_container_width=True)

db.close()
