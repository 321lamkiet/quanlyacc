import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta

# ==========================================
# CẤU HÌNH USER/PASS (SỬA TẠI ĐÂY)
# ==========================================
ADMIN_USER = "admin"
ADMIN_PASS = "mmo888"  # <--- Đổi mật khẩu của bạn ở đây

# ==========================================
# CẤU HÌNH HỆ THỐNG
# ==========================================
DATA_FILE = 'tiktok_farm_data.json'
st.set_page_config(page_title="TikTok Farm OS", page_icon="📱", layout="centered")

# CSS Tùy chỉnh (Giữ nguyên tối ưu cho Mobile)
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        height: 3em;
        font-weight: bold;
        font-size: 18px;
        border-radius: 12px;
    }
    .stCheckbox {
        padding: 10px;
        background-color: #262730;
        border-radius: 8px;
        margin-bottom: 5px;
    }
    /* Form đăng nhập đẹp hơn */
    [data-testid="stForm"] {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #333;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# XỬ LÝ DỮ LIỆU (BACKEND)
# ==========================================
def load_data():
    if not os.path.exists(DATA_FILE):
        # Dữ liệu mẫu
        dummy_data = {
            "iPhone 7-A": {
                "status": "Live",
                "info": {"username": "user_us_01", "password": "PassWord123!", "email": "mail1@tm.com", "imei": "99000123456", "country": "US"},
                "proxy": {"ip": "192.168.1.100", "port": "8080", "expire": (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')},
                "daily_log": {}
            }
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(dummy_data, f, ensure_ascii=False, indent=4)
        return dummy_data
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def check_proxy_health(expire_date_str):
    try:
        exp_date = datetime.strptime(expire_date_str, '%Y-%m-%d')
        days_left = (exp_date - datetime.now()).days
        if days_left < 0: return "HẾT HẠN", "error"
        if days_left <= 3: return f"Còn {days_left} ngày", "warning"
        return f"Còn {days_left} ngày", "success"
    except:
        return "Lỗi ngày", "error"

# ==========================================
# CHỨC NĂNG ĐĂNG NHẬP (SESSION)
# ==========================================
def check_login():
    """Hàm chặn đăng nhập"""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    # Giao diện đăng nhập
    st.title("🔒 TikTok Farm Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Đăng nhập")
        
        if submitted:
            if username == ADMIN_USER and password == ADMIN_PASS:
                st.session_state["authenticated"] = True
                st.success("Đăng nhập thành công!")
                st.rerun()
            else:
                st.error("Sai tài khoản hoặc mật khẩu")
    
    return False

# ==========================================
# GIAO DIỆN CHÍNH (DASHBOARD)
# ==========================================
def main_app():
    # Sidebar: Nút Logout
    with st.sidebar:
        st.write(f"User: **{ADMIN_USER}**")
        if st.button("Đăng xuất"):
            st.session_state["authenticated"] = False
            st.rerun()
        st.divider()

    data = load_data()
    
    # Sidebar: Chọn máy
    st.sidebar.title("📱 Danh sách máy")
    device_list = ["🏠 Dashboard"] + list(data.keys())
    selected_view = st.sidebar.radio("Chọn thiết bị:", device_list)

    # --- VIEW: DASHBOARD ---
    if selected_view == "🏠 Dashboard":
        st.title("🎛️ Tổng Quan Farm")
        
        # Metric nhanh
        live_count = sum(1 for x in data.values() if x['status'] == 'Live')
        col1, col2 = st.columns(2)
        col1.metric("Tổng máy", len(data))
        col2.metric("Đang sống", live_count)
        
        st.divider()
        
        # List view
        for dev_name, info in data.items():
            stt = info['status']
            icon = "🟢" if stt == "Live" else ("🔴" if stt == "Shadowban" else "🟡")
            prox_msg, prox_type = check_proxy_health(info['proxy']['expire'])
            warn = "⚠️" if prox_type != "success" else ""
            
            with st.expander(f"{icon} {dev_name} {warn}"):
                st.caption(f"User: {info['info']['username']}")
                st.markdown(f"Status: **{stt}** | Proxy: {prox_msg}")

    # --- VIEW: CHI TIẾT MÁY ---
    else:
        dev_name = selected_view
        acc = data[dev_name]
        
        st.header(f"📱 {dev_name}")
        
        # 1. Đổi trạng thái nhanh
        st.caption("Trạng thái hiện tại:")
        c1, c2 = st.columns([3, 1])
        with c1:
            new_stt = st.selectbox("Status", ["Live", "Shadowban", "Cần chăm sóc"], 
                                   index=["Live", "Shadowban", "Cần chăm sóc"].index(acc.get('status', 'Live')), 
                                   label_visibility="collapsed")
        with c2:
            if new_stt != acc['status']:
                acc['status'] = new_stt
                save_data(data)
                st.rerun()

        st.divider()

        # 2. Thông tin Login (Copy nhanh)
        with st.expander("🔑 Thông tin Login & Proxy", expanded=True):
            st.text("Username / Password:")
            st.code(f"{acc['info']['username']}\n{acc['info']['password']}", language="text")
            st.text(f"Proxy IP ({acc['proxy']['expire']}):")
            st.code(f"{acc['proxy']['ip']}:{acc['proxy']['port']}", language="text")

        # 3. Daily Checklist
        st.subheader("✅ Việc hôm nay")
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Tạo log ngày mới nếu chưa có
        if today not in acc['daily_log']:
            acc['daily_log'][today] = {"tasks": {}, "note": ""}
            
        day_log = acc['daily_log'][today]
        tasks = day_log.get('tasks', {})
        
        # Checkbox list
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            t1 = st.checkbox("Ngâm máy", value=tasks.get('soak', False))
            t2 = st.checkbox("Tương tác", value=tasks.get('interact', False))
        with col_t2:
            t3 = st.checkbox("Đăng Video", value=tasks.get('post', False))
            t4 = st.checkbox("Rep Comment", value=tasks.get('reply', False))
            
        # Lưu task tự động
        cur_tasks = {'soak': t1, 'interact': t2, 'post': t3, 'reply': t4}
        if cur_tasks != tasks:
            acc['daily_log'][today]['tasks'] = cur_tasks
            save_data(data)
            
        # 4. Ghi chú nhanh
        st.subheader("📝 Ghi chú")
        note = st.text_area("Note tình trạng:", value=day_log.get('note', ""), height=100)
        if st.button("Lưu Ghi chú"):
            acc['daily_log'][today]['note'] = note
            save_data(data)
            st.success("Đã lưu!")

# ==========================================
# MAIN ENTRY
# ==========================================
if __name__ == "__main__":
    if check_login():
        main_app()
