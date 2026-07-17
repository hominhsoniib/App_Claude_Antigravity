import streamlit as st
import pandas as pd
from database.db import get_session
from models.models import Customer, Contact, SalesUser
from auth.session import require_login

st.set_page_config(page_title="Khách hàng - QUOTEFLOW OS", page_icon="📋", layout="wide")

current_login_user = require_login()

st.title("📋 Quản lý Khách hàng")

db = get_session()
customers = db.query(Customer).all()
reps = {u.id: u.full_name for u in db.query(SalesUser).all()}

tab1, tab2 = st.tabs(["📄 Danh sách khách hàng", "➕ Thêm khách hàng mới"])

with tab1:
    rows = []
    for c in customers:
        rows.append({
            "Mã KH": c.code, "Tên khách hàng": c.name, "MST": c.tax_code,
            "Nhóm": c.group, "Khu vực": c.region,
            "NV phụ trách": reps.get(c.sales_rep_id, ""),
            "Công nợ (đ)": f"{c.debt:,.0f}" if c.debt is not None else "0", 
            "Doanh số (đ)": f"{c.revenue_ytd:,.0f}" if c.revenue_ytd is not None else "0",
        })
    df = pd.DataFrame(rows)
    col1, col2 = st.columns([1, 3])
    with col1:
        group_filter = st.multiselect("Lọc theo nhóm", options=sorted(df["Nhóm"].dropna().unique()) if not df.empty else [], key="customer_group_filter")
    show_df = df[df["Nhóm"].isin(group_filter)] if group_filter else df
    st.dataframe(
        show_df,
        use_container_width=True, hide_index=True,
    )
    st.caption(f"Tổng {len(show_df)} khách hàng")

    st.divider()
    st.subheader("🔍 Chi tiết khách hàng")
    if customers:
        pick = st.selectbox("Chọn khách hàng", options=[c.id for c in customers],
                             format_func=lambda cid: next(c.name for c in customers if c.id == cid))
        cust = next(c for c in customers if c.id == pick)
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Địa chỉ:** {cust.address}")
            st.write(f"**MST:** {cust.tax_code}")
            st.write(f"**Nhóm:** {cust.group}  |  **Khu vực:** {cust.region}")
        with c2:
            st.write(f"**Công nợ hiện tại:** {cust.debt:,.0f} đ")
            st.write(f"**Doanh số YTD:** {cust.revenue_ytd:,.0f} đ")
            st.write(f"**NV phụ trách:** {reps.get(cust.sales_rep_id, '')}")

        st.write("**Liên hệ:**")
        contacts = db.query(Contact).filter(Contact.customer_id == cust.id).all()
        for ct in contacts:
            st.write(f"- {ct.name} ({ct.position}) — {ct.phone} — {ct.email}")

with tab2:
    with st.form("new_customer"):
        c1, c2 = st.columns(2)
        with c1:
            code = st.text_input("Mã khách hàng*", value=f"KH{len(customers)+1:04d}")
            name = st.text_input("Tên khách hàng*")
            tax_code = st.text_input("Mã số thuế")
            address = st.text_input("Địa chỉ")
        with c2:
            group = st.selectbox("Nhóm khách hàng", ["Đại lý", "Dự án", "VIP", "Xuất khẩu", "Thường"])
            region = st.text_input("Khu vực")
            rep_id = st.selectbox("Nhân viên phụ trách", options=list(reps.keys()),
                                   format_func=lambda uid: reps[uid])
        submitted = st.form_submit_button("Lưu khách hàng", type="primary")
        if submitted:
            if not name:
                st.error("Vui lòng nhập tên khách hàng")
            else:
                new_c = Customer(code=code, name=name, tax_code=tax_code, address=address,
                                  group=group, region=region, sales_rep_id=rep_id)
                db.add(new_c)
                db.commit()
                st.success(f"Đã thêm khách hàng {name}")
                st.rerun()

db.close()
