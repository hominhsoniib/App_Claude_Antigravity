"""
AI Copilot - phiên bản rule-based chạy trên dữ liệu thật trong DB.
Không cần API key ngoài. Nhận diện intent theo từ khóa tiếng Việt,
trả về (câu trả lời text, dataframe kèm theo nếu có).
"""
import pandas as pd
from datetime import datetime
from services import kpi_service as kpi


def ask(db, question: str):
    """
    Điểm tiếp nhận câu hỏi của AI Copilot.
    Tự động chuyển sang gọi Claude API thực tế nếu có cấu hình CLAUDE_API_KEY trong .env.
    Tiếp theo gọi Gemini API thực tế nếu có cấu hình GEMINI_API_KEY trong .env.
    Nếu không, chạy chế độ rule-based mặc định.
    """
    import os
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    claude_key = os.getenv("CLAUDE_API_KEY", "").strip()
    claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022").strip()
    
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
    
    if claude_key and not claude_key.startswith("your-") and claude_key != "":
        return ask_claude_with_db(db, question, claude_key, claude_model)
    elif api_key and not api_key.startswith("your-") and api_key != "":
        return ask_gemini_with_db(db, question, api_key, model)
        
    return ask_rule_based(db, question)


def ask_rule_based(db, question: str):
    q = question.lower()

    if any(k in q for k in ["chốt cao nhất", "tỷ lệ chốt", "win rate khách"]):
        df = kpi.quotations_dataframe(db)
        if df.empty:
            return "Chưa có dữ liệu báo giá.", None
        grp = df.groupby("customer")["status"].apply(
            lambda s: (s == "Chốt đơn (Win)").sum() / max(len(s), 1) * 100
        ).sort_values(ascending=False).reset_index(name="win_rate_%")
        top = grp.head(5)
        text = f"Khách hàng có tỷ lệ chốt đơn cao nhất: **{top.iloc[0]['customer']}** ({top.iloc[0]['win_rate_%']:.0f}%)."
        return text, top

    if any(k in q for k in ["quá hạn", "hết hạn"]):
        df = kpi.quotations_dataframe(db)
        if df.empty:
            return "Chưa có dữ liệu báo giá.", None
        overdue = df[df["is_expired"] == True][["quote_no", "customer", "valid_until", "status", "grand_total"]]
        if overdue.empty:
            return "✅ Không có báo giá nào quá hạn.", None
        return f"Có **{len(overdue)}** báo giá đã quá hạn hiệu lực, cần theo dõi.", overdue

    if any(k in q for k in ["bán chạy", "top sản phẩm", "sản phẩm nào"]):
        df = kpi.top_products(db, n=5)
        if df.empty:
            return "Chưa có dữ liệu.", None
        return f"Sản phẩm bán chạy nhất theo doanh thu báo giá: **{df.iloc[0]['product']}**.", df

    if any(k in q for k in ["nhân viên", "win rate tốt nhất", "win rate nhân viên"]):
        df = kpi.top_sales_reps(db, n=10)
        if df.empty:
            return "Chưa có dữ liệu.", None
        best = df.sort_values("win_rate_%", ascending=False).iloc[0]
        return f"Nhân viên có win rate tốt nhất: **{best['sales_rep']}** ({best['win_rate_%']:.0f}%).", df

    if any(k in q for k in ["dự báo", "doanh thu tháng", "forecast"]):
        forecast = kpi.revenue_forecast_next_month(db)
        return f"Dự báo doanh thu có thể chốt trong thời gian tới (dựa trên pipeline hiện tại): **{forecast:,.0f} đ**.", None

    if any(k in q for k in ["chiết khấu phù hợp", "đề xuất chiết khấu", "mức chiết khấu"]):
        summary = kpi.kpi_summary(db)
        suggestion = (
            "Đề xuất: với khách hàng nhóm VIP/Đại lý lâu năm có thể áp dụng chiết khấu 8-10%; "
            "khách hàng mới hoặc đơn giá trị nhỏ nên giữ chiết khấu dưới 5% để bảo vệ biên lợi nhuận. "
            f"Chiết khấu trên 10% cần trình Giám đốc duyệt theo chính sách hiện hành."
        )
        return suggestion, None

    if any(k in q for k in ["tổng quan", "tình hình", "kpi", "summary"]):
        s = kpi.kpi_summary(db)
        text = (
            f"📊 Tổng số báo giá: **{s['total_quotes']}** | "
            f"Tổng giá trị: **{s['total_value']:,.0f} đ** | "
            f"Win rate: **{s['win_rate']}%** | "
            f"Báo giá quá hạn: **{s['overdue_count']}**"
        )
        return text, None

    return (
        "Tôi có thể trả lời các câu hỏi như: 'Khách hàng nào có tỷ lệ chốt cao nhất?', "
        "'Báo giá nào quá hạn?', 'Top sản phẩm bán chạy?', 'Nhân viên nào có win rate tốt nhất?', "
        "'Dự báo doanh thu tháng tới', 'Đề xuất mức chiết khấu phù hợp'.",
        None,
    )


def call_gemini_api(api_key, model, prompt):
    import urllib.request
    import json
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode("utf-8"), 
        headers=headers, 
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidates = res_data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return "Không nhận được phản hồi hợp lệ từ Gemini."
    except Exception as e:
        return f"Lỗi kết nối tới API Gemini (Hãy kiểm tra lại Key hoặc kết nối mạng): {str(e)}"


