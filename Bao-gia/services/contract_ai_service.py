"""
QUOTEFLOW OS - AI Contract Service
Handles drafting contracts and reviewing drafts using the Gemini API.
"""
import os
import json
import urllib.request
from dotenv import load_dotenv

def call_gemini_api(api_key, model, prompt):
    """
    Gửi prompt tới Gemini API sử dụng urllib.request (không cần cài thêm thư viện google-genai).
    """
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
        return f"Lỗi kết nối tới API Gemini (Vui lòng kiểm tra lại Key hoặc kết nối mạng): {str(e)}"

def call_claude_api(api_key, model, prompt):
    """
    Gửi prompt tới Anthropic Claude API sử dụng urllib.request (không cần cài thêm thư viện).
    """
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
        return f"Lỗi kết nối tới API Claude (Vui lòng kiểm tra lại Key hoặc kết nối mạng): {str(e)}"

def draft_contract(contract_type, seller_info, buyer_info, value_str, core_terms, special_terms,
                   payment_method, payment_schedule, lead_time, delivery_location, warranty_period, penalty_terms):
    """
    Soạn thảo hợp đồng dựa trên các thông số đầu vào.
    Ưu tiên sử dụng Claude API nếu có cấu hình CLAUDE_API_KEY, 
    tiếp theo sử dụng Gemini API nếu có GEMINI_API_KEY, 
    nếu không sử dụng Mock Engine.
    """
    load_dotenv(override=True)
    claude_key = os.getenv("CLAUDE_API_KEY", "").strip()
    claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022").strip()
    
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
    
    if (claude_key and not claude_key.startswith("your-") and claude_key != "") or (gemini_key and not gemini_key.startswith("your-") and gemini_key != ""):
        prompt = f"""
Bạn là một chuyên gia pháp lý và luật sư soạn thảo hợp đồng thương mại xuất sắc tại Việt Nam.
Hãy soạn thảo một bản dự thảo Hợp đồng song ngữ Việt - Anh (Bilingual Vietnamese - English) dựa trên các thông tin sau:
- Loại hợp đồng: {contract_type}
- Bên A (Bên bán/Bên cung cấp dịch vụ): {seller_info}
- Bên B (Bên mua/Bên sử dụng dịch vụ): {buyer_info}
- Giá trị hợp đồng ước tính: {value_str} VNĐ
- Các nội dung/điều khoản cốt lõi hàng hóa/dịch vụ: {core_terms}
- Phương thức thanh toán: {payment_method}
- Tiến độ thanh toán: {payment_schedule}
- Thời hạn thực hiện / giao hàng: {lead_time}
- Địa điểm thực hiện / giao hàng: {delivery_location}
- Thời hạn bảo hành: {warranty_period}
- Điều khoản phạt vi phạm: {penalty_terms}
- Yêu cầu đặc biệt bổ sung hoặc điều khoản khác: {special_terms}

YÊU CẦU BẮT BUỘC VỀ ĐỊNH DẠNG (BẮT BUỘC TUÂN THỦ 100%):
1. ĐỊNH DẠNG HEADING:
- Tiêu đề chính dùng Heading 1: `# HỢP ĐỒNG MUA BÁN`
- Các Điều dùng Heading 2: `## Điều 1. Đối tượng hợp đồng`
- Các tiểu mục phụ dùng Heading 3: `### 1.1` hoặc `### 1.2`
- Tuyệt đối không dùng ký tự `###` trong nội dung văn bản thông thường (chỉ dùng làm cú pháp Heading ở đầu dòng).

2. ĐÁNH SỐ ĐIỀU KHOẢN:
- Đánh số tự động tăng dần, không bỏ số, ví dụ:
Điều 1
1.1
1.2
1.2.1
Điều 2
2.1
2.2

3. DANH SÁCH:
- Chỉ sử dụng Markdown chuẩn với dấu gạch ngang `- Nội dung` hoặc số `1.`, `2.`, `3.`. Tuyệt đối không sử dụng ký tự đặc biệt khác như dấu chấm tròn `•` hay icon.

4. BẢNG DỮ LIỆU:
- Nếu có thông tin hàng hóa, sản phẩm, đơn giá, số lượng hoặc các đợt thanh toán, bắt buộc sử dụng bảng Markdown (Markdown Table). Ví dụ:
| STT | Nội dung | Giá trị |
|-----|----------|---------|
| 1 | Laptop Dell | 25.000.000 |

5. CHỮ IN ĐẬM:
- Các tiêu đề quan trọng bắt buộc dùng chữ in đậm: **BÊN A**, **BÊN B**, **ĐIỀU 1**, **ĐIỀU 2**. Không dùng ALL CAPS (viết hoa toàn bộ) cho toàn bộ đoạn văn hay câu dài.

6. TRÍCH DẪN PHÁP LUẬT:
- Khi viện dẫn điều luật, bắt buộc trình bày dưới dạng trích dẫn Markdown (Blockquote): `> Căn cứ Điều ...`

7. KHOẢNG CÁCH DÒNG:
- Giữa các Điều phải có chính xác một dòng trống. Không xuống dòng liên tục nhiều dòng trống.

8. SONG NGỮ:
- Không trộn lẫn tiếng Việt và tiếng Anh trên cùng một dòng. Phải viết đoạn tiếng Việt trước, xuống dòng viết đoạn tiếng Anh ngay dưới. Ví dụ:
**4.1 Địa điểm giao hàng**
Giao tại kho của Bên B.
**4.1 Delivery Location**
Delivered to Buyer's warehouse.

9. KHÔNG SINH HTML:
- Chỉ sử dụng cú pháp Markdown chuẩn. Tuyệt đối không dùng các thẻ HTML như `<br>`, `<div>`, `<p>`, `<span>`, v.v.

10. KHÔNG SINH KÝ TỰ THỪA:
- Không dùng `###`, `***`, `___` ngoài cú pháp Heading/Markdown tiêu chuẩn.

11. KẾT QUẢ CUỐI CÙNG:
- Chỉ trả về nội dung Hợp đồng ở định dạng Markdown hoàn chỉnh. Không giải thích thêm, không thêm lời bình luận, lời mở đầu hay lời kết. Ở cuối hợp đồng, thêm dòng phân cách "--- AI_ADVICE ---" và viết các lưu ý tư vấn của AI bên dưới dòng này (lưu ý tư vấn AI cũng phải tuân thủ định dạng Markdown ở trên).

Hãy thực hiện soạn thảo Hợp đồng theo các tiêu chuẩn nghiêm ngặt nêu trên.
"""
    if claude_key and not claude_key.startswith("your-") and claude_key != "":
        return call_claude_api(claude_key, claude_model, prompt)
    elif gemini_key and not gemini_key.startswith("your-") and gemini_key != "":
        return call_gemini_api(gemini_key, gemini_model, prompt)
    else:
        return get_mock_draft(contract_type, seller_info, buyer_info, value_str, core_terms, special_terms,
                              payment_method, payment_schedule, lead_time, delivery_location, warranty_period, penalty_terms)

