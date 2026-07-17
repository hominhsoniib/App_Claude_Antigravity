import streamlit as st
import pandas as pd
from database.db import get_session
from models.models import Customer, Contact, Product, QuotationHeader, SalesUser, QuoteStatus
from services import quotation_service as qs
from services import approval_service as aps
from services import pdf_service
from services import excel_service
from email_module import email_service
from auth.session import require_login
from auth.rbac import PermissionDenied
import io

st.set_page_config(page_title="Báo giá - QUOTEFLOW OS", page_icon="📝", layout="wide")

current_user = require_login()
db = get_session()

st.title("📝 Quản lý Báo giá")

tab1, tab2 = st.tabs(["📄 Danh sách báo giá", "➕ Tạo báo giá mới"])

STATUS_COLOR = {
    QuoteStatus.DRAFT.value: "⚪", QuoteStatus.PENDING_MANAGER.value: "🟡",
    QuoteStatus.PENDING_DIRECTOR.value: "🟠", QuoteStatus.APPROVED.value: "🟢",
    QuoteStatus.SENT.value: "🔵", QuoteStatus.NEGOTIATING.value: "🟣",
    QuoteStatus.WON.value: "✅", QuoteStatus.LOST.value: "❌",
    QuoteStatus.EXPIRED.value: "⏰", QuoteStatus.REJECTED.value: "🚫",
}

