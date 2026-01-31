import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta, date

# ==========================================
# CẤU HÌNH & AUTH
# ==========================================
ADMIN_USER = "admin"
ADMIN_PASS = "1" 
DATA_FILE = 'tiktok_farm_v2.json'

st.set_page_config(page_title="TikTok Farm Pro", page_icon="🚀", layout="wide")

# ==========================================
# BACKEND: XỬ LÝ DỮ LIỆU AN TOÀN
# ==========================================
def load_data():
    if not os.path.exists(DATA_FILE):
        # Dữ liệu mẫu ban đầu
        data = [
            {
                "id": "iPhone 7-A",
                "status": "Live",
                "username": "user_us_01",
                "niche": "Health",
                "country": "US",
                "proxy_ip": "192.168.1.10",
                "proxy_exp": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                "views": 1500,
                "gmv": 12.5,
                "last_active": "2023-10-25"
            }
        ]
        save_data(data)
        return data
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==========================================
# AUTHENTICATION
# ==========================================
def check_login():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            st.title("🔒 Farm Manager Pro")
            with st.form("login"):
                u = st.text_input("User")
                p = st.text_input("Pass", type="password")
                if st.form_submit_button("Login"):
                    if u == ADMIN_USER and p == ADMIN_PASS:
                        st.session_state["authenticated"] = True
                        st.rerun()
                    else:
                        st.error("Sai thông tin!")
        return False
    return True

