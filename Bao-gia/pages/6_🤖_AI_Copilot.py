import streamlit as st
from database.db import get_session
from models.models import SalesUser
import importlib
from services import copilot_service
importlib.reload(copilot_service)
from auth.session import require_login

st.set_page_config(page_title="AI Copilot - QUOTEFLOW OS", page_icon="🤖", layout="wide")

current_user = require_login()

st.title("🤖 AI Copilot")
st.caption("Hỏi nhanh về số liệu báo giá — trả lời dựa trên dữ liệu thật trong hệ thống (không cần API key ngoài).")

sample_questions = [
    "Tổng quan tình hình báo giá?",
    "Khách hàng nào có tỷ lệ chốt cao nhất?",
    "Báo giá nào quá hạn?",
    "Top sản phẩm bán chạy?",
    "Nhân viên nào có win rate tốt nhất?",
    "Dự báo doanh thu tháng tới?",
    "Đề xuất mức chiết khấu phù hợp?",
]

cols = st.columns(len(sample_questions))
clicked_q = None
for i, q in enumerate(sample_questions):
    if cols[i].button(q, use_container_width=True):
        clicked_q = q

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

question = st.chat_input("Nhập câu hỏi của bạn...")
final_q = clicked_q or question

if final_q:
    db = get_session()
    answer, df = copilot_service.ask(db, final_q)
    db.close()
    st.session_state["chat_history"].append({"q": final_q, "a": answer, "df": df})

for item in reversed(st.session_state["chat_history"]):
    with st.chat_message("user"):
        st.write(item["q"])
    with st.chat_message("assistant"):
        st.markdown(item["a"])
        if item["df"] is not None and not item["df"].empty:
            st.dataframe(item["df"], use_container_width=True, hide_index=True)

if not st.session_state["chat_history"]:
    st.info("💡 Bấm vào một câu hỏi gợi ý ở trên, hoặc gõ câu hỏi của bạn vào ô chat bên dưới.")
