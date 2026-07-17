import streamlit as st
import pandas as pd
from database.db import get_session
from models.models import QuotationHeader, QuoteStatus, SalesUser, RoleEnum
from services import approval_service as aps
from auth.rbac import PermissionDenied
from auth.session import require_login

st.set_page_config(page_title="Phê duyệt - QUOTEFLOW OS", page_icon="✅", layout="wide")

current_user = require_login()

db = get_session()

st.title("✅ Phê duyệt Báo giá")
st.caption("Workflow: Nhân viên KD → Trưởng phòng duyệt → Giám đốc duyệt → Gửi khách hàng")

role = current_user.role

if role == RoleEnum.SALES_MANAGER:
    pending = db.query(QuotationHeader).filter(
        QuotationHeader.status == QuoteStatus.PENDING_MANAGER).all()
    st.subheader(f"📥 Báo giá chờ Trưởng phòng duyệt ({len(pending)})")
elif role in (RoleEnum.SALES_DIRECTOR, RoleEnum.CEO):
    pending = db.query(QuotationHeader).filter(
        QuotationHeader.status == QuoteStatus.PENDING_DIRECTOR).all()
    st.subheader(f"📥 Báo giá chờ Giám đốc duyệt ({len(pending)})")
else:
    pending = db.query(QuotationHeader).filter(
        QuotationHeader.status.in_([QuoteStatus.PENDING_MANAGER, QuoteStatus.PENDING_DIRECTOR])).all()
    st.subheader(f"📥 Tất cả báo giá đang chờ duyệt ({len(pending)}) — chế độ xem")
    st.info("Vai trò của bạn không có quyền duyệt trực tiếp, chỉ có thể xem danh sách.")

if not pending:
    st.success("🎉 Không có báo giá nào đang chờ duyệt.")
