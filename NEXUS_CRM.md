Bạn là một Senior Fullstack Developer chuyên Google Apps Script, Google Workspace và CRM.

Hãy xây dựng cho tôi một hệ thống CRM hoàn chỉnh bằng Google Apps Script tương tự Hubspot mini.

## Mục tiêu

Xây dựng CRM chạy trên Google Apps Script + Google Sheets + HTML/CSS/Javascript.

## Kiến trúc hệ thống

Backend:

* Google Apps Script
* SpreadsheetApp
* PropertiesService
* CacheService
* Trigger Service

Database:

* Google Sheets

Frontend:

* HTML
* CSS
* Bootstrap 5
* Javascript thuần
* DataTables
* SweetAlert2
* Font Awesome

## Các module cần có

### 1. Đăng nhập

* Email
* Password
* Session
* Logout
* Phân quyền

  * Admin
  * Sale
  * Manager

### 2. Dashboard

Hiển thị:

* Tổng khách hàng
* Khách hàng mới hôm nay
* Số khách đang chăm sóc
* Doanh thu
* Tỷ lệ chuyển đổi
* KPI sale

Biểu đồ:

* Line Chart
* Pie Chart
* Bar Chart

### 3. Quản lý khách hàng

Thông tin:

ID
Tên khách hàng
Điện thoại
Email
Nguồn khách

Nguồn:

Facebook
Zalo
Website
Email
Referral
Ads

Trạng thái:

Lead
Tiềm năng
Đang tư vấn
Đàm phán
Đã chốt
Thất bại

Tính năng:

CRUD
Import Excel
Export Excel
Search realtime
Filter
Pagination
Tag khách hàng
Upload file
Lưu ghi chú

### 4. Lịch sử chăm sóc

Lưu:

Ngày gọi
Người phụ trách
Nội dung trao đổi
Ghi chú
Kết quả

Timeline hoạt động

Hiển thị theo dạng:

Facebook CRM style

### 5. Follow-up tự động

Cho phép:

Đặt lịch chăm sóc

Ngày hẹn

Giờ hẹn

Nhắc việc

Email reminder

Notification

Trigger Apps Script

### 6. Pipeline bán hàng

Kanban Board

Lead

Contacted

Proposal

Negotiation

Won

Lost

Kéo thả trạng thái.

### 7. Báo cáo

Doanh thu

Sale hiệu quả

Nguồn khách hiệu quả

Tỷ lệ chuyển đổi

Báo cáo theo tháng

Báo cáo theo nhân viên

Dashboard realtime.

### 8. Quản trị hệ thống

Quản lý user

Phân quyền

Nhật ký hoạt động

Audit Log

Backup dữ liệu

Khôi phục dữ liệu

## Yêu cầu kỹ thuật

Viết theo cấu trúc:

01_Config.gs

02_Utils.gs

03_Auth.gs

04_Code.gs

05_Customer.gs

06_Dashboard.gs

07_Report.gs

08_Automation.gs

09_EmailTemplate.gs

10_Integrations.gs

11_AI.gs

12_Webhook.gs

13_Trigger.gs

01_Index.html

02_Style.html

03_Components.html

04_Script.html

## UI

Thiết kế giao diện hiện đại.

Phong cách:

Hubspot

Pipedrive

Zoho CRM

Màu sắc:

#0F172A
#2563EB
#3B82F6
#F8FAFC

Responsive Mobile.

Sidebar cố định.

Topbar.

Dark mode.

Card KPI.

Kanban Drag & Drop.

Modal Bootstrap.

DataTable.

SweetAlert.

## Yêu cầu code

* Tách module rõ ràng
* Có comment đầy đủ
* Code chuẩn ES6
* Tối ưu tốc độ Apps Script
* Hạn chế gọi Spreadsheet nhiều lần
* Dùng batch update
* Sử dụng CacheService
* Dùng LockService tránh xung đột dữ liệu
* Có xử lý lỗi try/catch
* Có loading spinner
* Có toast notification

## Deliverables

1. Thiết kế kiến trúc hệ thống
2. Cấu trúc Google Sheet
3. Toàn bộ source code Apps Script
4. Toàn bộ HTML/CSS/Javascript
5. Trigger tự động
6. Hướng dẫn Deploy Web App
7. Hướng dẫn phân quyền người dùng
8. Hướng dẫn backup dữ liệu
9. Hướng dẫn mở rộng tích hợp:

   * Zalo OA API
   * Facebook Lead API
   * Gmail API
   * Google Calendar API
   * Google Drive API

Xuất code đầy đủ từng file theo thứ tự để tôi có thể copy trực tiếp vào Apps Script và chạy ngay.
Bổ sung tính năng CRM đa kênh:

- Đồng bộ Zalo OA
- Đồng bộ Facebook Messenger
- Đồng bộ Email Gmail
- Đồng bộ Form Website
- Ghi lịch sử cuộc gọi
- Gắn tag khách hàng tự động
- AI gợi ý kịch bản chăm sóc
- Tự động phân loại khách hàng
- Nhắc lịch follow-up thời gian thực
- Dashboard realtime
- KPI Sale
- Cảnh báo khách hàng quá hạn chăm sóc
- Gửi email tự động theo workflow
- Marketing Automation