def review_contract(contract_content, user_role, key_concerns):
    """
    Rà soát hợp đồng draft và đưa ra các đề xuất chỉnh sửa dưới góc độ bảo vệ quyền lợi người dùng.
    """
    load_dotenv(override=True)
    claude_key = os.getenv("CLAUDE_API_KEY", "").strip()
    claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022").strip()
    
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
    
    prompt = f"""
Bạn là một luật sư tư vấn doanh nghiệp chuyên nghiệp và chuyên gia rà soát rủi ro hợp đồng thương mại.
Hãy rà soát kỹ bản hợp đồng dưới đây dưới góc độ bảo vệ quyền lợi và giảm thiểu rủi ro tối đa cho bên: {user_role}.
- Các mối quan tâm/lo ngại đặc biệt của người dùng: {key_concerns}

Nội dung hợp đồng cần rà soát:
---
{contract_content}
---

Yêu cầu đầu ra (Trình bày dưới dạng Markdown chuyên nghiệp):
1. **Đánh giá tổng quan**: Phân tích mức độ cân bằng của hợp đồng, bên nào đang có nhiều lợi thế hơn, và mức độ rủi ro chung đối với {user_role}.
2. **Các điều khoản rủi ro & Đề xuất sửa đổi**: Liệt kê chi tiết các điều khoản có thể gây bất lợi hoặc rủi ro cho {user_role}. Với mỗi điều khoản, hãy cung cấp:
   - *Nội dung điều khoản gốc* trong hợp đồng.
   - *Phân tích rủi ro cụ thể*.
   - *Đề xuất điều chỉnh chi tiết* (cung cấp câu chữ cụ thể bằng tiếng Việt để người dùng thay thế hoặc đàm phán lại).
3. **Đề xuất bổ sung điều khoản**: Chỉ ra những điều khoản quan trọng còn thiếu trong hợp đồng hiện tại để bảo vệ {user_role} (ví dụ: Giới hạn trách nhiệm, Điều khoản bất khả kháng, Cơ chế giải quyết tranh chấp thuận lợi, Điều khoản bảo mật NDA).
4. **Mẹo đàm phán**: Đưa ra 3-4 lời khuyên chiến thuật giúp người dùng thương lượng thành công các điều khoản này với đối tác.
"""
    if claude_key and not claude_key.startswith("your-") and claude_key != "":
        return call_claude_api(claude_key, claude_model, prompt)
    elif gemini_key and not gemini_key.startswith("your-") and gemini_key != "":
        return call_gemini_api(gemini_key, gemini_model, prompt)
    else:
        return get_mock_review(contract_content, user_role, key_concerns)

