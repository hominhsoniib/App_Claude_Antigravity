import os
import base64
import shutil
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import Config, Tables, OPTIONS, Roles
import db
import auth
import ai_service
import automation

app = FastAPI(title=Config.APP_NAME, version=Config.VERSION)

# Đăng ký thư mục lưu trữ file tải lên tĩnh
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=Config.UPLOAD_DIR), name="uploads")

# Khởi tạo Jinja2 templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# --- BACKGROUND TASKS (PERIODIC) ---
async def background_loop():
    while True:
        try:
            # 1) Dọn dẹp session hết hạn
            auth.clean_expired_sessions()
            # 2) Gửi nhắc lịch follow-up
            automation.check_follow_ups_due()
        except Exception as e:
            print(f"[BACKGROUND TASK] Error: {e}")
        # Chạy lại mỗi 1 giờ
        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup_event():
    # 1) Khởi tạo cơ sở dữ liệu SQLite & bảng
    db.init_db()
    
    # 2) Tạo Admin mặc định nếu rỗng
    users = db.read_all(Tables.USERS)
    if not users:
        salt = auth.gen_salt()
        db.insert(Tables.USERS, {
            "id": auth.gen_id("USR"),
            "email": Config.DEFAULT_ADMIN_EMAIL.lower(),
            "passwordHash": auth.hash_password(Config.DEFAULT_ADMIN_PASS, salt),
            "salt": salt,
            "name": Config.DEFAULT_ADMIN_NAME,
            "role": Roles.ADMIN,
            "status": "active",
            "createdAt": datetime.now().isoformat(),
            "lastLogin": ""
        })
        print(f"[SETUP] Admin account created: {Config.DEFAULT_ADMIN_EMAIL} / {Config.DEFAULT_ADMIN_PASS}")

    # 3) Tạo config KPI mặc định nếu rỗng
    cfg = db.read_all(Tables.CONFIG)
    if not cfg:
        db.insert(Tables.CONFIG, {"key": "kpi_revenue_target", "value": "100000000"})
        db.insert(Tables.CONFIG, {"key": "kpi_deal_target", "value": "20"})
        db.insert(Tables.CONFIG, {"key": "ai_provider", "value": "claude"})

    # 4) Tạo email template mẫu nếu rỗng
    tpls = db.read_all(Tables.TEMPLATES)
    if not tpls:
        db.insert(Tables.TEMPLATES, {
            "id": auth.gen_id("TPL"),
            "name": "Chào mừng khách mới",
            "trigger": "status:Lead",
            "subject": "Cảm ơn {{name}} đã quan tâm!",
            "body": "Xin chào {{name}},\n\nCảm ơn bạn đã để lại thông tin. Đội ngũ của chúng tôi sẽ liên hệ sớm.\n\nTrân trọng.",
            "active": "no",
            "createdAt": datetime.now().isoformat()
        })
        db.insert(Tables.TEMPLATES, {
            "id": auth.gen_id("TPL"),
            "name": "Cảm ơn đã chốt deal",
            "trigger": "status:Đã chốt",
            "subject": "Cảm ơn {{name}} đã tin tưởng!",
            "body": "Xin chào {{name}},\n\nCảm ơn bạn đã đồng hành. Chúng tôi rất vui được phục vụ bạn.\n\nTrân trọng.",
            "active": "no",
            "createdAt": datetime.now().isoformat()
        })

    # 5) Chạy background loop
    asyncio.create_task(background_loop())

# --- ROUTE CHÍNH SERVE SPA ---
@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "appName": Config.APP_NAME,
        "version": Config.VERSION
    })

# --- IMPLEMENTATION OF API HANDLERS ---

def api_bootstrap(token: str = None):
    user = auth.verify_session(token)
    return {
        "ok": True,
        "data": {
            "app": {"name": Config.APP_NAME, "version": Config.VERSION},
            "options": OPTIONS,
            "roles": {
                "ADMIN": Roles.ADMIN,
                "MANAGER": Roles.MANAGER,
                "SALE": Roles.SALE
            },
            "user": user
        }
    }

def api_current_google_email():
    # Vì ứng dụng chạy cục bộ, trả về rỗng để ép user dùng email/password đăng nhập
    return {"ok": True, "data": ""}

def api_login(email: str, password: str):
    email = email.strip().lower()
    users = db.read_all(Tables.USERS)
    u = next((u for u in users if u["email"].lower() == email), None)
    if not u:
        return {"ok": False, "error": "Email hoặc mật khẩu không đúng."}
    if u["status"] != "active":
        return {"ok": False, "error": "Tài khoản đã bị khoá."}
        
    hash_val = auth.hash_password(password, u["salt"])
    if hash_val != u["passwordHash"]:
        return {"ok": False, "error": "Email hoặc mật khẩu không đúng."}
        
    db.update_by_id(Tables.USERS, u["id"], {"lastLogin": datetime.now().isoformat()})
    token = auth.create_session(u)
    db.insert(Tables.AUDIT, {
        "id": auth.gen_id("LOG"),
        "timestamp": datetime.now().isoformat(),
        "user": u["email"],
        "action": "login",
        "target": "auth",
        "targetId": u["id"],
        "detail": "password"
    })
    return {"ok": True, "data": {"token": token, "name": u["name"], "role": u["role"], "email": u["email"]}}

