import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta, date

# ==========================================
# CẤU HÌNH & AUTH
# ==========================================
ADMIN_USER = "admin"
ADMIN_PASS = "mmo888" 
DATA_FILE = 'tiktok_farm_v2.json'

st.set_page_config(page_title="TikTok Farm Pro", page_icon="🚀", layout="wide")

# CSS Tùy chỉnh để nút Copy to hơn trên Mobile
st.markdown("""
    <style>
    /* Tăng kích thước nút Copy trong st.code */
    button[title="Copy to clipboard"] {
        font-size: 1.2rem !important; 
        padding: 10px !important;
    }
    .stCode {
        font-size: 16px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# BACKEND: XỬ LÝ DỮ LIỆU
# ==========================================
def load_data():
    default_data = [
        {
            "id": "iPhone 7-A",
            "status": "Live",
            "username": "user_us_01",
            "password": "pass_tiktok_123", # Mật khẩu TikTok
            "niche": "Health",
            "country": "US",
            "proxy_ip": "192.168.1.10:8000",
            "proxy_pass": "proxypass1",      # Mật khẩu Proxy
            "proxy_exp": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "views": 1500,
            "gmv": 12.5
        }
    ]
    
    if not os.path.exists(DATA_FILE):
        save_data(default_data)
        return default_data
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Migration: Đảm bảo các field mới luôn tồn tại để tránh lỗi
            for item in data:
                if "password" not in item: item["password"] = ""
                if "proxy_pass" not in item: item["proxy_pass"] = ""
            return data
    except:
        return default_data

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
            st.title("🔒 Farm Login")
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
    with st.sidebar:
        st.title("🎛️ Menu")
        menu = st.radio("Chức năng:", ["Dashboard", "Quản lý & Copy", "Thêm Account"])
        st.divider()
        if st.button("Đăng xuất"):
            st.session_state["authenticated"] = False
            st.rerun()

    raw_data = load_data()
    
    # --- TAB 1: DASHBOARD ---
    if menu == "Dashboard":
        st.title("🚀 Tổng quan Farm")
        if not raw_data:
            st.warning("Chưa có dữ liệu.")
            return

        df = pd.DataFrame(raw_data)
        
        # Chỉ số
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng Acc", len(df))
        live_count = len(df[df['status'] == 'Live'])
        c2.metric("Đang sống", live_count)
        # Tính GMV an toàn
        total_gmv = pd.to_numeric(df.get('gmv', 0), errors='coerce').sum()
        c3.metric("Doanh thu", f"${total_gmv:.2f}")

        st.divider()
        st.subheader("⚠️ Cảnh báo Proxy")
        today = datetime.now().date()
        
        for item in raw_data:
            try:
                p_date = datetime.strptime(str(item.get('proxy_exp')), '%Y-%m-%d').date()
                days = (p_date - today).days
                if days < 0:
                    st.error(f"🔴 {item['id']}: Proxy Hết hạn {abs(days)} ngày!")
                elif days <= 3:
                    st.warning(f"🟡 {item['id']}: Proxy còn {days} ngày!")
            except: pass

    # --- TAB 2: QUẢN LÝ & COPY (QUAN TRỌNG) ---
    elif menu == "Quản lý & Copy":
        st.title("📱 Quản lý Account")
        
        if not raw_data:
            st.info("Chưa có account nào.")
        else:
            df = pd.DataFrame(raw_data)
            
            # 1. Bảng chỉnh sửa số liệu (Editor)
            st.subheader("1. Cập nhật chỉ số (Sửa trực tiếp)")
            
            # Xử lý data an toàn trước khi hiển thị
            if "proxy_exp" in df.columns:
                df["proxy_exp"] = pd.to_datetime(df["proxy_exp"], errors='coerce').dt.date
            
            edited_df = st.data_editor(
                df,
                column_config={
                    "status": st.column_config.SelectboxColumn("Trạng thái", options=["Live", "Shadowban", "Die", "Nuôi"], width="small"),
                    "niche": st.column_config.TextColumn("Chủ đề"),
                    "password": st.column_config.TextColumn("Pass TikTok", type="default"), # Để hiện text cho dễ nhìn
                    "proxy_pass": st.column_config.TextColumn("Pass Proxy"),
                    "gmv": st.column_config.NumberColumn("GMV ($)", format="$%.2f"),
                    "id": "Tên máy",
                    "username": "User"
                },
                hide_index=True,
                num_rows="dynamic",
                use_container_width=True,
                key="editor"
            )

            if st.button("💾 Lưu thay đổi bảng trên", type="primary"):
                try:
                    save_list = edited_df.to_dict(orient='records')
                    # Format lại date thành string
                    for item in save_list:
                        if isinstance(item.get('proxy_exp'), (date, datetime)):
                            item['proxy_exp'] = item['proxy_exp'].strftime('%Y-%m-%d')
                        else:
                            item['proxy_exp'] = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                    save_data(save_list)
                    st.success("Đã lưu dữ liệu!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")

            st.divider()

            # 2. KHU VỰC COPY NHANH (GIẢI PHÁP CHO MOBILE)
            st.subheader("📋 Copy Nhanh (Mobile Mode)")
            st.caption("Bấm vào biểu tượng 📄 ở góc phải mỗi ô để copy.")
            
            # Bộ lọc để tìm cho nhanh
            search = st.text_input("🔍 Tìm máy hoặc user để copy:", placeholder="Nhập tên máy...")
            
            # Lọc dữ liệu hiển thị card
            display_data = raw_data
            if search:
                display_data = [d for d in raw_data if search.lower() in d['id'].lower() or search.lower() in d['username'].lower()]

            # Hiển thị dạng Card
            for acc in display_data:
                status_icon = "🟢" if acc['status'] == "Live" else "🔴"
                
                with st.expander(f"{status_icon} {acc['id']} | {acc['username']}", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.caption("User TikTok")
                        st.code(acc['username'], language=None)
                    with c2:
                        st.caption("Pass TikTok")
                        st.code(acc.get('password', ''), language=None)
                    
                    c3, c4 = st.columns(2)
                    with c3:
                        st.caption("Proxy IP:Port")
                        st.code(acc.get('proxy_ip', ''), language=None)
                    with c4:
                        st.caption("Proxy Pass")
                        st.code(acc.get('proxy_pass', ''), language=None)

    # --- TAB 3: THÊM ACCOUNT MỚI ---
    elif menu == "Thêm Account":
        st.title("➕ Thêm Account")
        
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            new_id = c1.text_input("Tên máy (VD: iPhone 7-A)")
            new_country = c2.selectbox("Quốc gia", ["US", "UK", "FR", "VN"])
            
            st.markdown("---")
            st.write("Tk TikTok:")
            t1, t2 = st.columns(2)
            new_user = t1.text_input("Username")
            new_pass = t2.text_input("Password TikTok") # ĐÃ THÊM Ô NÀY
            
            # LOGIC CHỦ ĐỀ (NICHE)
            st.markdown("---")
            n1, n2 = st.columns([1, 1])
            with n1:
                niche_opt = st.selectbox("Chọn Chủ đề", ["Sức khỏe", "Gia dụng", "Thời trang", "Nhập thủ công..."])
            
            # Logic xử lý text input
            final_niche = niche_opt
            if niche_opt == "Nhập thủ công...":
                with n2:
                    custom_niche = st.text_input("👉 Nhập tên chủ đề tại đây:")
                    if custom_niche:
                        final_niche = custom_niche
                    else:
                        final_niche = "Chưa đặt tên"

            st.markdown("---")
            st.write("Proxy Info:")
            p1, p2 = st.columns(2)
            new_ip = p1.text_input("IP:Port")
            new_prox_pass = p2.text_input("Proxy Password (nếu có)") # ĐÃ THÊM Ô NÀY
            new_exp = st.date_input("Ngày hết hạn Proxy")

            if st.form_submit_button("Thêm ngay"):
                if new_id and new_user:
                    new_obj = {
                        "id": new_id,
                        "status": "Nuôi",
                        "username": new_user,
                        "password": new_pass,      # Lưu Pass TikTok
                        "niche": final_niche,      # Lưu Niche chuẩn
                        "country": new_country,
                        "proxy_ip": new_ip,
                        "proxy_pass": new_prox_pass, # Lưu Pass Proxy
                        "proxy_exp": new_exp.strftime('%Y-%m-%d'),
                        "views": 0,
                        "gmv": 0.0,
                        "last_active": datetime.now().strftime('%Y-%m-%d')
                    }
                    data = load_data()
                    data.append(new_obj)
                    save_data(data)
                    st.success(f"Đã thêm {new_id} - Chủ đề: {final_niche}")
                else:
                    st.error("Thiếu Tên máy hoặc Username!")

if __name__ == "__main__":
    if check_login():
        main_app()