def get_mock_draft(contract_type, seller_info, buyer_info, value_str, core_terms, special_terms,
                   payment_method, payment_schedule, lead_time, delivery_location, warranty_period, penalty_terms):
    """
    Tạo dự thảo mẫu song ngữ Việt - Anh dựa trên tệp hợp đồng mẫu của hệ thống, tuân thủ các quy tắc định dạng.
    """
    # Xử lý các dòng trong core_terms thành bảng Markdown
    table_rows = []
    stt = 1
    if core_terms.strip():
        lines = [line.strip("- *•").strip() for line in core_terms.split("\n") if line.strip()]
        for line in lines:
            if ":" in line:
                parts = line.split(":", 1)
                name = parts[0].strip()
                val = parts[1].strip()
                table_rows.append(f"| {stt} | {name} | {val} |")
                stt += 1
            else:
                table_rows.append(f"| {stt} | {line} | - |")
                stt += 1
    
    if not table_rows:
        table_rows.append("| 1 | [Vui lòng điền chi tiết sản phẩm] | - |")
        
    table_content = "\n".join([
        "| STT | Nội dung | Chi tiết |",
        "|-----|----------|----------|",
        "\n".join(table_rows)
    ])

    draft = f"""# HỢP ĐỒNG MUA BÁN

# SALE CONTRACT

Số/No: EDN-BDF-202607-01

> Căn cứ Bộ luật Dân sự số 91/2015/QH13 được Quốc hội khóa 13 thông qua ngày 24/11/2015;

> Pursuant to the Civil Code No. 91/2015/QH13 dated November 24, 2015 of the National Assembly;

> Căn cứ Luật Thương mại số 36/2005/QH11 được Quốc hội khóa 11 thông qua ngày 14/06/2005;

> Pursuant to the Commercial Law No. 36/2005/QH11 dated June 14, 2005 of the National Assembly;

> Căn cứ nhu cầu và khả năng thực tế của hai Bên.

> Based on the actual needs and capabilities of both Parties.

Hôm nay, ngày {__import__('datetime').datetime.now().strftime('%d/%m/%Y')}, hai Bên gồm:

Today, {__import__('datetime').datetime.now().strftime('%B %d, %Y')}, the two Parties are:

**BÊN A** (Bên Mua):
{buyer_info if buyer_info.strip() else "- Tên đơn vị: [Tên Bên Mua]\\n- Đại diện: [Đại diện]\\n- Chức vụ: [Chức vụ]"}

**BÊN A** (Buyer):
{buyer_info if buyer_info.strip() else "- Company Name: [Buyer Name]\\n- Representative: [Rep Name]\\n- Title: [Title]"}

**BÊN B** (Bên Bán):
{seller_info if seller_info.strip() else "- Tên đơn vị: [Tên Bên Bán]\\n- Đại diện: [Đại diện]\\n- Chức vụ: [Chức vụ]"}

**BÊN B** (Seller):
{seller_info if seller_info.strip() else "- Company Name: [Seller Name]\\n- Representative: [Rep Name]\\n- Title: [Title]"}

Hai Bên thống nhất ký kết Hợp đồng mua bán hàng hóa với các điều khoản sau:

The two Parties agree to enter into this sale contract with the following terms:

## Điều 1. Hàng hóa – Số lượng – Đơn giá

1.1 Bên Bán đồng ý cung cấp và Bên Mua đồng ý mua sản phẩm dịch vụ theo chi tiết sau:

{table_content}

1.2 Tổng giá trị hợp đồng tạm tính là: **{value_str if value_str.strip() else "[Giá trị hợp đồng]"}** VNĐ (Đã bao gồm VAT nếu có).

1.3 Số lượng thực tế của mỗi lần giao hàng được xác định theo Phiếu cân và Phiếu giao hàng do Bên Bán lập, có xác nhận của hai Bên.

1.4 Nghĩa vụ thuế: Đơn giá tại Hợp đồng này không bao gồm thuế GTGT (thuộc đối tượng không chịu thuế theo quy định về phụ phẩm nông nghiệp / nguyên liệu thức ăn chăn nuôi). Trường hợp chính sách thuế thay đổi, hai Bên sẽ điều chỉnh bằng phụ lục.

## Article 1. Goods – Quantity – Unit Price

1.1 The Seller agrees to supply and the Buyer agrees to purchase the goods/services as follows:

{table_content}

1.2 The provisional total contract value is: **{value_str if value_str.strip() else "[Contract Value]"}** VND (Including VAT if applicable).

1.3 The actual quantity of each delivery shall be determined by the Weight Slip and Delivery Note issued by the Seller, confirmed by both Parties.

1.4 Tax obligation: The unit price under this Contract does not include VAT (subject to non-taxable agricultural by-products). In case of tax policy changes, the Parties shall adjust via appendix.

## Điều 2. Chất lượng

2.1 Hàng đạt chất lượng thương mại, không có mùi mốc, chua hay bất cứ mùi lạ nào khác.

2.2 Không pha trộn các tạp chất, nguyên liệu khác không phải đối tượng hợp đồng.

2.3 Không lẫn đá, kim loại và chất độc hại.

## Article 2. Quality

2.1 The goods shall be of commercial quality, with no musty, sour or other strange smell.

2.2 Do not mix any other materials or foreign substances.

2.3 No stones, metals or toxic substances.

## Điều 3. Bao bì

3.1 Đóng gói trong bao PP mới.

3.2 Quy cách đóng gói tiêu chuẩn 50kg/bao.

## Article 3. Packaging

3.1 Packed in new PP bags.

3.2 Standard specification of 50kg/bag.

## Điều 4. Giao hàng

4.1 Thời gian giao hàng: {lead_time if lead_time.strip() else "Theo lịch giao hàng hai Bên thống nhất bằng văn bản"}.

4.2 Địa điểm giao hàng: {delivery_location if delivery_location.strip() else "Tại địa chỉ của Bên Mua"}.

4.3 Phương tiện vận chuyển và chi phí vận chuyển do Bên Bán chịu trách nhiệm.

4.4 Bên Bán thông báo trước ít nhất 24 giờ trước mỗi lần giao hàng.

## Article 4. Delivery

4.1 Delivery time: {lead_time if lead_time.strip() else "According to the delivery schedule agreed in writing by the Parties"}.

4.2 Delivery place: {delivery_location if delivery_location.strip() else "At the Buyer's address"}.

4.3 Transportation means and shipping costs shall be borne by the Seller.

4.4 The Seller shall notify at least 24 hours prior to each delivery.

## Điều 5. Thanh toán

5.1 Tiến độ thanh toán: {payment_schedule if payment_schedule.strip() else "Thanh toán trong thời hạn 14 ngày kể từ ngày giao hàng thực tế"}.

5.2 Hình thức thanh toán: {payment_method if payment_method.strip() else "Chuyển khoản vào tài khoản ngân hàng của Bên Bán"}.

5.3 Hồ sơ thanh toán bao gồm: Đề nghị thanh toán, Hợp đồng gốc, Hóa đơn giá trị gia tăng hợp lệ, Phiếu giao hàng hoặc Phiếu cân.

5.4 Trường hợp chậm thanh toán, bên chậm trả phải trả lãi tính theo mức lãi suất nợ quá hạn trung bình trên thị trường theo quy định tại Điều 306 Luật Thương mại 2005. Quá 30 ngày, Bên Bán có quyền tạm ngừng giao hàng.

## Article 5. Payment

5.1 Payment schedule: {payment_schedule if payment_schedule.strip() else "Payment within 14 days from the actual delivery date"}.

5.2 Payment method: {payment_method if payment_method.strip() else "Bank transfer to the Seller's bank account"}.

5.3 Payment documents include: Payment request, Original contract, Valid VAT invoice, Weight Slip or Delivery Note.

5.4 In case of late payment, interest shall be paid at the average market overdue interest rate pursuant to Article 306 of the Commercial Law 2005. Beyond 30 days, the Seller has the right to suspend deliveries.

## Điều 6. Quyền và nghĩa vụ của các Bên

6.1 Bên Mua được quyền từ chối nhận hàng nếu hàng hóa không đúng chất lượng (bị ẩm mốc, có mùi lạ, bao bì rách), không đúng số lượng, hoặc Bên Bán giao trễ mà không thông báo trước.

6.2 Bên Bán không tự ý thay đổi số lượng, giá cả nếu không có đồng ý bằng văn bản của Bên Mua.

6.3 Nếu Bên Bán giao hàng trễ làm Bên Mua thiếu nguyên liệu sản xuất, Bên Bán chịu phạt 8% giá trị phần nghĩa vụ bị vi phạm và phải chịu phần chênh lệch giá phát sinh khi Bên Mua mua hàng thay thế từ nhà cung cấp khác.

## Article 6. Rights and Obligations

6.1 The Buyer has the right to refuse goods if they fail to meet quality (moldy, strange smell, torn bags), incorrect quantity, or late delivery without prior notice.

6.2 The Seller shall not unilaterally change quantity or price without the Buyer's written consent.

6.3 If the Seller delays delivery causing raw material shortage, the Seller shall pay a liquidated-damages penalty of 8% of the breached obligation value and bear the price difference when the Buyer purchases replacement supply.

## Điều 7. Kiểm tra, khiếu nại chất lượng

7.1 Trường hợp tranh chấp chất lượng, mẫu hàng sẽ được gửi đến Quatest 3 để phân tích.

7.2 Kết quả của Quatest 3 là kết quả cuối cùng và ràng buộc cả hai Bên.

7.3 Chi phí giám định do bên có kết quả sai chịu.

## Article 7. Quality Inspection and Claims

7.1 In case of quality dispute, samples shall be sent to Quatest 3 for analysis.

7.2 The Quatest 3 result shall be final and binding on both Parties.

7.3 The inspection cost shall be borne by the Party whose position is proven incorrect.

## Điều 8. Bất khả kháng

8.1 Sự kiện bất khả kháng là sự kiện xảy ra khách quan, không thể lường trước và không thể khắc phục được mặc dù đã áp dụng mọi biện pháp cần thiết trong khả năng cho phép.

8.2 Bên gặp sự kiện bất khả kháng phải thông báo bằng văn bản trong vòng 05 ngày làm việc.

8.3 Nếu sự kiện bất khả kháng kéo dài quá 30 ngày liên tục, mỗi Bên có quyền đơn phương chấm dứt hợp đồng.

## Article 8. Force Majeure

8.1 A force majeure event is an event that occurs objectively, is unforeseeable, and cannot be remedied despite all necessary and reasonable measures having been taken.

8.2 The affected Party shall notify in writing within 5 working days.

8.3 If the force majeure event continues for more than 30 consecutive days, either Party may unilaterally terminate the Contract.

## Điều 9. Giải quyết tranh chấp

9.1 Mọi tranh chấp trước hết giải quyết qua thương lượng.

9.2 Nếu thất bại sau 30 ngày, tranh chấp sẽ đưa ra giải quyết tại Tòa án nhân dân có thẩm quyền theo quy định của Bộ luật Tố tụng Dân sự Việt Nam.

9.3 Bên vi phạm/thua kiện chịu toàn bộ án phí, lệ phí Tòa án và chi phí luật sư hợp lý của Bên kia.

## Article 9. Dispute Resolution

9.1 Any dispute shall first be resolved through negotiation.

9.2 If fails after 30 days, it shall be settled at the competent People's Court.

9.3 The losing Party shall bear all court fees and reasonable legal costs.

## Điều 10. Điều khoản chung và hiệu lực

10.1 Hợp đồng có hiệu lực kể từ ngày ký.

10.2 Mọi sửa đổi phải lập thành phụ lục.

10.3 Bản scan có chữ ký gửi qua email có giá trị như bản chính.

10.4 Hợp đồng lập song ngữ Việt – Anh, bản tiếng Việt được ưu tiên áp dụng nếu có mâu thuẫn.

## Article 10. General Provisions

10.1 The Contract takes effect from signing date.

10.2 Any amendments must be in writing.

10.3 Scanned copies sent via email have legal validity.

10.4 Bilingual contract, the Vietnamese version shall prevail in case of conflict.

Yêu cầu đặc biệt bổ sung:
{special_terms if special_terms.strip() else "- Không có."}

Special requirements:
{special_terms if special_terms.strip() else "- None."}

**ĐẠI DIỆN BÊN A**

**REPRESENTATIVE OF PARTY A**

**ĐẠI DIỆN BÊN B**

**REPRESENTATIVE OF PARTY B**

--- AI_ADVICE ---
> Căn cứ quy định pháp lý, lưu ý tư vấn từ AI:

- **Ngôn ngữ ưu tiên**: Điều 10 quy định rõ nội dung tiếng Việt được ưu tiên áp dụng. Đây là điều khoản chuẩn giúp tránh rủi ro dịch thuật sai lệch khi tranh chấp trước Tòa án Việt Nam.
- **Kiểm định Quatest 3**: Điều 7 quy định cơ quan kiểm định độc lập là Quatest 3. Hãy đảm bảo quy trình lấy mẫu niêm phong được thực hiện đúng quy chuẩn kỹ thuật có chữ ký xác nhận của hai bên.
- **Phạt vi phạm và Giá chênh lệch**: Điều 6.3 quy định Bên Bán phải chịu mức phạt vi phạm 8% nghĩa vụ vi phạm kèm bồi thường phần chênh lệch giá mua ngoài. Đây là điều khoản bảo vệ Bên Mua, cần chuẩn bị đầy đủ hóa đơn mua ngoài làm bằng chứng.
- **Miễn thuế phụ phẩm**: Điều 1.4 nhắc về quy định bã mè/phụ phẩm thức ăn chăn nuôi thuộc đối tượng không chịu thuế GTGT. Hãy lưu ý kiểm tra MST và ngành nghề đăng ký kinh doanh của bên cung cấp để đảm bảo tính hợp lệ.
"""
    return draft