def api_google_login():
    return {"ok": False, "error": "Đăng nhập bằng tài khoản Google chỉ hỗ trợ trên môi trường Google Apps Script. Vui lòng đăng nhập bằng Email/Password."}

def api_logout(token: str):
    s = auth.verify_session(token)
    if s:
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": s["email"],
            "action": "logout",
            "target": "auth",
            "targetId": "",
            "detail": ""
        })
    auth.destroy_session(token)
    return {"ok": True, "data": True}

def api_sales_list(token: str):
    auth.guard(token)
    users = db.read_all(Tables.USERS)
    sales = [{"email": u["email"], "name": u["name"], "role": u["role"]} for u in users if u["status"] == "active"]
    return {"ok": True, "data": sales}

def api_list_customers(token: str, q: dict = None):
    try:
        me = auth.guard(token, "customer.view")
        q = q or {}
        rows = db.read_all(Tables.CUSTOMERS)
        
        # Sales chỉ được xem khách do mình phụ trách
        if me["role"] == Roles.SALE:
            rows = [r for r in rows if r["assignedTo"] == me["email"]]
            
        if q.get("source"):
            rows = [r for r in rows if r["source"] == q["source"]]
        if q.get("status"):
            rows = [r for r in rows if r["status"] == q["status"]]
        if q.get("assignedTo"):
            rows = [r for r in rows if r["assignedTo"] == q["assignedTo"]]
        if q.get("search"):
            s = str(q["search"]).lower()
            rows = [r for r in rows if s in f"{r['name']} {r['phone']} {r['email']} {r['tags']}".lower()]
            
        # Sắp xếp theo ngày cập nhật giảm dần
        rows.sort(key=lambda x: x["updatedAt"], reverse=True)
        
        total = len(rows)
        page = max(1, q.get("page", 1))
        size = min(200, q.get("pageSize", 20))
        paged = rows[(page - 1) * size : page * size]
        
        return {"ok": True, "data": {"rows": paged, "total": total, "page": page, "pageSize": size}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_get_customer(token: str, id: str):
    try:
        me = auth.guard(token, "customer.view")
        c = db.find_by_id(Tables.CUSTOMERS, id)
        if not c:
            return {"ok": False, "error": "Không tìm thấy khách hàng."}
        if me["role"] == Roles.SALE and c["assignedTo"] != me["email"]:
            return {"ok": False, "error": "Bạn không có quyền xem khách hàng này."}
            
        deals = [d for d in db.read_all(Tables.DEALS) if d["customerId"] == id]
        care = [r for r in db.read_all(Tables.CARE) if r["customerId"] == id]
        care.sort(key=lambda x: x["date"], reverse=True)
        notes = [n for n in db.read_all(Tables.NOTES) if n["customerId"] == id]
        notes.sort(key=lambda x: x["createdAt"])
        
        return {"ok": True, "data": {"customer": c, "deals": deals, "care": care, "notes": notes}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_create_customer(token: str, payload: dict):
    try:
        me = auth.guard(token, "customer.create")
        name = payload.get("name", "").strip()
        phone = payload.get("phone", "").strip()
        if not name or not phone:
            return {"ok": False, "error": "Thiếu tên hoặc số điện thoại."}
            
        now = datetime.now().isoformat()
        c = {
            "id": auth.gen_id("CUS"),
            "name": name,
            "phone": phone,
            "email": payload.get("email", "").strip(),
            "source": payload.get("source") if payload.get("source") in OPTIONS["SOURCES"] else "Website",
            "status": payload.get("status") if payload.get("status") in OPTIONS["STATUSES"] else "Lead",
            "tags": payload.get("tags", "").strip(),
            "assignedTo": payload.get("assignedTo") or me["email"],
            "createdAt": now,
            "updatedAt": now,
            "score": "",
            "attachments": "",
            "channel": "manual",
            "channelId": ""
        }
        db.insert(Tables.CUSTOMERS, c)
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": now,
            "user": me["email"],
            "action": "create",
            "target": "customer",
            "targetId": c["id"],
            "detail": c["name"]
        })
        return {"ok": True, "data": {"id": c["id"]}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_update_customer(token: str, id: str, patch: dict):
    try:
        me = auth.guard(token, "customer.update")
        c = db.find_by_id(Tables.CUSTOMERS, id)
        if not c:
            return {"ok": False, "error": "Không tìm thấy khách hàng."}
        if me["role"] == Roles.SALE and c["assignedTo"] != me["email"]:
            return {"ok": False, "error": "Bạn không có quyền sửa khách hàng này."}
            
        clean = {}
        for k in ["name", "phone", "email", "source", "status", "tags", "assignedTo"]:
            if k in patch:
                clean[k] = patch[k]
                
        clean["updatedAt"] = datetime.now().isoformat()
        db.update_by_id(Tables.CUSTOMERS, id, clean)
        
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "update",
            "target": "customer",
            "targetId": id,
            "detail": ", ".join(clean.keys())
        })
        
        # Nếu đổi trạng thái, kích hoạt email workflow
        if "status" in clean and clean["status"] != c["status"]:
            automation.trigger_email_workflow(id, f"status:{clean['status']}")
            
        return {"ok": True, "data": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_delete_customer(token: str, id: str):
    try:
        me = auth.guard(token, "customer.delete")
        if me["role"] == Roles.SALE:
            return {"ok": False, "error": "Sale không được xoá khách hàng."}
            
        db.delete_by_id(Tables.CUSTOMERS, id)
        # Xóa các liên kết
        for t in [Tables.DEALS, Tables.CARE, Tables.NOTES]:
            rows = db.read_all(t)
            for r in rows:
                if r["customerId"] == id:
                    db.delete_by_id(t, r["id"])
                    
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "delete",
            "target": "customer",
            "targetId": id,
            "detail": ""
        })
        return {"ok": True, "data": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_add_care(token: str, payload: dict):
    try:
        me = auth.guard(token, "care.create")
        now = datetime.now().isoformat()
        r = {
            "id": auth.gen_id("CARE"),
            "customerId": payload["customerId"],
            "date": payload.get("date") or now,
            "handler": f"{me['name']} ({me['email']})",
            "content": payload["content"],
            "note": payload.get("note", ""),
            "result": payload.get("result", ""),
            "createdAt": now
        }
        db.insert(Tables.CARE, r)
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": now,
            "user": me["email"],
            "action": "create",
            "target": "care",
            "targetId": payload["customerId"],
            "detail": ""
        })
        return {"ok": True, "data": {"id": r["id"]}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_import_customers(token: str, rows: list):
    try:
        me = auth.guard(token, "customer.create")
        if not rows:
            return {"ok": False, "error": "Không có dữ liệu để import."}
            
        added = 0
        skipped = 0
        now = datetime.now().isoformat()
        for p in rows:
            if not p.get("name") or not p.get("phone"):
                skipped += 1
                continue
                
            c = {
                "id": auth.gen_id("CUS"),
                "name": p["name"],
                "phone": p["phone"],
                "email": p.get("email", ""),
                "source": p["source"] if p.get("source") in OPTIONS["SOURCES"] else "Website",
                "status": p["status"] if p.get("status") in OPTIONS["STATUSES"] else "Lead",
                "tags": p.get("tags", ""),
                "assignedTo": p.get("assignedTo") or me["email"],
                "createdAt": now,
                "updatedAt": now,
                "score": "",
                "attachments": "",
                "channel": "import",
                "channelId": ""
            }
            db.insert(Tables.CUSTOMERS, c)
            added += 1
            
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": now,
            "user": me["email"],
            "action": "import",
            "target": "customer",
            "targetId": "",
            "detail": f"Thêm thành công: {added}, bỏ qua: {skipped}"
        })
        return {"ok": True, "data": {"added": added, "skipped": skipped}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_export_customers(token: str):
    try:
        me = auth.guard(token, "customer.view")
        rows = db.read_all(Tables.CUSTOMERS)
        if me["role"] == Roles.SALE:
            rows = [r for r in rows if r["assignedTo"] == me["email"]]
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "export",
            "target": "customer",
            "targetId": "",
            "detail": f"Xuất: {len(rows)}"
        })
        return {"ok": True, "data": rows}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_list_deals(token: str):
    try:
        me = auth.guard(token, "deal.view")
        deals = db.read_all(Tables.DEALS)
        if me["role"] == Roles.SALE:
            deals = [d for d in deals if d["assignedTo"] == me["email"]]
            
        # Gán tên khách hàng
        c_list = db.read_all(Tables.CUSTOMERS)
        c_map = {c["id"]: c["name"] for c in c_list}
        for d in deals:
            d["customerName"] = c_map.get(d["customerId"], "(đã xoá)")
            
        board = {s: [] for s in OPTIONS["STAGES"]}
        for d in deals:
            stage = d["stage"]
            if stage in board:
                board[stage].append(d)
            else:
                board["Lead"].append(d)
                
        return {"ok": True, "data": board}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_create_deal(token: str, payload: dict):
    try:
        me = auth.guard(token, "deal.create")
        c = db.find_by_id(Tables.CUSTOMERS, payload["customerId"])
        if not c:
            return {"ok": False, "error": "Khách hàng không tồn tại."}
            
        now = datetime.now().isoformat()
        stage = payload["stage"] if payload.get("stage") in OPTIONS["STAGES"] else "Lead"
        d = {
            "id": auth.gen_id("DEAL"),
            "customerId": payload["customerId"],
            "title": payload["title"],
            "value": float(payload.get("value", 0)),
            "stage": stage,
            "source": payload.get("source") or c["source"],
            "assignedTo": payload.get("assignedTo") or me["email"],
            "expectedClose": payload.get("expectedClose", ""),
            "wonAt": now if stage == OPTIONS["WON_STAGE"] else "",
            "createdAt": now,
            "updatedAt": now
        }
        db.insert(Tables.DEALS, d)
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": now,
            "user": me["email"],
            "action": "create",
            "target": "deal",
            "targetId": d["id"],
            "detail": d["title"]
        })
        return {"ok": True, "data": {"id": d["id"]}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_move_deal(token: str, id: str, stage: str):
    try:
        me = auth.guard(token, "deal.update")
        if stage not in OPTIONS["STAGES"]:
            return {"ok": False, "error": "Trạng thái deal không hợp lệ."}
            
        patch = {"stage": stage, "updatedAt": datetime.now().isoformat()}
        if stage == OPTIONS["WON_STAGE"]:
            patch["wonAt"] = datetime.now().isoformat()
            
        db.update_by_id(Tables.DEALS, id, patch)
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "move",
            "target": "deal",
            "targetId": id,
            "detail": stage
        })
        return {"ok": True, "data": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_update_deal(token: str, id: str, patch: dict):
    try:
        me = auth.guard(token, "deal.update")
        clean = {}
        for k in ["title", "value", "stage", "source", "assignedTo", "expectedClose"]:
            if k in patch:
                if k == "value":
                    clean[k] = float(patch[k]) if patch[k] else 0.0
                else:
                    clean[k] = patch[k]
                    
        if clean.get("stage") == OPTIONS["WON_STAGE"]:
            clean["wonAt"] = datetime.now().isoformat()
            
        clean["updatedAt"] = datetime.now().isoformat()
        db.update_by_id(Tables.DEALS, id, clean)
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "update",
            "target": "deal",
            "targetId": id,
            "detail": ", ".join(clean.keys())
        })
        return {"ok": True, "data": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_delete_deal(token: str, id: str):
    try:
        me = auth.guard(token, "deal.delete")
        db.delete_by_id(Tables.DEALS, id)
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "delete",
            "target": "deal",
            "targetId": id,
            "detail": ""
        })
        return {"ok": True, "data": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_dashboard(token: str):
    try:
        me = auth.guard(token, "dashboard.view")
        scope = me["email"] if me["role"] == Roles.SALE else None
        
        customers = db.read_all(Tables.CUSTOMERS)
        deals = db.read_all(Tables.DEALS)
        
        if scope:
            customers = [c for c in customers if c["assignedTo"] == scope]
            deals = [d for d in deals if d["assignedTo"] == scope]
            
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_customers = len(customers)
        new_today = len([c for c in customers if datetime.fromisoformat(c["createdAt"]) >= today])
        caring = len([c for c in customers if c["status"] in ["Đang tư vấn", "Đàm phán", "Tiềm năng"]])
        
        won_deals = [d for d in deals if d["stage"] == OPTIONS["WON_STAGE"]]
        revenue = sum([float(d["value"] or 0) for d in won_deals])
        closed_deals = len([d for d in deals if d["stage"] in [OPTIONS["WON_STAGE"], OPTIONS["LOST_STAGE"]]])
        conv_rate = round(len(won_deals) / closed_deals * 100) if closed_deals else 0
        
        # 6 months line chart
        months = []
        for i in range(5, -1, -1):
            # Tính toán tháng
            m_date = datetime.now()
            # Trừ tháng một cách đơn giản
            for _ in range(i):
                m_date = (m_date.replace(day=1) - asyncio.subprocess.sys.dateutil.relativedelta.relativedelta(months=1) if 'dateutil' in globals() else m_date) # Fallback: simple logic
            # Thủ công trừ tháng tránh phụ thuộc dateutil
            year = datetime.now().year
            month = datetime.now().month - i
            while month <= 0:
                month += 12
                year -= 1
            months.append({"key": f"{year}-{month:02d}", "label": f"T{month}"})
            
        rev_by_month = {m["key"]: 0.0 for m in months}
        for d in won_deals:
            dt_str = d["wonAt"] or d["updatedAt"]
            dt = datetime.fromisoformat(dt_str)
            k = f"{dt.year}-{dt.month:02d}"
            if k in rev_by_month:
                rev_by_month[k] += float(d["value"] or 0)
                
        line_chart = {
            "labels": [m["label"] for m in months],
            "data": [rev_by_month[m["key"]] for m in months]
        }
        
        # Pie chart: sources
        by_source = {s: 0 for s in OPTIONS["SOURCES"]}
        for c in customers:
            if c["source"] in by_source:
                by_source[c["source"]] += 1
        pie_chart = {
            "labels": list(by_source.keys()),
            "data": list(by_source.values())
        }
        
        # Bar chart: stages
        by_stage = {s: 0 for s in OPTIONS["STAGES"]}
        for d in deals:
            if d["stage"] in by_stage:
                by_stage[d["stage"]] += 1
        bar_chart = {
            "labels": list(by_stage.keys()),
            "data": list(by_stage.values())
        }
        
        # KPI Sale
        kpi_sale = []
        if me["role"] != Roles.SALE:
            deals_all = db.read_all(Tables.DEALS)
            s_map = {}
            for d in deals_all:
                k = d["assignedTo"] or "(chưa gán)"
                if k not in s_map:
                    s_map[k] = {"sale": k, "deals": 0, "won": 0, "revenue": 0.0}
                s_map[k]["deals"] += 1
                if d["stage"] == OPTIONS["WON_STAGE"]:
                    s_map[k]["won"] += 1
                    s_map[k]["revenue"] += float(d["value"] or 0)
            kpi_sale = list(s_map.values())
            kpi_sale.sort(key=lambda x: x["revenue"], reverse=True)
            
        return {
            "ok": True,
            "data": {
                "cards": {
                    "totalCustomers": total_customers,
                    "newToday": new_today,
                    "caring": caring,
                    "revenue": revenue,
                    "convRate": conv_rate,
                    "wonDeals": len(won_deals)
                },
                "lineChart": line_chart,
                "pieChart": pie_chart,
                "barChart": bar_chart,
                "kpiSale": kpi_sale
            }
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_report(token: str, q: dict = None):
    try:
        me = auth.guard(token, "report.view")
        if me["role"] == Roles.SALE:
            return {"ok": False, "error": "Sale không có quyền xem báo cáo tổng."}
            
        q = q or {}
        dt_from = datetime.fromisoformat(q["from"]) if q.get("from") else None
        dt_to = datetime.fromisoformat(q["to"]) if q.get("to") else None
        
        deals = db.read_all(Tables.DEALS)
        customers = db.read_all(Tables.CUSTOMERS)
        
        def in_range(date_str):
            if not date_str:
                return False
            dt = datetime.fromisoformat(date_str)
            if dt_from and dt < dt_from:
                return False
            if dt_to and dt > dt_to:
                return False
            return True
            
        won = [d for d in deals if d["stage"] == OPTIONS["WON_STAGE"] and (not (dt_from or dt_to) or in_range(d["wonAt"] or d["updatedAt"]))]
        
        # 1) Revenue by month
        rev_month = {}
        for d in won:
            dt = datetime.fromisoformat(d["wonAt"] or d["updatedAt"])
            k = f"{dt.year}-{dt.month:02d}"
            rev_month[k] = rev_month.get(k, 0.0) + float(d["value"] or 0)
        rev_by_month = [{"month": k, "revenue": v} for k, v in sorted(rev_month.items())]
        
        # 2) By source
        src_stat = {s: {"source": s, "customers": 0, "deals": 0, "won": 0, "revenue": 0.0} for s in OPTIONS["SOURCES"]}
        for c in customers:
            if c["source"] in src_stat:
                src_stat[c["source"]]["customers"] += 1
        for d in deals:
            s = d["source"]
            if s in src_stat:
                src_stat[s]["deals"] += 1
                if d["stage"] == OPTIONS["WON_STAGE"]:
                    src_stat[s]["won"] += 1
                    src_stat[s]["revenue"] += float(d["value"] or 0)
        by_source = list(src_stat.values())
        
        # 3) By sales staff
        sale_stat = {}
        for d in deals:
            k = d["assignedTo"] or "(chưa gán)"
            if k not in sale_stat:
                sale_stat[k] = {"sale": k, "deals": 0, "won": 0, "lost": 0, "revenue": 0.0}
            sale_stat[k]["deals"] += 1
            if d["stage"] == OPTIONS["WON_STAGE"]:
                sale_stat[k]["won"] += 1
                sale_stat[k]["revenue"] += float(d["value"] or 0)
            elif d["stage"] == OPTIONS["LOST_STAGE"]:
                sale_stat[k]["lost"] += 1
                
        by_sale = []
        for k, r in sale_stat.items():
            closed = r["won"] + r["lost"]
            r["convRate"] = round(r["won"] / closed * 100) if closed else 0
            by_sale.append(r)
        by_sale.sort(key=lambda x: x["revenue"], reverse=True)
        
        total_revenue = sum([float(d["value"] or 0) for d in won])
        total_closed = len([d for d in deals if d["stage"] in [OPTIONS["WON_STAGE"], OPTIONS["LOST_STAGE"]]])
        conv_rate = round(len(won) / total_closed * 100) if total_closed else 0
        
        return {
            "ok": True,
            "data": {
                "summary": {
                    "totalRevenue": total_revenue,
                    "wonDeals": len(won),
                    "convRate": conv_rate,
                    "totalCustomers": len(customers)
                },
                "revByMonth": rev_by_month,
                "bySource": by_source,
                "bySale": by_sale
            }
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_audit_log(token: str, limit: int = 200):
    try:
        auth.guard(token, "admin.audit")
        rows = db.read_all(Tables.AUDIT)
        rows.sort(key=lambda x: x["timestamp"], reverse=True)
        return {"ok": True, "data": rows[:min(500, limit)]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_list_backups(token: str):
    try:
        auth.guard(token, "admin.backup")
        backup_dir = os.path.join(os.path.dirname(__file__), "backups")
        if not os.path.exists(backup_dir):
            return {"ok": True, "data": []}
            
        files = []
        for f in os.listdir(backup_dir):
            if f.endswith(".db"):
                path = os.path.join(backup_dir, f)
                created = datetime.fromtimestamp(os.path.getctime(path)).isoformat()
                # URL tải file backup
                url = f"/uploads/../backups/{f}" # Mẹo dẫn ra ngoài hoặc tải qua static
                files.append({"id": f, "name": f, "url": f"/api/downloadBackup?name={f}&token={token}", "created": created})
                
        files.sort(key=lambda x: x["created"], reverse=True)
        return {"ok": True, "data": files}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_backup(token: str):
    try:
        me = auth.guard(token, "admin.backup")
        backup_dir = os.path.join(os.path.dirname(__file__), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        stamp = datetime.now().strftime("%Y%m%d_%H%m%S")
        name = f"NEXUS_CRM_Backup_{stamp}.db"
        dest = os.path.join(backup_dir, name)
        
        # Sao chép file SQLite
        shutil.copy(Config.DATABASE_PATH, dest)
        
        # Dọn dẹp giữ tối đa 10 bản
        backups = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith(".db")]
        backups.sort(key=os.path.getctime, reverse=True)
        for old in backups[Config.BACKUP_KEEP:]:
            try:
                os.remove(old)
            except Exception:
                pass
                
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "backup",
            "target": "system",
            "targetId": name,
            "detail": f"Khởi tạo sao lưu thành công: {name}"
        })
        return {"ok": True, "data": {"name": name, "url": f"/api/downloadBackup?name={name}&token={token}", "kept": len(backups[:Config.BACKUP_KEEP])}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_list_templates(token: str):
    try:
        auth.guard(token, "template.view")
        tpls = db.read_all(Tables.TEMPLATES)
        tpls.sort(key=lambda x: x["createdAt"], reverse=True)
        return {"ok": True, "data": tpls}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_create_template(token: str, payload: dict):
    try:
        me = auth.guard(token, "admin.users")
        t = {
            "id": auth.gen_id("TPL"),
            "name": payload["name"].strip(),
            "trigger": payload["trigger"],
            "subject": payload["subject"].strip(),
            "body": payload["body"],
            "active": "yes" if payload.get("active") else "no",
            "createdAt": datetime.now().isoformat()
        }
        db.insert(Tables.TEMPLATES, t)
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "create",
            "target": "template",
            "targetId": t["id"],
            "detail": t["name"]
        })
        return {"ok": True, "data": {"id": t["id"]}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_update_template(token: str, id: str, patch: dict):
    try:
        me = auth.guard(token, "admin.users")
        clean = {}
        for k in ["name", "trigger", "subject", "body"]:
            if k in patch:
                clean[k] = patch[k]
        if "active" in patch:
            clean["active"] = "yes" if patch["active"] else "no"
            
        db.update_by_id(Tables.TEMPLATES, id, clean)
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "update",
            "target": "template",
            "targetId": id,
            "detail": ", ".join(clean.keys())
        })
        return {"ok": True, "data": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_delete_template(token: str, id: str):
    try:
        me = auth.guard(token, "admin.users")
        db.delete_by_id(Tables.TEMPLATES, id)
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "delete",
            "target": "template",
            "targetId": id,
            "detail": ""
        })
        return {"ok": True, "data": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_list_users(token: str):
    try:
        auth.guard(token, "admin.users")
        users = db.read_all(Tables.USERS)
        # Loại bỏ mật khẩu băm và muối
        clean = []
        for u in users:
            clean.append({
                "id": u["id"],
                "email": u["email"],
                "name": u["name"],
                "role": u["role"],
                "status": u["status"],
                "createdAt": u["createdAt"],
                "lastLogin": u["lastLogin"]
            })
        return {"ok": True, "data": clean}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_create_user(token: str, payload: dict):
    try:
        me = auth.guard(token, "admin.users")
        email = payload["email"].strip().lower()
        
        users = db.read_all(Tables.USERS)
        if any(u["email"].lower() == email for u in users):
            return {"ok": False, "error": "Email đã tồn tại."}
            
        salt = auth.gen_salt()
        u = {
            "id": auth.gen_id("USR"),
            "email": email,
            "passwordHash": auth.hash_password(payload["password"], salt),
            "salt": salt,
            "name": payload["name"].strip(),
            "role": payload["role"],
            "status": "active",
            "createdAt": datetime.now().isoformat(),
            "lastLogin": ""
        }
        db.insert(Tables.USERS, u)
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "create",
            "target": "user",
            "targetId": u["id"],
            "detail": u["email"]
        })
        return {"ok": True, "data": {"id": u["id"]}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_update_user(token: str, id: str, patch: dict):
    try:
        me = auth.guard(token, "admin.users")
        clean = {}
        for k in ["name", "role", "status"]:
            if k in patch:
                clean[k] = patch[k]
        if patch.get("password"):
            salt = auth.gen_salt()
            clean["salt"] = salt
            clean["passwordHash"] = auth.hash_password(patch["password"], salt)
            
        db.update_by_id(Tables.USERS, id, clean)
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "update",
            "target": "user",
            "targetId": id,
            "detail": ", ".join(clean.keys())
        })
        return {"ok": True, "data": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_delete_user(token: str, id: str):
    try:
        me = auth.guard(token, "admin.users")
        db.delete_by_id(Tables.USERS, id)
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "delete",
            "target": "user",
            "targetId": id,
            "detail": ""
        })
        return {"ok": True, "data": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_list_follow_ups(token: str, customer_id: str = None):
    try:
        me = auth.guard(token, "followup.view")
        rows = db.read_all(Tables.FOLLOWUPS)
        if customer_id:
            rows = [r for r in rows if r["customerId"] == customer_id]
        elif me["role"] == Roles.SALE:
            rows = [r for r in rows if r["assignedTo"] == me["email"]]
            
        # Sắp xếp theo ngày hẹn tăng dần
        rows.sort(key=lambda x: x["dueDate"])
        return {"ok": True, "data": rows}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_create_follow_up(token: str, payload: dict):
    try:
        me = auth.guard(token, "followup.create")
        c = db.find_by_id(Tables.CUSTOMERS, payload["customerId"])
        if not c:
            return {"ok": False, "error": "Không tìm thấy khách hàng."}
            
        fu = {
            "id": auth.gen_id("FU"),
            "customerId": payload["customerId"],
            "dueDate": payload["dueDate"],
            "dueTime": payload.get("dueTime") or "09:00",
            "content": payload["content"],
            "status": "pending",
            "assignedTo": payload.get("assignedTo") or me["email"],
            "createdAt": datetime.now().isoformat(),
            "calendarEventId": "",  # Google Calendar event id (sẽ được tạo giả lập)
            "remindedAt": ""
        }
        db.insert(Tables.FOLLOWUPS, fu)
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "create",
            "target": "followup",
            "targetId": payload["customerId"],
            "detail": payload["dueDate"]
        })
        return {"ok": True, "data": {"id": fu["id"], "calendar": False}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_done_follow_up(token: str, id: str):
    try:
        me = auth.guard(token, "followup.update")
        db.update_by_id(Tables.FOLLOWUPS, id, {"status": "done"})
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "done",
            "target": "followup",
            "targetId": id,
            "detail": ""
        })
        return {"ok": True, "data": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_delete_follow_up(token: str, id: str):
    try:
        me = auth.guard(token, "followup.delete")
        db.delete_by_id(Tables.FOLLOWUPS, id)
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "delete",
            "target": "followup",
            "targetId": id,
            "detail": ""
        })
        return {"ok": True, "data": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_list_files(token: str, customer_id: str):
    try:
        auth.guard(token, "file.view")
        c = db.find_by_id(Tables.CUSTOMERS, customer_id)
        if not c:
            return {"ok": False, "error": "Không tìm thấy khách hàng."}
            
        attachments = c.get("attachments")
        files = []
        if attachments:
            try:
                files = json.loads(attachments)
            except Exception:
                try:
                    import json
                    files = json.loads(attachments)
                except Exception:
                    pass
        return {"ok": True, "data": files}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_upload_file(token: str, payload: dict):
    try:
        me = auth.guard(token, "file.upload")
        customer_id = payload["customerId"]
        file_name = payload["fileName"]
        base64_data = payload["base64"]
        
        c = db.find_by_id(Tables.CUSTOMERS, customer_id)
        if not c:
            return {"ok": False, "error": "Không tìm thấy khách hàng."}
            
        # Lưu file cục bộ
        file_bytes = base64.b64decode(base64_data)
        safe_name = f"{customer_id}_{int(datetime.now().timestamp())}_{file_name}"
        file_path = os.path.join(Config.UPLOAD_DIR, safe_name)
        
        with open(file_path, "wb") as f:
            f.write(file_bytes)
            
        file_url = f"/uploads/{safe_name}"
        
        # Cập nhật danh sách tệp đính kèm trong cơ sở dữ liệu
        import json
        attachments = []
        if c.get("attachments"):
            try:
                attachments = json.loads(c["attachments"])
            except Exception:
                pass
                
        attachments.append({
            "name": file_name,
            "url": file_url,
            "id": safe_name,
            "at": datetime.now().isoformat()
        })
        
        db.update_by_id(Tables.CUSTOMERS, customer_id, {
            "attachments": json.dumps(attachments),
            "updatedAt": datetime.now().isoformat()
        })
        
        db.insert(Tables.AUDIT, {
            "id": auth.gen_id("LOG"),
            "timestamp": datetime.now().isoformat(),
            "user": me["email"],
            "action": "upload",
            "target": "file",
            "targetId": customer_id,
            "detail": file_name
        })
        return {"ok": True, "data": {"name": file_name, "url": file_url}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

COMPANIES_FILE = os.path.join(os.path.dirname(__file__), "companies.json")

def read_companies_data() -> list[dict]:
    if not os.path.exists(COMPANIES_FILE):
        default_data = [
            {
                "code": "default",
                "name": "CÔNG TY TNHH GIẢI PHÁP CÔNG NGHIỆP VIỆT",
                "address": "123 Đường Công Nghiệp, Q. Bình Tân, TP.HCM",
                "tax_code": "0312345678",
                "phone_email": "(028) 3838 3838   |   Email: sales@congty.vn"
            }
        ]
        try:
            import json
            with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return default_data
    try:
        import json
        with open(COMPANIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def api_list_companies(token: str = None):
    data = read_companies_data()
    return {"ok": True, "data": data}

def api_create_company(token: str, payload: dict):
    try:
        # Check permissions
        auth.guard(token, "admin.company")
        
        code = payload.get("code", "").strip().lower()
        name = payload.get("name", "").strip()
        address = payload.get("address", "").strip()
        tax_code = payload.get("tax_code", "").strip()
        phone_email = payload.get("phone_email", "").strip()
        
        if not code or not name:
            return {"ok": False, "error": "Mã và Tên công ty không được để trống."}
            
        import re
        if not re.match(r"^[a-z0-9_-]+$", code):
            return {"ok": False, "error": "Mã công ty chỉ gồm chữ thường không dấu, số, gạch dưới (_) hoặc gạch ngang (-)."}
            
        data = read_companies_data()
        if any(c["code"] == code for c in data):
            return {"ok": False, "error": "Mã công ty này đã tồn tại."}
            
        new_company = {
            "code": code,
            "name": name,
            "address": address,
            "tax_code": tax_code,
            "phone_email": phone_email
        }
        data.append(new_company)
        
        import json
        with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        # Trigger DB initialization
        db.active_company.set(code)
        conn = db.get_db()
        conn.close()
        
        return {"ok": True, "data": new_company}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# Bản đồ ánh xạ tất cả các phương thức API gọi từ Client
API_MAP = {
    "apiListCompanies": api_list_companies,
    "apiCreateCompany": api_create_company,
    "apiBootstrap": api_bootstrap,
    "apiCurrentGoogleEmail": api_current_google_email,
    "apiLogin": api_login,
    "apiGoogleLogin": api_google_login,
    "apiLogout": api_logout,
    "apiSalesList": api_sales_list,
    "apiListCustomers": api_list_customers,
    "apiGetCustomer": api_get_customer,
    "apiCreateCustomer": api_create_customer,
    "apiUpdateCustomer": api_update_customer,
    "apiDeleteCustomer": api_delete_customer,
    "apiAddCare": api_add_care,
    "apiImportCustomers": api_import_customers,
    "apiExportCustomers": api_export_customers,
    "apiListDeals": api_list_deals,
    "apiCreateDeal": api_create_deal,
    "apiMoveDeal": api_move_deal,
    "apiUpdateDeal": api_update_deal,
    "apiDeleteDeal": api_delete_deal,
    "apiDashboard": api_dashboard,
    "apiReport": api_report,
    "apiAuditLog": api_audit_log,
    "apiListBackups": api_list_backups,
    "apiBackup": api_backup,
    "apiListTemplates": api_list_templates,
    "apiCreateTemplate": api_create_template,
    "apiUpdateTemplate": api_update_template,
    "apiDeleteTemplate": api_delete_template,
    "apiListUsers": api_list_users,
    "apiCreateUser": api_create_user,
    "apiUpdateUser": api_update_user,
    "apiDeleteUser": api_delete_user,
    "apiListFollowUps": api_list_follow_ups,
    "apiCreateFollowUp": api_create_follow_up,
    "apiDoneFollowUp": api_done_follow_up,
    "apiDeleteFollowUp": api_delete_follow_up,
    "apiListFiles": api_list_files,
    "apiUploadFile": api_upload_file,
    
    # AI service endpoints
    "apiAISuggest": ai_service.api_ai_suggest,
    "apiAIScore": ai_service.api_ai_score,
    "apiAIAutoTag": ai_service.api_ai_autotag,
    "apiAISummary": ai_service.api_ai_summary,
    "apiAIStatus": ai_service.api_ai_status,
    
    # Gmail integration endpoints
    "apiScanGmail": automation.api_scan_gmail_manual
}

# --- DYNAMIC RPC ROUTER ---
@app.post("/api/{method}")
async def api_router(method: str, request: Request):
    try:
        args = await request.json()
    except Exception:
        args = []
        
    # Read company code header and set context variable
    company = request.headers.get("X-Company-Code", "default")
    db.active_company.set(company)
        
    if method not in API_MAP:
        return JSONResponse(content={"ok": False, "error": f"Phương thức API '{method}' không tồn tại trên hệ thống."}, status_code=404)
        
    try:
        handler = API_MAP[method]
        result = handler(*args)
        return JSONResponse(content=result)
    except TypeError as te:
        return JSONResponse(content={"ok": False, "error": f"Lỗi tham số cuộc gọi API: {str(te)}"}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": f"Lỗi thực thi API: {str(e)}"}, status_code=500)

@app.get("/api/downloadBackup")
async def download_backup(name: str, token: str):
    try:
        auth.guard(token, "admin.backup")
        backup_dir = os.path.join(os.path.dirname(__file__), "backups")
        file_path = os.path.join(backup_dir, name)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File không tồn tại.")
            
        from fastapi.responses import FileResponse
        return FileResponse(path=file_path, filename=name, media_type="application/octet-stream")
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))