def ask_gemini_with_db(db, question, api_key, model):
    from models.models import Product, Customer, QuotationHeader
    import json
    
    # Lấy dữ liệu từ DB để tạo context cho AI
    products = db.query(Product).all()
    customers = db.query(Customer).all()
    quotes = db.query(QuotationHeader).order_by(QuotationHeader.id.desc()).limit(15).all()
    
    prod_data = [
        {"sku": p.sku, "name": p.name, "list_price": p.list_price, "cost_price": p.cost_price, "stock": p.stock_qty, "category": p.category} 
        for p in products
    ]
    cust_data = [
        {"code": c.code, "name": c.name, "group": c.group, "region": c.region, "revenue_ytd": c.revenue_ytd} 
        for c in customers
    ]
    quote_data = [
        {"quote_no": q.quote_no, "customer": q.customer.name if q.customer else "", "status": q.status.value, "total": q.grand_total, "date": q.quote_date.strftime("%d/%m/%Y")} 
        for q in quotes
    ]
    
    prompt = f"""
Bạn là trợ lý AI chuyên nghiệp Copilot cho hệ thống QUOTEFLOW OS (Hệ thống quản lý báo giá và CRM).
Dưới đây là dữ liệu hiện tại của hệ thống:

1. Danh sách sản phẩm:
{json.dumps(prod_data, ensure_ascii=False, indent=2)}

2. Danh sách khách hàng:
{json.dumps(cust_data, ensure_ascii=False, indent=2)}

3. Danh sách 15 báo giá gần đây nhất:
{json.dumps(quote_data, ensure_ascii=False, indent=2)}

Hãy trả lời câu hỏi sau của người dùng bằng tiếng Việt chuyên nghiệp, ngắn gọn và rõ ràng dưới dạng Markdown.
Nếu câu hỏi yêu cầu tính toán, hãy thực hiện tính toán chính xác dựa trên các số liệu trên. Nếu không thể tự tính toán được, hãy mô tả cách thực hiện hoặc giải thích lý do.
Nếu câu hỏi liên quan đến sản phẩm bán chạy hoặc tỷ lệ chốt đơn, hãy đưa ra số liệu tương ứng từ dữ liệu trên.

Câu hỏi của người dùng: {question}
"""
    return call_gemini_api(api_key, model, prompt), None


def call_claude_api(api_key, model, prompt):
    import urllib.request
    import json
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": model,
        "max_tokens": 4000,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode("utf-8"), 
        headers=headers, 
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            content = res_data.get("content", [])
            if content:
                return content[0].get("text", "")
            return "Không nhận được phản hồi hợp lệ từ Claude."
    except Exception as e:
        return f"Lỗi kết nối tới API Claude (Hãy kiểm tra lại Key hoặc kết nối mạng): {str(e)}"


def ask_claude_with_db(db, question, api_key, model):
    from models.models import Product, Customer, QuotationHeader
    import json
    
    # Lấy dữ liệu từ DB để tạo context cho AI
    products = db.query(Product).all()
    customers = db.query(Customer).all()
    quotes = db.query(QuotationHeader).order_by(QuotationHeader.id.desc()).limit(15).all()
    
    prod_data = [
        {"sku": p.sku, "name": p.name, "list_price": p.list_price, "cost_price": p.cost_price, "stock": p.stock_qty, "category": p.category} 
        for p in products
    ]
    cust_data = [
        {"code": c.code, "name": c.name, "group": c.group, "region": c.region, "revenue_ytd": c.revenue_ytd} 
        for c in customers
    ]
    quote_data = [
        {"quote_no": q.quote_no, "customer": q.customer.name if q.customer else "", "status": q.status.value, "total": q.grand_total, "date": q.quote_date.strftime("%d/%m/%Y")} 
        for q in quotes
    ]
    
    prompt = f"""
Bạn là trợ lý AI chuyên nghiệp Copilot cho hệ thống QUOTEFLOW OS (Hệ thống quản lý báo giá và CRM).
Dưới đây là dữ liệu hiện tại của hệ thống:

1. Danh sách sản phẩm:
{json.dumps(prod_data, ensure_ascii=False, indent=2)}

2. Danh sách khách hàng:
{json.dumps(cust_data, ensure_ascii=False, indent=2)}

3. Danh sách 15 báo giá gần đây nhất:
{json.dumps(quote_data, ensure_ascii=False, indent=2)}

Hãy trả lời câu hỏi sau của người dùng bằng tiếng Việt chuyên nghiệp, ngắn gọn và rõ ràng dưới dạng Markdown.
Nếu câu hỏi yêu cầu tính toán, hãy thực hiện tính toán chính xác dựa trên các số liệu trên. Nếu không thể tự tính toán được, hãy mô tả cách thực hiện hoặc giải thích lý do.
Nếu câu hỏi liên quan đến sản phẩm bán chạy hoặc tỷ lệ chốt đơn, hãy đưa ra số liệu tương ứng từ dữ liệu trên.

Câu hỏi của người dùng: {question}
"""
    return call_claude_api(api_key, model, prompt), None

