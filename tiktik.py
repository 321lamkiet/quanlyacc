import streamlit as st
import pandas as pd
import json
import os
import requests
import time
from datetime import datetime, timedelta, date

# ==========================================
# CẤU HÌNH & AUTH
# ==========================================
try:
    ADMIN_USER = st.secrets["auth"]["username"]
    ADMIN_PASS = st.secrets["auth"]["password"]
except:
    ADMIN_USER = "admin"
    ADMIN_PASS = "mmo888"

DATA_FILE = 'tiktok_farm_v2.json'
VIDEO_DIR = 'video_storage'  # Thư mục lưu video

# Tạo thư mục lưu video nếu chưa có
if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

st.set_page_config(page_title="TikTok Farm Pro Max", page_icon="🚀", layout="wide")

# CSS Tùy chỉnh
st.markdown("""
    <style>
    .stTextInput input {
        background-color: #262730;
        color: #fff;
        border: 1px solid #444;
    }
    .status-badge {
        font-weight: bold; padding: 5px 10px; border-radius: 5px;
    }
    .farm-days {
        color: #FFD700; font-weight: bold; font-size: 14px;
    }
    .content-tag {
        color: #00BFFF; font-weight: bold; font-size: 14px;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #444; border-radius: 8px; margin-bottom: 10px;
    }
    /* Style cho khu vực Video */
    .video-card {
        background-color: #1E1E1E;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #333;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_status_config(status):
    if status == "Live": return "🟢", 0 
    if status == "Nuôi": return "🟡", 1
    if status == "Shadowban": return "❌", 2
    if status == "Die": return "💀", 3
    return "⚪", 4

def check_tiktok_status_simple(username):
    url = f"https://www.tiktok.com/@{username}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            if '"user":{"id":' in r.text or '"uniqueId":' in r.text: return "Live"
            return "Live (Cần check)"
        elif r.status_code == 404: return "Die"
        else: return "Unknown"
    except: return "Error"

# ==========================================
# BACKEND: DATA & FILE
# ==========================================
def load_data():
    default_data = [{
        "id": "iPhone 7-A", "status": "Live", "username": "user_demo", "password": "123",
        "niche": "Health", "content_type": "Reup", "country": "US", 
        "proxy_ip": "1.1.1.1", "proxy_pass": "", 
        "proxy_exp": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        "date_added": datetime.now().strftime('%Y-%m-%d'), "views": 0, "gmv": 0
    }]
    if not os.path.exists(DATA_FILE):
        save_data(default_data)
        return default_data
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data: # Validate fields
                if "password" not in item: item["password"] = ""
                if "date_added" not in item: item["date_added"] = datetime.now().strftime('%Y-%m-%d')
            return data
    except: return default_data

def save_data(data):
    for item in data:
        for key, value in item.items():
            if isinstance(value, (date, datetime)):
                item[key] = value.strftime('%Y-%m-%d')
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_uploaded_file(uploaded_file):
    try:
        file_path = os.path.join(VIDEO_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True
    except:
        return False

# ==========================================
# AUTH
# ==========================================
def check_login():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            st.title("🔒 Login")
            with st.form("login"):
                u = st.text_input("User"); p = st.text_input("Pass", type="password")
                if st.form_submit_button("Login"):
                    if u == ADMIN_USER and p == ADMIN_PASS:
                        st.session_state["authenticated"] = True; st.rerun()
                    else: st.error("Sai thông tin!")
        return False
    return True

# ==========================================
# MAIN APP
# ==========================================
def main_app():
    with st.sidebar:
        st.title("🎛️ Menu")
        # --- THÊM MENU KHO VIDEO VÀO ĐÂY ---
        menu = st.radio("Chức năng:", ["Dashboard", "Quản lý & Copy", "Kho Video", "Tool Check Live", "Thêm Account"])
        st.divider()
        if st.button("Đăng xuất"):
            st.session_state["authenticated"] = False; st.rerun()

    raw_data = load_data()
    
    # --- TAB 1: DASHBOARD ---
    if menu == "Dashboard":
        st.title("🚀 Tổng quan Farm")
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            st.download_button("📥 Tải Backup Data", f, file_name=f"backup_{datetime.now().date()}.json")
        
        df = pd.DataFrame(raw_data)
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng Acc", len(df))
        c2.metric("Acc Live", len(df[df['status'] == 'Live']))
        c3.metric("Acc Nuôi", len(df[df['status'] == 'Nuôi']))
        
        st.divider()
        col_chart, col_warn = st.columns([2, 1])
        with col_chart:
            if not df.empty: st.bar_chart(df['status'].value_counts(), color="#FE2C55")
        with col_warn:
            st.write("⚠️ **Proxy sắp hết hạn**")
            with st.container(height=200):
                today = datetime.now().date()
                for item in raw_data:
                    try:
                        p_date = datetime.strptime(str(item.get('proxy_exp')), '%Y-%m-%d').date()
                        days = (p_date - today).days
                        if days < 3: st.warning(f"{item['id']}: Còn {days} ngày")
                    except: pass

    # --- TAB 2: QUẢN LÝ ---
    elif menu == "Quản lý & Copy":
        st.title("📱 Quản lý Account")
        # Editor Table
        st.subheader("1. Chỉnh sửa")
        df = pd.DataFrame(raw_data)
        edited_df = st.data_editor(df, key="editor", num_rows="dynamic", use_container_width=True)
        if st.button("💾 Lưu thay đổi"):
            save_data(edited_df.to_dict(orient='records'))
            st.success("Đã lưu!"); st.rerun()
        
        st.divider()
        # Mobile Copy
        st.subheader("📋 Copy Mobile")
        search = st.text_input("🔍 Tìm kiếm:", placeholder="Tên máy, user...")
        display_data = raw_data
        if search: display_data = [d for d in raw_data if search.lower() in d['id'].lower() or search.lower() in d['username'].lower()]
        
        for acc in display_data:
            with st.expander(f"{acc['id']} | {acc['username']}"):
                c1, c2 = st.columns(2)
                c1.text_input("User", acc['username'], key=f"u_{acc['id']}")
                c2.text_input("Pass", acc['password'], key=f"p_{acc['id']}")
                st.code(f"{acc.get('proxy_ip','')}:{acc.get('proxy_pass','')}", language="text")

    # --- TAB 3: KHO VIDEO (TÍNH NĂNG MỚI) ---
    elif menu == "Kho Video":
        st.title("🎬 Kho Video Upload")
        st.info(f"📁 Thư mục lưu trữ: `{os.path.abspath(VIDEO_DIR)}`")

        # 1. Khu vực Upload
        with st.container():
            st.subheader("⬆️ Upload Video Mới")
            uploaded_files = st.file_uploader("Kéo thả video vào đây (MP4, MOV)", type=['mp4', 'mov'], accept_multiple_files=True)
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    if save_uploaded_file(uploaded_file):
                        st.success(f"✅ Đã lưu: {uploaded_file.name}")
                time.sleep(1)
                st.rerun()

        st.divider()

        # 2. Danh sách Video
        st.subheader("📂 Danh sách Video đã lưu")
        
        # Lấy danh sách file trong thư mục
        try:
            files = os.listdir(VIDEO_DIR)
            video_files = [f for f in files if f.endswith(('.mp4', '.mov'))]
        except:
            video_files = []

        if not video_files:
            st.warning("Chưa có video nào trong kho.")
        else:
            # Hiển thị dạng lưới
            for vid_file in video_files:
                file_path = os.path.join(VIDEO_DIR, vid_file)
                file_stat = os.stat(file_path)
                file_size_mb = file_stat.st_size / (1024 * 1024)
                
                with st.container():
                    cols = st.columns([1, 3, 1, 1])
                    
                    # Cột 1: Icon
                    with cols[0]:
                        st.markdown(f"### 🎥")
                    
                    # Cột 2: Tên file & Size
                    with cols[1]:
                        st.write(f"**{vid_file}**")
                        st.caption(f"Dung lượng: {file_size_mb:.2f} MB")
                    
                    # Cột 3: Nút Download
                    with cols[2]:
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Tải về",
                                data=f,
                                file_name=vid_file,
                                mime="video/mp4",
                                key=f"dl_{vid_file}"
                            )
                    
                    # Cột 4: Nút Xóa
                    with cols[3]:
                        if st.button("🗑️ Xóa", key=f"del_{vid_file}"):
                            os.remove(file_path)
                            st.rerun()
                    
                    # Preview (Có thể ẩn đi nếu nặng)
                    with st.expander("👁️ Xem trước video"):
                        st.video(file_path)
                    
                    st.divider()

    # --- TAB 4: TOOL CHECK ---
    elif menu == "Tool Check Live":
        st.title("🕵️ Tool Check Live")
        if st.button("Quét ngay"):
            bar = st.progress(0)
            for i, acc in enumerate(raw_data):
                status = check_tiktok_status_simple(acc['username'])
                if status == "Die": acc['status'] = "Die"
                bar.progress((i+1)/len(raw_data))
                time.sleep(1)
            save_data(raw_data)
            st.success("Đã quét xong!")

    # --- TAB 5: THÊM ACCOUNT ---
    elif menu == "Thêm Account":
        st.title("➕ Thêm Account")
        with st.form("add"):
            id_may = st.text_input("Tên máy")
            user = st.text_input("Username")
            pas = st.text_input("Password")
            if st.form_submit_button("Thêm"):
                raw_data.append({"id": id_may, "username": user, "password": pas, "status": "Nuôi", "date_added": datetime.now().strftime('%Y-%m-%d')})
                save_data(raw_data)
                st.success("Đã thêm!")

if __name__ == "__main__":
    if check_login():
        main_app()