else:
    for h in pending:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2.5, 0.8, 1.7])
            with c1:
                st.write(f"**{h.quote_no}** — {h.customer.name if h.customer else ''}")
                st.caption(f"NV: {h.sales_rep.full_name if h.sales_rep else ''} | "
                           f"Ngày: {h.quote_date.strftime('%d/%m/%Y')}")
                max_discount = max([d.discount_pct for d in h.details], default=0)
                st.caption(f"Chiết khấu tối đa trong báo giá: {max_discount}%")
                
                # --- HIỂN THỊ TIẾN TRÌNH LUỒNG PHÊ DUYỆT 2 CẤP ---
                from models.models import ApprovalWorkflow
                flow_logs = db.query(ApprovalWorkflow).filter(ApprovalWorkflow.header_id == h.id).all()
                
                tp_status = "⚪ Chưa thực hiện"
                gd_status = "⚪ Chưa thực hiện"
                
                for log in flow_logs:
                    if "Trưởng phòng" in log.step:
                        if log.action == "Approved":
                            tp_status = f"✅ **Đã duyệt** bởi {log.approver} ({log.acted_at.strftime('%d/%m/%Y %H:%M') if log.acted_at else ''})"
                            if log.comment:
                                tp_status += f" - *\"{log.comment}\"*"
                        elif log.action == "Rejected":
                            tp_status = f"❌ **Từ chối** bởi {log.approver} ({log.acted_at.strftime('%d/%m/%Y %H:%M') if log.acted_at else ''})"
                            if log.comment:
                                tp_status += f" - *\"{log.comment}\"*"
                        elif log.action == "Pending":
                            tp_status = "🟡 **Đang chờ duyệt**"
                    elif "Giám đốc" in log.step or "CEO" in log.step:
                        if log.action == "Approved":
                            gd_status = f"✅ **Đã duyệt** bởi {log.approver} ({log.acted_at.strftime('%d/%m/%Y %H:%M') if log.acted_at else ''})"
                            if log.comment:
                                gd_status += f" - *\"{log.comment}\"*"
                        elif log.action == "Rejected":
                            gd_status = f"❌ **Từ chối** bởi {log.approver} ({log.acted_at.strftime('%d/%m/%Y %H:%M') if log.acted_at else ''})"
                            if log.comment:
                                gd_status += f" - *\"{log.comment}\"*"
                        elif log.action == "Pending":
                            gd_status = "🟡 **Đang chờ duyệt**"
                
                if h.status == QuoteStatus.PENDING_MANAGER and tp_status == "⚪ Chưa thực hiện":
                    tp_status = "🟡 **Đang chờ duyệt (Bạn đang ở bước này)**" if role == RoleEnum.SALES_MANAGER else "🟡 **Đang chờ duyệt**"
                    gd_status = "⚪ **Chưa đến lượt (Chờ Cấp 1 duyệt)**"
                    
                if h.status == QuoteStatus.PENDING_DIRECTOR:
                    if tp_status == "⚪ Chưa thực hiện":
                        tp_status = "➖ *Không qua bước này (Duyệt vượt cấp)*"
                    gd_status = "🟡 **Đang chờ duyệt (Bạn đang ở bước này)**" if role in (RoleEnum.SALES_DIRECTOR, RoleEnum.CEO) else "🟡 **Đang chờ duyệt**"
                
                st.markdown(
                    f"""
                    <div style="background-color: #F8FAFC; padding: 10px; border-radius: 8px; border: 1px dashed #E2E8F0; margin-top: 8px;">
                        <span style="font-size: 13px; color: #475569; font-weight: bold; display: block; margin-bottom: 4px;">🔍 TIẾN TRÌNH DUYỆT 2 CẤP:</span>
                        <span style="font-size: 13px; color: #334155; display: block; margin-bottom: 2px;">• <b>Cấp 1 (Trưởng phòng):</b> {tp_status}</span>
                        <span style="font-size: 13px; color: #334155; display: block;">• <b>Cấp 2 (Giám đốc/CEO):</b> {gd_status}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with c2:
                st.markdown(
                    f"""
                    <div style="padding-top: 10px;">
                        <span style="font-size: 13px; color: #64748B; font-weight: 500;">Giá trị</span><br>
                        <span style="font-size: 18px; color: #1E293B; font-weight: 700; white-space: nowrap;">{h.grand_total:,.0f} đ</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with c3:
                comment = st.text_input(
                    "Ý kiến phê duyệt / Lý do từ chối", 
                    key=f"cmt_{h.id}", 
                    placeholder="Nhập ghi chú tại đây...",
                    label_visibility="visible"
                )
                
                st.write("")
                col_appr, col_rej = st.columns(2)
                
                if role == RoleEnum.SALES_MANAGER and h.status == QuoteStatus.PENDING_MANAGER:
                    with col_appr:
                        approve = st.button("✅ Duyệt", key=f"appr_{h.id}", use_container_width=True, type="primary")
                    with col_rej:
                        reject = st.button("❌ Từ chối", key=f"rej_{h.id}", use_container_width=True)
                    try:
                        if approve:
                            aps.act_on_approval(db, h.id, "Trưởng phòng duyệt", current_user.full_name, "Approved", role, comment.strip())
                            st.rerun()
                        if reject:
                            reason = comment.strip() if comment.strip() else "Từ chối bởi trưởng phòng"
                            aps.act_on_approval(db, h.id, "Trưởng phòng duyệt", current_user.full_name, "Rejected", role, reason)
                            st.rerun()
                    except PermissionDenied as e:
                        st.error(f"🚫 {e}")
                elif role in (RoleEnum.SALES_DIRECTOR, RoleEnum.CEO) and h.status == QuoteStatus.PENDING_DIRECTOR:
                    with col_appr:
                        approve = st.button("✅ Duyệt", key=f"appr_{h.id}", use_container_width=True, type="primary")
                    with col_rej:
                        reject = st.button("❌ Từ chối", key=f"rej_{h.id}", use_container_width=True)
                    try:
                        if approve:
                            aps.act_on_approval(db, h.id, "Giám đốc duyệt", current_user.full_name, "Approved", role, comment.strip())
                            st.rerun()
                        if reject:
                            reason = comment.strip() if comment.strip() else "Từ chối bởi giám đốc"
                            aps.act_on_approval(db, h.id, "Giám đốc duyệt", current_user.full_name, "Rejected", role, reason)
                            st.rerun()
                    except PermissionDenied as e:
                        st.error(f"🚫 {e}")
            
            # --- Xem chi tiết sản phẩm trước khi duyệt ---
            with st.expander("🔍 Xem chi tiết đơn hàng (Kiểm tra trước khi duyệt)"):
                details_rows = []
                for i, d in enumerate(h.details, start=1):
                    details_rows.append({
                        "STT": i,
                        "Sản phẩm": d.product.name if d.product else "",
                        "Quy cách": d.product.spec if d.product else "",
                        "ĐVT": d.product.unit if d.product else "",
                        "SL": d.qty,
                        "Đơn giá": f"{d.unit_price:,.0f} đ",
                        "CK%": f"{d.discount_pct}%",
                        "VAT%": f"{d.vat_pct}%",
                        "Thành tiền": f"{d.line_total:,.0f} đ"
                    })
                if details_rows:
                    st.dataframe(pd.DataFrame(details_rows), use_container_width=True, hide_index=True)
                else:
                    st.info("Báo giá này chưa có sản phẩm nào.")

st.divider()
st.subheader("📜 Lịch sử phê duyệt gần đây")
from models.models import ApprovalWorkflow
logs = db.query(ApprovalWorkflow).order_by(ApprovalWorkflow.id.desc()).limit(20).all()
rows = [{
    "Báo giá": db.query(QuotationHeader).get(l.header_id).quote_no if db.query(QuotationHeader).get(l.header_id) else "",
    "Bước": l.step, "Người duyệt": l.approver, "Kết quả": l.action,
    "Ghi chú": l.comment, "Thời gian": l.acted_at.strftime("%d/%m/%Y %H:%M"),
} for l in logs]
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

db.close()
