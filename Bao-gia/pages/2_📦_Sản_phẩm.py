import streamlit as st
import pandas as pd
from database.db import get_session
from models.models import Product
from auth.session import require_login
from auth.rbac import has_permission, require_role, PermissionDenied

st.set_page_config(page_title="Sản phẩm - QUOTEFLOW OS", page_icon="📦", layout="wide")

current_login_user = require_login()

st.title("📦 Quản lý Sản phẩm")

db = get_session()
products = db.query(Product).all()

tab1, tab2 = st.tabs(["📄 Danh mục sản phẩm", "➕ Thêm sản phẩm mới"])

with tab1:
    rows = [{
        "Mã hàng": p.sku, "Tên hàng": p.name, "Quy cách": p.spec, "ĐVT": p.unit,
        "Giá vốn (đ)": f"{p.cost_price:,.0f}" if p.cost_price is not None else "0", 
        "Giá bán (đ)": f"{p.list_price:,.0f}" if p.list_price is not None else "0", 
        "CK tối đa %": f"{p.max_discount_pct}%",
        "VAT %": f"{p.vat_pct}%", "Nhóm hàng": p.category, "Kho": p.warehouse, 
        "Tồn kho": f"{p.stock_qty:,.0f}" if p.stock_qty is not None else "0",
        "Biên LN %": f"{round((p.list_price - p.cost_price) / p.list_price * 100, 1)}%" if p.list_price else "0%",
    } for p in products]
    df = pd.DataFrame(rows)
    cat_filter = st.multiselect("Lọc theo nhóm hàng", options=sorted(df["Nhóm hàng"].dropna().unique()) if not df.empty else [], key="product_cat_filter")
    show_df = df[df["Nhóm hàng"].isin(cat_filter)] if cat_filter else df
    st.dataframe(
        show_df,
        use_container_width=True, hide_index=True,
    )
    st.caption(f"Tổng {len(show_df)} sản phẩm")

    low_stock_count = sum(1 for p in products if (p.stock_qty or 0) < 100)
    if low_stock_count > 0:
        st.warning(f"⚠️ Có {low_stock_count} sản phẩm tồn kho thấp (<100)")

with tab2:
    if not has_permission(current_login_user.role, "manage_products"):
        st.warning("🚫 Vai trò của bạn không có quyền thêm sản phẩm mới. Chỉ Admin/Giám đốc/CEO mới được phép.")
    else:
        with st.form("new_product"):
            c1, c2 = st.columns(2)
            with c1:
                sku = st.text_input("Mã hàng*", value=f"SP{len(products)+1:04d}")
                name = st.text_input("Tên hàng*")
                spec = st.text_input("Quy cách")
                unit = st.text_input("Đơn vị tính*", value="Cái")
                category = st.text_input("Nhóm hàng")
            with c2:
                cost_price = st.number_input("Giá vốn", min_value=0.0, step=1000.0)
                list_price = st.number_input("Giá bán*", min_value=0.0, step=1000.0)
                max_discount_pct = st.number_input("Chiết khấu tối đa (%)", min_value=0.0, max_value=100.0, value=10.0)
                vat_pct = st.number_input("VAT (%)", min_value=0.0, max_value=100.0, value=10.0)
                warehouse = st.text_input("Kho", value="Kho chính")
                stock_qty = st.number_input("Tồn kho", min_value=0.0, step=1.0)
            submitted = st.form_submit_button("Lưu sản phẩm", type="primary")
            if submitted:
                if not name or list_price <= 0:
                    st.error("Vui lòng nhập tên hàng và giá bán hợp lệ")
                else:
                    db.add(Product(sku=sku, name=name, spec=spec, unit=unit, cost_price=cost_price,
                                    list_price=list_price, max_discount_pct=max_discount_pct,
                                    vat_pct=vat_pct, category=category, warehouse=warehouse,
                                    stock_qty=stock_qty))
                    db.commit()
                    st.success(f"Đã thêm sản phẩm {name}")
                    st.rerun()

db.close()