with tab1:
    headers = db.query(QuotationHeader).order_by(QuotationHeader.id.desc()).all()
    rows = [{
        "ID": h.id, "Số báo giá": h.quote_no,
        "Khách hàng": h.customer.name if h.customer else "",
        "NV": h.sales_rep.full_name if h.sales_rep else "",
        "Ngày": h.quote_date.strftime("%d/%m/%Y"),
        "Hiệu lực đến": h.valid_until.strftime("%d/%m/%Y") if h.valid_until else "",
        "Trạng thái": f"{STATUS_COLOR.get(h.status.value,'')} {h.status.value}",
        "Giá trị (đ)": f"{h.grand_total:,.0f}" if h.grand_total is not None else "0",
    } for h in headers]
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🔍 Chi tiết báo giá")
    if headers:
        pick_id = st.selectbox("Chọn báo giá", options=[h.id for h in headers],
                                format_func=lambda hid: next(h.quote_no for h in headers if h.id == hid))
        header = db.query(QuotationHeader).get(pick_id)

        c1, c2, c3 = st.columns(3)
        
        status_val = header.status.value
        # Xác định màu sắc hiển thị động theo trạng thái
        if "Duyệt" in status_val or "Win" in status_val or "Approved" in status_val or "Thành công" in status_val:
            st_color = "#16A34A" # Xanh lá
        elif "Nháp" in status_val:
            st_color = "#4B5563" # Xám
        elif "Chờ" in status_val or "Đang" in status_val:
            st_color = "#D97706" # Vàng cam
        elif "Từ chối" in status_val or "Lost" in status_val or "Thất bại" in status_val:
            st_color = "#DC2626" # Đỏ
        else:
            st_color = "#2563EB" # Xanh dương
            
        c1.markdown(
            f"""
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px 16px; border-radius: 8px; min-height: 80px;">
                <span style="font-size: 13px; color: #64748B; font-weight: 500;">Trạng thái</span><br>
                <span style="font-size: 18px; color: {st_color}; font-weight: 700;">{status_val}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        c2.markdown(
            f"""
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px 16px; border-radius: 8px; min-height: 80px;">
                <span style="font-size: 13px; color: #64748B; font-weight: 500;">Tổng giá trị</span><br>
                <span style="font-size: 18px; color: #1E293B; font-weight: 700; white-space: nowrap;">{header.grand_total:,.0f} đ</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        c3.markdown(
            f"""
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px 16px; border-radius: 8px; min-height: 80px;">
                <span style="font-size: 13px; color: #64748B; font-weight: 500;">Phiên bản hiện tại</span><br>
                <span style="font-size: 18px; color: #1E293B; font-weight: 700;">v{header.current_version}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write(f"**Khách hàng:** {header.customer.name if header.customer else ''}  |  "
                 f"**NV:** {header.sales_rep.full_name if header.sales_rep else ''}")
        st.write(f"**Điều kiện thanh toán:** {header.payment_terms}")
        st.write(f"**Điều kiện giao hàng:** {header.delivery_terms}  |  **Thời gian giao:** {header.lead_time}")

        st.write("**Chi tiết dòng hàng:**")
        line_rows = [{
            "Sản phẩm": d.product.name if d.product else "", "SL": d.qty,
            "Đơn giá (đ)": f"{d.unit_price:,.0f}", "CK%": f"{d.discount_pct}%", "VAT%": f"{d.vat_pct}%",
            "Thành tiền (đ)": f"{d.line_total:,.0f}",
        } for d in header.details]
        st.dataframe(pd.DataFrame(line_rows), use_container_width=True, hide_index=True)

        colA, colB, colC, colD, colE = st.columns(5)
        with colA:
            if header.status == QuoteStatus.DRAFT:
                if st.button("📤 Gửi duyệt", use_container_width=True):
                    aps.submit_for_approval(db, header.id, current_user.full_name)
                    st.success("Đã gửi duyệt")
                    st.rerun()
        with colB:
            if header.status == QuoteStatus.APPROVED:
                if st.button("✉️ Đánh dấu đã gửi KH", use_container_width=True):
                    aps.mark_sent(db, header.id, current_user.full_name)
                    st.rerun()
        with colC:
            if header.status in (QuoteStatus.SENT,):
                if st.button("🤝 Đang đàm phán", use_container_width=True):
                    aps.mark_negotiating(db, header.id, current_user.full_name)
                    st.rerun()
        with colD:
            if header.status in (QuoteStatus.SENT, QuoteStatus.NEGOTIATING, QuoteStatus.APPROVED):
                if st.button("✅ Chốt đơn (Win)", use_container_width=True):
                    aps.mark_won(db, header.id, current_user.full_name)
                    st.rerun()
        with colE:
            if header.status in (QuoteStatus.SENT, QuoteStatus.NEGOTIATING, QuoteStatus.APPROVED):
                if st.button("❌ Mất đơn (Lost)", use_container_width=True):
                    aps.mark_lost(db, header.id, current_user.full_name)
                    st.rerun()

        st.divider()
        colX, colY, colZ = st.columns(3)
        with colX:
            if st.button("📄 Xuất PDF báo giá", type="primary"):
                path = pdf_service.generate_quote_pdf(header)
                with open(path, "rb") as f:
                    st.download_button("⬇️ Tải file PDF", f, file_name=f"{header.quote_no}.pdf",
                                        mime="application/pdf")
        with colY:
            buf = excel_service.export_quotation_excel(header)
            st.download_button("⬇️ Tải file Excel", buf, file_name=f"{header.quote_no}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with colZ:
            with st.popover("✉️ Gửi email cho khách hàng"):
                contacts = db.query(Contact).filter(Contact.customer_id == header.customer_id).all()
                default_email = contacts[0].email if contacts else (header.customer.contacts[0].email if header.customer and header.customer.contacts else "")
                to_email = st.text_input("Email người nhận", value=default_email or "", key=f"email_{header.id}")
                note = st.text_area("Lời nhắn thêm (tùy chọn)", key=f"note_{header.id}")
                if st.button("Gửi ngay", key=f"send_{header.id}", type="primary"):
                    if not to_email:
                        st.error("Vui lòng nhập email người nhận.")
                    else:
                        pdf_path = pdf_service.generate_quote_pdf(header)
                        success, msg = email_service.send_quotation_email(db, header, to_email, pdf_path, note)
                        if success:
                            aps.mark_sent(db, header.id, current_user.full_name)
                            st.success(msg)
                            st.rerun()
                        else:
                            st.warning(msg)

        with st.expander("➕ Thêm dòng sản phẩm vào báo giá này"):
            products = db.query(Product).all()
            if products and header.status == QuoteStatus.DRAFT:
                with st.form(f"add_line_{header.id}"):
                    p_id = st.selectbox("Sản phẩm", options=[p.id for p in products],
                                         format_func=lambda pid: next(p.name for p in products if p.id == pid))
                    qty = st.number_input("Số lượng", min_value=1.0, value=1.0)
                    prod = next(p for p in products if p.id == p_id)
                    unit_price = st.number_input("Đơn giá", value=float(prod.list_price))
                    discount_pct = st.number_input("Chiết khấu %", min_value=0.0,
                                                    max_value=float(prod.max_discount_pct or 100), value=0.0)
                    if st.form_submit_button("Thêm dòng"):
                        qs.add_line(db, header.id, p_id, qty, unit_price, discount_pct, prod.vat_pct)
                        st.rerun()
            elif header.status != QuoteStatus.DRAFT:
                st.info("Chỉ có thể thêm dòng khi báo giá ở trạng thái Nháp.")

        with st.expander("📜 Lịch sử phiên bản"):
            if st.button("💾 Lưu snapshot phiên bản hiện tại"):
                qs.snapshot_version(db, header.id, current_user.full_name, "Lưu thủ công")
                st.success("Đã lưu phiên bản")
                st.rerun()
            for v in header.versions:
                st.write(f"- v{v.version_no} — {v.changed_by} — {v.changed_at.strftime('%d/%m/%Y %H:%M')} — {v.change_note}")

with tab2:
    customers = db.query(Customer).all()
    sales_users = db.query(SalesUser).all()
    if not customers:
        st.info("Chưa có khách hàng nào. Vui lòng thêm khách hàng trước.")
    else:
        create_mode = st.radio("Phương thức tạo báo giá", ["📝 Nhập liệu thủ công", "📥 Import từ file Excel mẫu chuẩn", "📥 Import từ file Excel mẫu OMRI"], horizontal=True, key="quote_create_mode")

        if create_mode == "📝 Nhập liệu thủ công":
            with st.form("new_quotation"):
                c1, c2 = st.columns(2)
                with c1:
                    cust_id = st.selectbox("Khách hàng*", options=[c.id for c in customers],
                                            format_func=lambda cid: next(c.name for c in customers if c.id == cid))
                    rep_id = st.selectbox("Nhân viên phụ trách*", options=[u.id for u in sales_users],
                                           format_func=lambda uid: next(u.full_name for u in sales_users if u.id == uid),
                                           index=[u.id for u in sales_users].index(current_user.id) if current_user.id in [u.id for u in sales_users] else 0)
                    valid_days = st.number_input("Hiệu lực (số ngày)", min_value=1, value=15)
                with c2:
                    payment_terms = st.text_input("Điều kiện thanh toán", value="Thanh toán 50% đặt cọc, 50% khi giao hàng")
                    delivery_terms = st.text_input("Điều kiện giao hàng", value="Giao hàng tại kho khách hàng")
                    lead_time = st.text_input("Thời gian giao hàng", value="7 ngày làm việc")
                note = st.text_area("Ghi chú")
                shipping_fee = st.number_input("Chi phí vận chuyển", min_value=0.0, step=10000.0)
                other_fee = st.number_input("Chi phí khác", min_value=0.0, step=10000.0)

                submitted = st.form_submit_button("Tạo báo giá", type="primary")
                if submitted:
                    header = qs.create_quotation(
                        db, cust_id, rep_id, valid_days=valid_days,
                        payment_terms=payment_terms, delivery_terms=delivery_terms,
                        lead_time=lead_time, note=note, shipping_fee=shipping_fee,
                        other_fee=other_fee, actor=current_user.full_name,
                    )
                    st.success(f"✅ Đã tạo báo giá **{header.quote_no}**. Vào tab 'Danh sách báo giá' để thêm dòng sản phẩm.")
                    
        elif create_mode == "📥 Import từ file Excel mẫu chuẩn":
            cust_id = st.selectbox("Khách hàng*", options=[c.id for c in customers],
                                    format_func=lambda cid: next(c.name for c in customers if c.id == cid), key="std_xl_cust")
            rep_id = st.selectbox("Nhân viên phụ trách*", options=[u.id for u in sales_users],
                                   format_func=lambda uid: next(u.full_name for u in sales_users if u.id == uid),
                                   index=[u.id for u in sales_users].index(current_user.id) if current_user.id in [u.id for u in sales_users] else 0, key="std_xl_rep")
            
            st.markdown("**Bước 1: Tải file mẫu**")
            st.caption("File mẫu sẽ điền sẵn danh sách sản phẩm hiện có để bạn nhập số lượng và chiết khấu.")
            template_buf = excel_service.build_quotation_import_template(db)
            st.download_button(
                "⬇️ Tải file Excel mẫu Báo giá (.xlsx)",
                template_buf,
                file_name="template_tao_bao_gia.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_dl_quote_tpl_std",
                use_container_width=True
            )
            
            st.write("")
            st.markdown("**Bước 2: Tải lên file Excel báo giá đã nhập**")
            uploaded_file = st.file_uploader("Chọn file Excel báo giá mẫu chuẩn (.xlsx)", type=["xlsx"], key="std_quote_uploader")
            
            if uploaded_file:
                df = pd.read_excel(uploaded_file)
                st.write("**Preview dữ liệu:**")
                st.dataframe(df, use_container_width=True)
                
                errors = excel_service.validate_quotation_import_df(df)
                if errors:
                    st.error("❌ Phát hiện lỗi trong file Excel:")
                    for err in errors[:10]:
                        st.write(f"- {err}")
                else:
                    try:
                        valid_qty_count = sum(1 for _, row in df.iterrows() if float(row.get("qty", 0) or 0) > 0)
                    except:
                        valid_qty_count = 0
                    
                    st.success(f"✅ Dữ liệu hợp lệ — tìm thấy {valid_qty_count} dòng sản phẩm có số lượng > 0.")
                    
                    if st.button("🚀 Khởi tạo báo giá từ Excel mẫu chuẩn", type="primary", key="btn_import_std_quote_run", use_container_width=True):
                        with st.spinner("Đang khởi tạo báo giá..."):
                            success, fail, errs, quote_no = excel_service.import_quotation_from_excel(
                                db, df, cust_id, rep_id, actor=current_user.full_name
                            )
                        if fail == 0 and quote_no:
                            st.success(f"🎉 Import báo giá **{quote_no}** thành công với {success} dòng sản phẩm!")
                            st.info("💡 Hãy chuyển sang tab 'Danh sách báo giá' để kiểm tra chi tiết và tải file PDF/Excel!")
                            st.rerun()
                        else:
                            st.error(f"❌ Khởi tạo thất bại:")
                            for e in errs[:10]:
                                st.write(f"- {e}")
                                
        else:
            # Excel import form
            cust_id = st.selectbox("Khách hàng*", options=[c.id for c in customers],
                                    format_func=lambda cid: next(c.name for c in customers if c.id == cid), key="xl_cust")
            rep_id = st.selectbox("Nhân viên phụ trách*", options=[u.id for u in sales_users],
                                   format_func=lambda uid: next(u.full_name for u in sales_users if u.id == uid),
                                   index=[u.id for u in sales_users].index(current_user.id) if current_user.id in [u.id for u in sales_users] else 0, key="xl_rep")
            
            uploaded_file = st.file_uploader("Tải lên file Excel báo giá mẫu OMRI (.xlsx)", type=["xlsx"], key="quote_file_uploader")
            if uploaded_file:
                file_key = f"file_{uploaded_file.name}_{uploaded_file.size}"
                if "last_file_key" not in st.session_state or st.session_state.last_file_key != file_key:
                    st.session_state.last_file_key = file_key
                    st.session_state.file_bytes = uploaded_file.read()
                    import openpyxl
                    try:
                        wb = openpyxl.load_workbook(io.BytesIO(st.session_state.file_bytes), read_only=True)
                        st.session_state.sheet_names = wb.sheetnames
                    except Exception as e:
                        st.session_state.sheet_names = []
                        st.error(f"❌ Không thể đọc cấu trúc file Excel: {e}")
                
                if st.session_state.get("sheet_names"):
                    try:
                        selected_sheet = st.selectbox("Chọn Sheet chứa bảng báo giá", options=st.session_state.sheet_names, key="xl_sheet")
                        
                        if st.button("🚀 Khởi tạo báo giá từ Excel", type="primary", key="xl_import_btn"):
                            from services.excel_service import parse_omri_quotation_excel
                            from models.models import Product
                            
                            with st.spinner("Đang phân tích dữ liệu và tạo báo giá..."):
                                items = parse_omri_quotation_excel(st.session_state.file_bytes, selected_sheet)
                            
                            if not items:
                                st.warning("⚠️ Không tìm thấy sản phẩm nào trong sheet này.")
                            else:
                                # Tạo báo giá header
                                header = qs.create_quotation(
                                    db, cust_id, rep_id, valid_days=15,
                                    payment_terms="Thanh toán theo chính sách công ty",
                                    delivery_terms="Giao hàng tại kho khách hàng",
                                    lead_time="7 ngày làm việc",
                                    note=f"Import từ Excel mẫu OMRI - Sheet: {selected_sheet}",
                                    shipping_fee=0, other_fee=0, actor=current_user.full_name,
                                )
                                
                                # Thêm các dòng sản phẩm
                                for item in items:
                                    # Tìm xem sản phẩm tồn tại chưa (tìm theo tên khớp chính xác)
                                    prod = db.query(Product).filter(Product.name == item["name"]).first()
                                    if not prod:
                                        # Tự động tạo SKU mới
                                        last_prod = db.query(Product).order_by(Product.id.desc()).first()
                                        next_id = (last_prod.id + 1) if last_prod else 1
                                        sku = f"SP-AUTO-{next_id:04d}"
                                        
                                        prod = Product(
                                            sku=sku, name=item["name"], spec=item["spec"],
                                            unit=item["unit"], cost_price=item["price"] * 0.7, # Giả định giá vốn = 70% giá bán
                                            list_price=item["price"], max_discount_pct=15, vat_pct=10,
                                            category="Import từ Excel", warehouse="Kho chính", stock_qty=100
                                        )
                                        db.add(prod)
                                        db.flush()
                                    
                                    # Thêm vào chi tiết báo giá (số lượng mặc định là 1, có thể chỉnh sửa lại sau)
                                    qs.add_line(db, header.id, prod.id, qty=1, unit_price=prod.list_price, discount_pct=0, vat_pct=prod.vat_pct)
                                
                                st.success(f"✅ Đã tạo báo giá **{header.quote_no}** và import thành công {len(items)} dòng sản phẩm!")
                                st.info("💡 Bạn hãy chuyển sang tab 'Danh sách báo giá' để điều chỉnh số lượng/chiết khấu và tải file PDF/Excel!")
                    except Exception as e:
                        st.error(f"❌ Có lỗi xảy ra khi đọc file Excel: {e}")

db.close()