def get_mock_review(contract_content, user_role, key_concerns):
    """
    Tạo đánh giá mẫu khi không có Gemini API Key (chế độ demo).
    """
    review = f"""### 🔍 KẾT QUẢ RÀ SOÁT HỢP ĐỒNG (Chế độ Demo/Offline)
*Phân tích dưới góc độ bảo vệ lợi ích của: **{user_role.upper()}***
*Mối lo ngại đặc biệt: {key_concerns if key_concerns.strip() else "Không có cụ thể"}*

---

#### 1. Đánh giá tổng quan
Hợp đồng hiện tại đang ở dạng cơ bản. Tuy nhiên, các điều khoản về thanh toán và trách nhiệm thực hiện vẫn có những kẽ hở lớn có thể gây bất lợi cho **{user_role}**. Cần thương lượng lại một số điều khoản cốt lõi để đảm bảo sự cân bằng và tránh rủi ro tranh chấp về sau.

#### 2. Các điều khoản rủi ro & Đề xuất sửa đổi chi tiết

| Điều khoản trong hợp đồng | Rủi ro phát sinh | Đề xuất sửa đổi (Câu chữ đàm phán) |
| :--- | :--- | :--- |
| **Thanh toán đợt 2 trong vòng 7 ngày kể từ bàn giao** | Nếu có lỗi kỹ thuật phát sinh ngay sau bàn giao nhưng chưa sửa xong, {user_role} (nếu là Bên mua) vẫn phải trả hết tiền, mất đi công cụ ràng buộc Bên bán. | **Sửa lại:** "Bên B thanh toán 70% giá trị hợp đồng còn lại trong vòng 07 ngày làm việc kể từ ngày nghiệm thu bàn giao và ký Biên bản nghiệm thu đạt yêu cầu, không phát sinh lỗi kỹ thuật nghiêm trọng." |
| **Phạt Bên B chậm thanh toán theo lãi suất 150% lãi suất cơ bản** | Lãi suất phạt này khá cao và chỉ có lợi cho Bên bán. Nếu {user_role} là Bên mua, điều này tạo áp lực tài chính lớn khi có tranh chấp dòng tiền. | **Sửa lại:** "Mức lãi suất chậm thanh toán sẽ áp dụng theo lãi suất nợ quá hạn trung bình của 3 ngân hàng thương mại lớn tại thời điểm phát sinh nợ." |
| **Phạt chậm bàn giao tối đa 8%** | Mức phạt 8% là mức trần theo Luật Thương mại. Tuy nhiên nếu Bên bán chậm trễ quá lâu gây thiệt hại lớn vượt quá 8% thì Bên mua bị thiệt thòi nếu không có điều khoản bồi thường thiệt hại thực tế. | **Bổ sung câu chữ:** "Mức phạt chậm bàn giao là 0.5%/ngày chậm trễ (tối đa 8%). Bên vi phạm phải bồi thường toàn bộ thiệt hại thực tế phát sinh cho bên bị vi phạm do việc chậm trễ gây ra." |

#### 3. Đề xuất bổ sung điều khoản bảo vệ {user_role}
- **Điều khoản Bất khả kháng (Force Majeure):** Cần bổ sung định nghĩa rõ ràng về thiên tai, dịch bệnh, thay đổi chính sách pháp luật để được miễn trừ trách nhiệm khi không thể thực hiện hợp đồng.
- **Điều khoản Bảo mật (NDA):** Bổ sung cam kết không tiết lộ thông tin kinh doanh, thông tin khách hàng và số liệu báo giá của hai bên cho bên thứ ba. Mức phạt vi phạm bảo mật nên quy định cụ thể (ví dụ: 50.000.000 VNĐ/lần vi phạm).
- **Giới hạn trách nhiệm (Limitation of Liability):** Nếu {user_role} là Bên bán, cần bổ sung điều khoản giới hạn tổng trách nhiệm bồi thường thiệt hại tối đa không vượt quá 100% giá trị hợp đồng để quản trị rủi ro pháp lý.

#### 4. Mẹo đàm phán thương lượng
1. **Lấy Luật Thương mại làm điểm tựa**: Khi đàm phán về điều khoản phạt vi phạm và bồi thường, hãy nhấn mạnh rằng các điều chỉnh này hoàn toàn tuân thủ theo Bộ luật Dân sự và Luật Thương mại để đối tác dễ chấp thuận.
2. **Cơ chế thanh toán gắn với nghiệm thu**: Đàm phán thanh toán đợt cuối cùng chỉ được thực hiện sau khi có biên bản nghiệm thu chạy thử thành công. Đây là điểm mấu chốt để bảo vệ chất lượng dịch vụ/sản phẩm.
3. **Nguyên tắc song phương**: Mọi nghĩa vụ phạt chậm trễ hoặc bồi thường nên được quy định song phương (bên nào vi phạm cũng chịu chế tài tương đương) để tạo cảm giác công bằng cho đối tác trong quá trình thương thảo.
"""
    return review

