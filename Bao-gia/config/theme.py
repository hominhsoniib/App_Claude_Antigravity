import streamlit as st

def apply_custom_theme():
    """Injects custom CSS to style the sidebar with a beautiful blue color and set a professional Vietnamese font."""
    # Nạp font Inter bằng link HTML trực tiếp để đảm bảo trình duyệt luôn load thành công
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        
        <style>
        /* Ép toàn bộ các thẻ HTML sử dụng font Inter */
        * {
            font-family: 'Inter', sans-serif !important;
        }

        /* Sidebar background styling */
        section[data-testid="stSidebar"] {
            background-color: #1F3864 !important; /* Deep Corporate Blue */
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Sidebar text color override */
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, 
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] caption,
        section[data-testid="stSidebar"] label {
            color: #F8FAFC !important;
        }

        /* Subtitle and divider color adjustment */
        section[data-testid="stSidebar"] hr {
            border-color: rgba(255, 255, 255, 0.15) !important;
        }

        /* Sidebar menu items styling */
        div[data-testid="stSidebarNavItems"] a {
            color: #E2E8F0 !important;
            border-radius: 8px !important;
            margin: 4px 12px !important;
            padding: 8px 16px !important;
            transition: all 0.3s ease !important;
            font-weight: 500 !important;
        }

        /* Hover state */
        div[data-testid="stSidebarNavItems"] a:hover {
            color: #FFFFFF !important;
            background-color: rgba(255, 255, 255, 0.1) !important;
            text-decoration: none !important;
        }

        /* Active menu item */
        div[data-testid="stSidebarNavItems"] a[aria-current="page"] {
            color: #FFFFFF !important;
            background-color: #2563EB !important; /* Premium Royal Blue */
            font-weight: 600 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        }

        /* Customize Streamlit sidebar headers and hide default group header (like 'app') */
        section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] {
            background-color: transparent !important;
        }
        
        section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] h2 {
            display: none !important;
        }
        
        /* Đổi chữ 'app' ở menu thành 'BÁO GIÁ CHO KHÁCH HÀNG' */
        [data-testid="stSidebarNav"] ul li:first-child a span,
        [data-testid="stSidebarNav"] a[href$="/"] span,
        [data-testid="stSidebarNav"] a[href*="/app"] span {
            font-size: 0 !important;
        }
        
        [data-testid="stSidebarNav"] ul li:first-child a span::after,
        [data-testid="stSidebarNav"] a[href$="/"] span::after,
        [data-testid="stSidebarNav"] a[href*="/app"] span::after {
            content: "📊 BÁO GIÁ CHO KHÁCH HÀNG" !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            display: inline-block !important;
        }
        /* Nút Đăng xuất màu đỏ ở sidebar */
        section[data-testid="stSidebar"] button {
            background-color: transparent !important;
            color: #EF4444 !important;
            border: 1px solid rgba(239, 68, 68, 0.5) !important;
            border-radius: 8px !important;
            transition: all 0.2s ease-in-out !important;
        }
        section[data-testid="stSidebar"] button:hover {
            background-color: rgba(239, 68, 68, 0.1) !important;
            border-color: #EF4444 !important;
        }
        section[data-testid="stSidebar"] button p,
        section[data-testid="stSidebar"] button span {
            color: #EF4444 !important; /* Chữ màu đỏ */
        }
        section[data-testid="stSidebar"] button:hover p,
        section[data-testid="stSidebar"] button:hover span {
            color: #DC2626 !important;
        }
        
        /* Make sure warnings in sidebar are visible */
        section[data-testid="stSidebar"] .stAlert p {
            color: #1F2937 !important; /* Keep alert text readable */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