# ==========================================
# GIAO DIỆN CHÍNH
# ==========================================
def main_app():
    # Sidebar Menu
    with st.sidebar:
        st.title("🎛️ Menu")
        menu = st.radio("Chọn chức năng:", ["Dashboard Tổng quan", "Quản lý Account (Table)", "Thêm Account Mới"])
        st.divider()
        if st.button("Đăng xuất"):
            st.session_state["authenticated"] = False
            st.rerun()

    # Load dữ liệu thô từ JSON
    raw_data = load_data()
    
    # --- TAB 1: DASHBOARD ---
    if menu == "Dashboard Tổng quan":
        st.title("🚀 Tổng quan hiệu suất Farm")
        
        # Tính toán chỉ số
        df_dash = pd.DataFrame(raw_data)
        if not df_dash.empty:
            total_acc = len(df_dash)
            live_acc = len(df_dash[df_dash['status'] == 'Live'])
            total_gmv = df_dash['gmv'].sum() if 'gmv' in df_dash.columns else 0
        else:
            total_acc = 0; live_acc = 0; total_gmv = 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng Acc", total_acc)
        c2.metric("Acc Live", live_acc)
        c3.metric("Cần xử lý", total_acc - live_acc)
        c4.metric("Tổng GMV", f"${total_gmv}")

        st.divider()
        st.subheader("⚠️ Cảnh báo Proxy")
        
        has_warning = False
        today_date = datetime.now().date()
        
        if not df_dash.empty and 'proxy_exp' in df_dash.columns:
            for index, row in df_dash.iterrows():
                try:
                    # Chuyển string sang date để so sánh
                    p_date = datetime.strptime(str(row['proxy_exp']), '%Y-%m-%d').date()
                    days_left = (p_date - today_date).days
                    
                    if days_left < 0:
                        st.error(f"🔴 **{row['id']}**: Proxy đã hết hạn ({days_left} ngày)!")
                        has_warning = True
                    elif days_left <= 3:
                        st.warning(f"🟡 **{row['id']}**: Proxy sắp hết ({days_left} ngày)!")
                        has_warning = True
                except:
                    pass
        
        if not has_warning:
            st.success("Tất cả Proxy đều ổn định.")

    # --- TAB 2: QUẢN LÝ ACCOUNT (BẢNG EDITOR) ---
    elif menu == "Quản lý Account (Table)":
        st.title("📱 Danh sách & Trạng thái")
        st.info("💡 Bạn có thể sửa trực tiếp mọi ô trong bảng rồi ấn **Lưu thay đổi**.")

        if not raw_data:
            st.warning("Chưa có dữ liệu nào. Hãy qua tab 'Thêm Account Mới'.")
        else:
            df = pd.DataFrame(raw_data)

            # --- [QUAN TRỌNG] XỬ LÝ DỮ LIỆU TRƯỚC KHI HIỂN THỊ ĐỂ TRÁNH LỖI ---
            # 1. Chuyển cột ngày tháng từ String -> Date Object
            if "proxy_exp" in df.columns:
                df["proxy_exp"] = pd.to_datetime(df["proxy_exp"], errors='coerce').dt.date
            
            # 2. Đảm bảo số liệu là số (tránh lỗi null hoặc string)
            df["gmv"] = pd.to_numeric(df["gmv"], errors='coerce').fillna(0.0)
            df["views"] = pd.to_numeric(df["views"], errors='coerce').fillna(0)

            # Cấu hình hiển thị bảng
            edited_df = st.data_editor(
                df,
                column_config={
                    "status": st.column_config.SelectboxColumn(
                        "Trạng thái",
                        options=["Live", "Shadowban", "Die", "Nuôi", "Kháng"],
                        required=True,
                        width="medium"
                    ),
                    "niche": st.column_config.TextColumn(
                        "Chủ đề (Niche)",
                        help="Nhập chủ đề kênh (vd: Health, Pet...)",
                        width="medium"
                    ),
                    "gmv": st.column_config.NumberColumn(
                        "Doanh thu ($)", format="$%.2f"
                    ),
                    "views": st.column_config.NumberColumn(
                        "Views", format="%d"
                    ),
                    "proxy_exp": st.column_config.DateColumn(
                        "Hết hạn Proxy", format="YYYY-MM-DD"
                    ),
                    "id": "Tên máy",
                    "username": "User TikTok",
                    "country": "Quốc gia"
                },
                hide_index=True,
                num_rows="dynamic",
                use_container_width=True
            )

            # Nút Lưu Dữ Liệu
            if st.button("💾 Lưu thay đổi", type="primary"):
                try:
                    # Chuyển DataFrame ngược lại thành List Dictionary
                    saved_data = edited_df.to_dict(orient='records')
                    
                    # --- [QUAN TRỌNG] FORMAT LẠI DATA TRƯỚC KHI LƯU JSON ---
                    final_data = []
                    for item in saved_data:
                        # Convert Date Object -> String (YYYY-MM-DD)
                        if isinstance(item.get('proxy_exp'), (date, datetime)):
                            item['proxy_exp'] = item['proxy_exp'].strftime('%Y-%m-%d')
                        else:
                            # Nếu null hoặc lỗi, set mặc định ngày mai
                            item['proxy_exp'] = str(item.get('proxy_exp') or (datetime.now()+timedelta(days=1)).strftime('%Y-%m-%d'))
                        
                        final_data.append(item)

                    save_data(final_data)
                    st.success("✅ Đã cập nhật dữ liệu thành công!")
                    st.rerun() # Refresh lại trang để nhận data mới
                except Exception as e:
                    st.error(f"Lỗi khi lưu: {e}")

    # --- TAB 3: THÊM ACCOUNT MỚI ---
    elif menu == "Thêm Account Mới":
        st.title("➕ Thêm thiết bị vào Farm")
        
        with st.form("add_acc_form"):
            c1, c2 = st.columns(2)
            new_id = c1.text_input("Tên máy (Ví dụ: iPhone 7-A)", placeholder="Nhập tên thiết bị...")
            new_user = c2.text_input("Username TikTok", placeholder="@username...")
            
            c3, c4 = st.columns(2)
            
            # --- TÍNH NĂNG MỚI: NICHE TÙY CHỈNH ---
            niche_options = ["Gia dụng", "Mỹ phẩm", "Thời trang", "Sức khỏe", "Giải trí", "Nhập thủ công (Khác)..."]
            selected_niche_opt = c3.selectbox("Chủ đề (Niche)", niche_options)
            
            final_niche = selected_niche_opt
            # Nếu chọn "Nhập thủ công" thì hiện ô input mới
            if selected_niche_opt == "Nhập thủ công (Khác)...":
                final_niche = c3.text_input("👉 Nhập tên chủ đề của bạn:", placeholder="Ví dụ: Phong thủy...")

            new_country = c4.selectbox("Quốc gia", ["US", "UK", "FR", "DE", "VN"])
            
            c5, c6 = st.columns(2)
            new_ip = c5.text_input("Proxy IP:Port")
            new_exp = c6.date_input("Ngày hết hạn Proxy")
            
            if st.form_submit_button("Thêm Account"):
                if new_id and new_user:
                    # Logic lấy Niche cuối cùng
                    saved_niche = final_niche if final_niche else "Chưa set"

                    new_record = {
                        "id": new_id,
                        "status": "Nuôi",
                        "username": new_user,
                        "niche": saved_niche, # Lưu giá trị text
                        "country": new_country,
                        "proxy_ip": new_ip,
                        "proxy_exp": new_exp.strftime('%Y-%m-%d'),
                        "views": 0,
                        "gmv": 0.0,
                        "last_active": datetime.now().strftime('%Y-%m-%d')
                    }
                    
                    current_data = load_data()
                    current_data.append(new_record)
                    save_data(current_data)
                    st.success(f"Đã thêm **{new_id}** (Chủ đề: {saved_niche}) thành công!")
                else:
                    st.warning("Vui lòng nhập Tên máy và Username!")

if __name__ == "__main__":
    if check_login():
        main_app()