def chat_about_contract(question, contract_context, chat_history):
    """
    Hỏi đáp, trao đổi trực tiếp với AI về nội dung hợp đồng hiện tại.
    """
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
    
    # Chuẩn bị lịch sử trò chuyện (tối đa 6 lượt hội thoại gần nhất để tránh tràn token)
    history_str = ""
    for item in chat_history[-6:]:
        history_str += f"Người dùng: {item['q']}\nAI: {item['a']}\n"
        
    if api_key and not api_key.startswith("your-") and api_key != "":
        prompt = f"""
Bạn là một chuyên gia pháp lý và luật sư tư vấn doanh nghiệp xuất sắc tại Việt Nam, chuyên về hợp đồng thương mại.
Dưới đây là văn bản hợp đồng hiện tại đang thảo luận (Bản nháp hoặc dự thảo vừa tạo):
---
{contract_context if contract_context.strip() else "[Chưa có nội dung hợp đồng, hãy trả lời câu hỏi tổng quát của người dùng]"}
---

Lịch sử trao đổi trước đó:
{history_str}

Hãy trả lời câu hỏi hoặc thực hiện yêu cầu mới nhất của người dùng dưới dạng Markdown rõ ràng, trang trọng, giải thích cặn kẽ và chuyên nghiệp:
Yêu cầu mới nhất của người dùng: {question}
"""
        return call_gemini_api(api_key, model, prompt)
    else:
        return get_mock_chat_response(question, contract_context)

