import streamlit as st
import pandas as pd
from datetime import datetime
from database.db import get_session
from models.models import Product, InventoryTransaction
from auth.session import require_login
from services import inventory_service as inv_s
from services import excel_service

st.set_page_config(page_title="Tồn kho - QUOTEFLOW OS", page_icon="📦", layout="wide")

current_user = require_login()
db = get_session()

st.title("📦 Quản lý Nhập Xuất Tồn kho")

# --- Lấy dữ liệu ---
products = db.query(Product).all()
transactions = db.query(InventoryTransaction).order_by(InventoryTransaction.id.desc()).all()

# --- Tính toán thống kê ---
total_products = len(products)
total_stock = sum(p.stock_qty for p in products)
low_stock_limit = 15  # Cảnh báo khi tồn kho < 15
low_stock_items = sum(1 for p in products if p.stock_qty < low_stock_limit)

# --- Thống kê dạng thẻ ---
c1, c2, c3 = st.columns(3)
c1.markdown(
    f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 16px; border-radius: 8px; min-height: 90px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <span style="font-size: 13px; color: #64748B; font-weight: 500;">Tổng số mặt hàng</span><br>
        <span style="font-size: 24px; color: #1E293B; font-weight: 700;">{total_products}</span>
    </div>
    """,
    unsafe_allow_html=True
)
c2.markdown(
    f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 16px; border-radius: 8px; min-height: 90px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <span style="font-size: 13px; color: #64748B; font-weight: 500;">Tổng lượng tồn kho</span><br>
        <span style="font-size: 24px; color: #2563EB; font-weight: 700;">{total_stock:,.1f}</span>
    </div>
    """,
    unsafe_allow_html=True
)
c3.markdown(
    f"""
    <div style="background-color: #FEF2F2; border: 1px solid #FEE2E2; padding: 16px; border-radius: 8px; min-height: 90px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <span style="font-size: 13px; color: #991B1B; font-weight: 500;">Sản phẩm sắp hết hàng (&lt;{low_stock_limit})</span><br>
        <span style="font-size: 24px; color: #DC2626; font-weight: 700;">{low_stock_items}</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Báo cáo tồn kho", "📥/📤 Nhập xuất kho thủ công", "📜 Lịch sử nhập xuất", "📦 Khai báo số dư đầu kỳ"])

# --- TAB 1: BÁO CÁO TỒN KHO ---
with tab1:
    st.subheader("📊 Tình trạng tồn kho hiện tại")
    
    # Bộ lọc tìm kiếm
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        search_query = st.text_input("🔍 Tìm theo tên hoặc mã sản phẩm", "")
    with col_f2:
        categories = sorted(list(set(p.category for p in products if p.category)))
        cat_filter = st.selectbox("Lọc theo nhóm hàng", ["Tất cả"] + categories)

    # Chuyển đổi dữ liệu sang Pandas DataFrame
    prod_rows = []
    for p in products:
        # Áp dụng bộ lọc tìm kiếm
        if search_query and (search_query.lower() not in p.name.lower() and search_query.lower() not in p.sku.lower()):
            continue
        # Áp dụng bộ lọc nhóm hàng
        if cat_filter != "Tất cả" and p.category != cat_filter:
            continue
            
        status = "Bình thường"
        if p.stock_qty < 0:
            status = "Âm kho 🚨"
        elif p.stock_qty == 0:
            status = "Hết hàng 🛑"
        elif p.stock_qty < low_stock_limit:
            status = "Tồn kho thấp ⚠️"
            
        prod_rows.append({
            "Mã sản phẩm (SKU)": p.sku,
            "Tên sản phẩm": p.name,
            "Nhóm hàng": p.category or "-",
            "Kho": p.warehouse or "Mặc định",
            "ĐVT": p.unit or "Cái",
            "Giá vốn (đ)": p.cost_price,
            "Giá bán (đ)": p.list_price,
            "Số lượng tồn": p.stock_qty,
            "Trạng thái": status
        })
        
    if prod_rows:
        df_prod = pd.DataFrame(prod_rows)
        
        # Định dạng tô màu cho Trạng thái
        def color_status(val):
            if "🚨" in val or "🛑" in val:
                return "color: #DC2626; font-weight: bold; background-color: #FEF2F2;"
            elif "⚠️" in val:
                return "color: #D97706; font-weight: bold; background-color: #FFFBEB;"
            return "color: #16A34A; font-weight: bold;"

        st.dataframe(
            df_prod.style.format({
                "Giá vốn (đ)": "{:,.0f}",
                "Giá bán (đ)": "{:,.0f}",
                "Số lượng tồn": "{:,.1f}"
            }).map(color_status, subset=["Trạng thái"]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Không tìm thấy sản phẩm nào phù hợp với bộ lọc.")

# --- TAB 2: NHẬP XUẤT THỦ CÔNG ---
with tab2:
    st.subheader("📥/📤 Thực hiện giao dịch nhập xuất kho")
    
    if not products:
        st.info("Chưa có sản phẩm nào trong hệ thống để thực hiện giao dịch.")
    else:
        with st.form("inventory_transaction_form"):
            col_t1, col_t2 = st.columns(2)
            
            with col_t1:
                # Tạo danh sách sản phẩm để chọn
                product_options = {p.id: f"{p.sku} - {p.name} (Tồn hiện tại: {p.stock_qty:,.1f})" for p in products}
                selected_prod_id = st.selectbox(
                    "Chọn sản phẩm*",
                    options=list(product_options.keys()),
                    format_func=lambda pid: product_options[pid]
                )
                
                transaction_type = st.selectbox(
                    "Loại giao dịch*",
                    options=["IMPORT", "EXPORT", "ADJUST"],
                    format_func=lambda x: "📥 Nhập kho (IMPORT)" if x == "IMPORT" else ("📤 Xuất kho (EXPORT)" if x == "EXPORT" else "🔧 Điều chỉnh tồn kho (ADJUST)")
                )
                
                qty = st.number_input(
                    "Số lượng*",
                    min_value=0.0,
                    value=1.0,
                    step=1.0,
                    help="Nhập số lượng giao dịch đối với Nhập/Xuất, hoặc Tồn kho mới đối với Điều chỉnh."
                )
                
            with col_t2:
                reference_no = st.text_input(
                    "Mã tham chiếu / Số chứng từ",
                    value="",
                    placeholder="Ví dụ: PN001, PX002, MANUAL, v.v."
                )
                
                note = st.text_area(
                    "Ghi chú chi tiết",
                    value="",
                    placeholder="Lý do nhập xuất, ghi chú điều chỉnh..."
                )
                
            st.write("")
            submit_btn = st.form_submit_button("Thực hiện giao dịch", type="primary")
            
            if submit_btn:
                try:
                    # Kiểm tra số lượng
                    if transaction_type in ["IMPORT", "EXPORT"] and qty <= 0:
                        st.error("Số lượng giao dịch nhập/xuất phải lớn hơn 0.")
                    else:
                        ref_val = reference_no.strip() if reference_no.strip() else "MANUAL"
                        note_val = note.strip()
                        
                        # Thực hiện giao dịch
                        tx = inv_s.add_transaction(
                            db=db,
                            product_id=selected_prod_id,
                            transaction_type=transaction_type,
                            qty=qty,
                            reference_no=ref_val,
                            note=note_val,
                            actor=current_user.full_name
                        )
                        
                        st.success(f"🎉 Giao dịch thực hiện thành công!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Có lỗi xảy ra: {str(e)}")

# --- TAB 3: LỊCH SỬ GIAO DỊCH ---
with tab3:
    st.subheader("📜 Nhật ký lịch sử nhập xuất tồn kho")
    
    # Bộ lọc lịch sử
    col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
    with col_h1:
        tx_search = st.text_input("🔍 Tìm theo Mã báo giá / Mã chứng từ hoặc SKU", "")
    with col_h2:
        tx_type_filter = st.selectbox("Lọc loại giao dịch", ["Tất cả", "Nhập kho (IMPORT)", "Xuất kho (EXPORT)", "Điều chỉnh (ADJUST)", "Số dư đầu kỳ (OPENING)"])
    with col_h3:
        # Cho phép xuất báo cáo giao dịch nếu muốn
        pass
        
    # Chuyển đổi dữ liệu sang Pandas DataFrame
    tx_rows = []
    
    tx_mapping = {
        "IMPORT": "Nhập kho (IMPORT)",
        "EXPORT": "Xuất kho (EXPORT)",
        "ADJUST": "Điều chỉnh (ADJUST)",
        "OPENING": "Số dư đầu kỳ (OPENING)"
    }
    
    for tx in transactions:
        tx_type_name = tx_mapping.get(tx.transaction_type, tx.transaction_type)
        
        # Áp dụng bộ lọc tìm kiếm
        if tx_search:
            s_query = tx_search.lower()
            sku_match = tx.product and s_query in tx.product.sku.lower()
            name_match = tx.product and s_query in tx.product.name.lower()
            ref_match = tx.reference_no and s_query in tx.reference_no.lower()
            if not (sku_match or name_match or ref_match):
                continue
                
        # Áp dụng bộ lọc loại giao dịch
        if tx_type_filter != "Tất cả" and tx_type_name != tx_type_filter:
            continue
            
        tx_rows.append({
            "Thời gian": tx.created_at.strftime("%d/%m/%Y %H:%M:%S") if tx.created_at else "-",
            "Mã sản phẩm": tx.product.sku if tx.product else "-",
            "Tên sản phẩm": tx.product.name if tx.product else "-",
            "Loại giao dịch": tx_type_name,
            "Số lượng": tx.qty,
            "Chứng từ / Tham chiếu": tx.reference_no or "-",
            "Người thực hiện": tx.created_by or "-",
            "Ghi chú chi tiết": tx.note or ""
        })
        
    if tx_rows:
        df_tx = pd.DataFrame(tx_rows)
        
        # Định dạng màu cho cột loại giao dịch
        def color_tx_type(val):
            if "IMPORT" in val:
                return "color: #16A34A; font-weight: bold; background-color: #F0FDF4;"
            elif "EXPORT" in val:
                return "color: #DC2626; font-weight: bold; background-color: #FEF2F2;"
            return "color: #D97706; font-weight: bold; background-color: #FFFBEB;"
            
        st.dataframe(
            df_tx.style.format({
                "Số lượng": "{:,.1f}"
            }).map(color_tx_type, subset=["Loại giao dịch"]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Chưa có giao dịch kho nào được ghi nhận.")

# --- TAB 4: KHAI BÁO SỐ DƯ ĐẦU KỲ ---
with tab4:
    st.subheader("📦 Khai báo số dư đầu kỳ cho sản phẩm")
    st.markdown(
        """
        > **Lưu ý**: Khai báo số dư đầu kỳ sẽ thiết lập số lượng tồn kho của sản phẩm về giá trị được nhập 
        > và ghi nhận một giao dịch kho loại `Số dư đầu kỳ (OPENING)`. Việc này thường thực hiện khi khởi tạo hệ thống.
        """
    )
    
    if not products:
        st.info("Chưa có sản phẩm nào trong hệ thống.")
    else:
        # Lấy lịch sử giao dịch đầu kỳ gần nhất của các sản phẩm
        opening_txs = {
            tx.product_id: tx 
            for tx in db.query(InventoryTransaction)
            .filter(InventoryTransaction.transaction_type == "OPENING")
            .order_by(InventoryTransaction.id.asc())
            .all()
        }
        
        col_m, col_e = st.columns(2)
        
        with col_m:
            st.markdown("### ✍️ Khai báo thủ công (Từng sản phẩm)")
            with st.form("opening_balance_form"):
                product_options_o = {p.id: f"{p.sku} - {p.name} (Tồn: {p.stock_qty:,.1f})" for p in products}
                selected_prod_id_o = st.selectbox(
                    "Chọn sản phẩm*",
                    options=list(product_options_o.keys()),
                    format_func=lambda pid: product_options_o[pid],
                    key="opening_prod_select"
                )
                
                # Hiển thị thông tin nếu đã khai báo
                if selected_prod_id_o in opening_txs:
                    tx_o = opening_txs[selected_prod_id_o]
                    st.info(
                        f"ℹ️ Sản phẩm này đã khai báo đầu kỳ: **{tx_o.qty:,.1f}** "
                        f"bởi **{tx_o.created_by}** vào lúc {tx_o.created_at.strftime('%d/%m/%Y %H:%M')}."
                    )
                    
                qty_o = st.number_input(
                    "Số lượng tồn đầu kỳ*",
                    min_value=0.0,
                    value=float(opening_txs[selected_prod_id_o].qty) if selected_prod_id_o in opening_txs else 0.0,
                    step=1.0,
                    key="opening_qty_input"
                )
                
                note_o = st.text_input(
                    "Ghi chú",
                    value="Khai báo số dư đầu kỳ",
                    key="opening_note_input"
                )
                
                submit_btn_o = st.form_submit_button("Xác nhận số dư đầu kỳ", type="primary", use_container_width=True)
                
                if submit_btn_o:
                    try:
                        tx = inv_s.add_transaction(
                            db=db,
                            product_id=selected_prod_id_o,
                            transaction_type="OPENING",
                            qty=qty_o,
                            reference_no="OPENING",
                            note=note_o,
                            actor=current_user.full_name
                        )
                        st.success(f"🎉 Đã khai báo số dư đầu kỳ cho sản phẩm thành công!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Có lỗi xảy ra: {str(e)}")
                        
        with col_e:
            st.markdown("### 📥 Khai báo hàng loạt từ Excel")
            st.markdown("**Bước 1: Tải file mẫu**")
            st.caption("File mẫu sẽ tự động điền danh sách sản phẩm và mã SKU hiện có trong hệ thống.")
            
            # Tạo nút download template
            template_buf = excel_service.build_opening_balance_template(db)
            st.download_button(
                "⬇️ Tải file mẫu Số dư đầu kỳ (.xlsx)",
                template_buf,
                file_name="template_so_du_dau_ky.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_dl_opening_tpl",
                use_container_width=True
            )
            
            st.write("")
            st.markdown("**Bước 2: Tải lên file Excel số dư đầu kỳ**")
            uploaded_opening = st.file_uploader(
                "Chọn file Excel đã điền số dư (.xlsx)",
                type=["xlsx"],
                key="opening_excel_upload"
            )
            
            if uploaded_opening:
                df_op = pd.read_excel(uploaded_opening)
                st.write("*Xem trước dữ liệu:*")
                st.dataframe(df_op.head(10), use_container_width=True)
                
                errors_op = excel_service.validate_opening_balance_df(df_op)
                if errors_op:
                    st.error("❌ Phát hiện lỗi trong file Excel:")
                    for err in errors_op[:5]:
                        st.write(f"- {err}")
                    if len(errors_op) > 5:
                        st.write(f"... và {len(errors_op) - 5} lỗi khác.")
                else:
                    st.success(f"✅ Dữ liệu hợp lệ — sẵn sàng import {len(df_op)} dòng sản phẩm.")
                    
                    if st.button("🚀 Cập nhật số dư đầu kỳ hàng loạt", type="primary", key="btn_import_opening", use_container_width=True):
                        success, fail, errs = excel_service.import_opening_balances(
                            db, df_op, actor=current_user.full_name
                        )
                        if fail == 0:
                            st.success(f"🎉 Import thành công {success} dòng số dư đầu kỳ!")
                            st.rerun()
                        else:
                            st.error(f"❌ Có {fail} dòng bị lỗi:")
                            for e in errs[:10]:
                                st.write(f"- {e}")
                                
        st.divider()
        st.write("**Danh sách trạng thái khai báo đầu kỳ của sản phẩm:**")
        
        status_rows = []
        for p in products:
            declared = p.id in opening_txs
            status_rows.append({
                "Mã hàng (SKU)": p.sku,
                "Tên hàng": p.name,
                "Trạng thái": "Đã khai báo" if declared else "Chưa khai báo",
                "Số dư đầu kỳ": opening_txs[p.id].qty if declared else 0.0,
                "Tồn hiện tại": p.stock_qty,
                "Người thực hiện": opening_txs[p.id].created_by if declared else "-",
                "Thời gian khai báo": opening_txs[p.id].created_at.strftime("%d/%m/%Y %H:%M:%S") if declared and opening_txs[p.id].created_at else "-",
            })
            
        df_status = pd.DataFrame(status_rows)
        
        def color_opening_status(val):
            if val == "Đã khai báo":
                return "color: #16A34A; font-weight: bold;"
            return "color: #DC2626; font-style: italic;"
            
        st.dataframe(
            df_status.style.format({
                "Số dư đầu kỳ": "{:,.1f}",
                "Tồn hiện tại": "{:,.1f}"
            }).map(color_opening_status, subset=["Trạng thái"]),
            use_container_width=True,
            hide_index=True
        )

db.close()
