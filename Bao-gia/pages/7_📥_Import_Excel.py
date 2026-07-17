import streamlit as st
import pandas as pd
from database.db import get_session
from services import excel_service
from auth.session import require_login

st.set_page_config(page_title="Import Excel - QUOTEFLOW OS", page_icon="📥", layout="wide")

current_user = require_login()

st.title("📥 Import dữ liệu từ Excel")

tab1, tab2, tab3 = st.tabs(["📦 Import Sản phẩm", "📋 Import Khách hàng", "💰 Import Số dư đầu kỳ (Tồn kho)"])

with tab1:
    st.subheader("Bước 1: Tải template mẫu")
    template_buf = excel_service.build_template(excel_service.PRODUCT_TEMPLATE_COLUMNS, "Products")
    st.download_button("⬇️ Tải template Sản phẩm", template_buf,
                        file_name="template_san_pham.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.subheader("Bước 2: Upload file đã điền")
    uploaded = st.file_uploader("Chọn file Excel sản phẩm (.xlsx)", type=["xlsx"], key="prod_upload")

    if uploaded:
        df = pd.read_excel(uploaded)
        st.write("**Preview dữ liệu:**")
        st.dataframe(df, use_container_width=True)

        errors = excel_service.validate_products_df(df)
        if errors:
            st.error("❌ Phát hiện lỗi dữ liệu, vui lòng sửa trước khi import:")
            for e in errors:
                st.write(f"- {e}")
        else:
            st.success(f"✅ Dữ liệu hợp lệ — {len(df)} dòng sẵn sàng import.")
            if st.button("🚀 Import hàng loạt vào hệ thống", type="primary"):
                db = get_session()
                success, fail, errs = excel_service.import_products(db, df, actor=current_user.username)
                db.close()
                if fail == 0:
                    st.success(f"✅ Import thành công {success} sản phẩm (thêm mới hoặc cập nhật theo mã hàng).")
                else:
                    st.error(f"❌ Import thất bại: {errs}")

    st.caption("⚠️ Rollback: nếu import sai, có thể sửa lại file Excel với mã hàng đúng và import đè lại "
               "(hệ thống update theo `sku` trùng), hoặc xóa sản phẩm thủ công ở trang Sản phẩm.")

with tab2:
    st.subheader("Bước 1: Tải template mẫu")
    cust_template = excel_service.build_template(excel_service.CUSTOMER_TEMPLATE_COLUMNS, "Customers")
    st.download_button("⬇️ Tải template Khách hàng", cust_template,
                        file_name="template_khach_hang.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.subheader("Bước 2: Upload file đã điền")
    uploaded_cust = st.file_uploader("Chọn file Excel khách hàng (.xlsx)", type=["xlsx"], key="cust_upload")

    if uploaded_cust:
        df_cust = pd.read_excel(uploaded_cust)
        st.write("**Preview dữ liệu:**")
        st.dataframe(df_cust, use_container_width=True)

        errors_cust = excel_service.validate_customers_df(df_cust)
        if errors_cust:
            st.error("❌ Phát hiện lỗi dữ liệu, vui lòng sửa trước khi import:")
            for e in errors_cust:
                st.write(f"- {e}")
        else:
            st.success(f"✅ Dữ liệu hợp lệ — {len(df_cust)} dòng sẵn sàng import.")
            if st.button("🚀 Import khách hàng vào hệ thống", type="primary", key="btn_import_cust"):
                db = get_session()
                success, fail, errs = excel_service.import_customers(db, df_cust, actor=current_user.username)
                db.close()
                if fail == 0:
                    st.success(f"✅ Import thành công {success} khách hàng (thêm mới hoặc cập nhật theo mã khách hàng).")
                else:
                    st.error(f"❌ Import thất bại: {errs}")

    st.caption("⚠️ Rollback: nếu import sai, có thể sửa lại file Excel với mã khách hàng đúng và import đè lại "
               "(hệ thống update theo `code` trùng), hoặc xóa khách hàng thủ công ở trang Khách hàng.")

with tab3:
    st.subheader("Bước 1: Tải template mẫu")
    st.caption("File mẫu sẽ tự động điền danh sách sản phẩm và mã SKU hiện có trong hệ thống để bạn khai báo số lượng tồn kho đầu kỳ.")
    
    db = get_session()
    template_buf = excel_service.build_opening_balance_template(db)
    db.close()
    
    st.download_button(
        "⬇️ Tải file mẫu Số dư đầu kỳ (.xlsx)",
        template_buf,
        file_name="template_so_du_dau_ky.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="btn_dl_opening_tpl_main",
        use_container_width=True
    )
    
    st.write("")
    st.subheader("Bước 2: Upload file đã điền số dư")
    uploaded_opening = st.file_uploader(
        "Chọn file Excel số dư đầu kỳ (.xlsx)",
        type=["xlsx"],
        key="opening_excel_upload_main"
    )
    
    if uploaded_opening:
        df_op = pd.read_excel(uploaded_opening)
        st.write("**Preview dữ liệu:**")
        st.dataframe(df_op, use_container_width=True)
        
        errors_op = excel_service.validate_opening_balance_df(df_op)
        if errors_op:
            st.error("❌ Phát hiện lỗi trong file Excel:")
            for err in errors_op[:10]:
                st.write(f"- {err}")
        else:
            st.success(f"✅ Dữ liệu hợp lệ — sẵn sàng import {len(df_op)} dòng số dư.")
            if st.button("🚀 Cập nhật số dư đầu kỳ hàng loạt", type="primary", key="btn_import_opening_main", use_container_width=True):
                db = get_session()
                success, fail, errs = excel_service.import_opening_balances(
                    db, df_op, actor=current_user.full_name
                )
                db.close()
                if fail == 0:
                    st.success(f"🎉 Import thành công {success} dòng số dư đầu kỳ!")
                    st.rerun()
                else:
                    st.error(f"❌ Có {fail} dòng bị lỗi:")
                    for e in errs[:10]:
                        st.write(f"- {e}")