def get_mock_chat_response(question, contract_context):
    """
    Phản hồi giả lập cho chế độ trò chuyện offline.
    """
    q = question.lower()
    if "phạt" in q or "vi phạm" in q:
        return (
            "💡 **Tư vấn AI (Chế độ Demo):**\n\n"
            "Đối với điều khoản phạt vi phạm trong hợp đồng thương mại:\n"
            "- Theo Điều 301 Luật Thương mại 2005, mức phạt vi phạm nghĩa vụ hợp đồng do các bên thỏa thuận nhưng **không quá 8%** giá trị phần nghĩa vụ hợp đồng bị vi phạm.\n"
            "- Tuy nhiên, đối với Hợp đồng dân sự (không có mục đích sinh lợi của ít nhất một bên), Bộ luật Dân sự 2015 không giới hạn mức phạt tối đa.\n"
            "- Khuyên dùng: Nên ghi rõ mức phạt cụ thể (ví dụ: phạt giao hàng chậm 0.5% mỗi ngày chậm trễ) để tăng tính thực thi."
        )
    elif "thanh toán" in q:
        return (
            "💡 **Tư vấn AI (Chế độ Demo):**\n\n"
            "Đối với điều khoản thanh toán:\n"
            "- Nên chia tiến độ thanh toán thành **3 đợt** để đảm bảo an toàn cho cả hai bên:\n"
            "  1. Đợt 1: Tạm ứng 20% - 30% ngay sau khi ký hợp đồng.\n"
            "  2. Đợt 2: Thanh toán 50% - 60% sau khi bàn giao hàng hóa hoặc nghiệm thu kỹ thuật.\n"
            "  3. Đợt 3: Thanh toán 10% - 20% còn lại trong vòng 7-15 ngày sau khi nghiệm thu bàn giao và ký biên bản nghiệm thu cuối cùng.\n"
            "- Nên ghi rõ điều kiện thanh toán (cần có hóa đơn tài chính hợp lệ, biên bản giao nhận có chữ ký hai bên)."
        )
    elif "bảo mật" in q or "nda" in q:
        return (
            "💡 **Tư vấn AI (Chế độ Demo):**\n\n"
            "Để bổ sung điều khoản bảo mật thông tin (NDA), bạn có thể chèn nội dung sau vào hợp đồng:\n"
            "> *'Điều ...: Bảo mật thông tin*\n"
            "> *1. Hai bên cam kết bảo mật tuyệt đối mọi thông tin kỹ thuật, thông tin kinh doanh, số liệu báo giá, thông tin khách hàng nhận được từ bên kia trong suốt thời hạn hợp đồng và ít nhất 02 năm sau khi thanh lý hợp đồng.*\n"
            "> *2. Bên nào vi phạm nghĩa vụ bảo mật phải bồi thường toàn bộ thiệt hại thực tế phát sinh và chịu phạt vi phạm mức [Điền số tiền, ví dụ: 50.000.000 VNĐ] cho mỗi lần vi phạm.'*"
        )
    else:
        return (
            f"💡 **Tư vấn AI (Chế độ Demo):**\n\n"
            f"Tôi đã nhận được câu hỏi liên quan đến hợp đồng: *\"{question}\"*\n\n"
            f"Hiện tại hệ thống đang chạy ở chế độ **Giả lập (Offline/Demo)** do chưa nhận được Gemini API Key thật (hoặc key đang bị lỗi).\n"
            f"Để nhận câu trả lời tư vấn pháp lý thông minh và chính xác dựa trên nội dung hợp đồng thực tế, vui lòng đảm bảo khóa API Gemini được cấu hình đúng trong phần **Cấu hình hệ thống**."
        )

