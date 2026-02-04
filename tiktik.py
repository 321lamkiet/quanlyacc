import streamlit as st
import pandas as pd
import json
import time
import requests
from datetime import datetime, timedelta, date
from github import Github

# ==========================================
# 1. CẤU HÌNH TRANG & ÉP GIAO DIỆN DARK MODE
# ==========================================
st.set_page_config(page_title="TikTok Farm Mobile", page_icon="📱", layout="wide")

# CSS QUAN TRỌNG: Sửa lỗi màn hình trắng trên iPhone
st.markdown("""
    <style>
    /* 1. Ép nền đen cho toàn bộ web (Sửa lỗi iPhone Light Mode) */
    [data-testid="stAppViewContainer"] {
        background-color: #0e1117;
        color: white;
    }
    [data-testid="stHeader"] {
        background-color: #0e1117; /* Ẩn thanh header trắng */
    }
    [data-testid="stToolbar"] {
        right: 2rem;
    }
    
    /* 2. Tối ưu ô nhập liệu trên Mobile */
    .stTextInput input {
        background-color: #262730 !important;
        color: white !important;
        border: 1px solid #444 !important;
    }
    
    /* 3. Button to và dễ bấm hơn trên điện thoại */
    .stButton button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
    
    /* 4. Ẩn bớt padding thừa */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KẾT NỐI GITHUB (XỬ LÝ LỖI 401)
# ==========================================
# Lấy Config an toàn, nếu lỗi thì hiện thông báo đẹp thay vì crash app
try:
    ADMIN_USER = st.secrets["auth"]["username"]
    ADMIN_PASS = st.secrets["auth"]["password"]
    GH_TOKEN = st.secrets["github"]["token"]
    GH_REPO_NAME = st.secrets["github"]["repo_name"]
    GH_BRANCH = st.secrets["github"].get("branch", "main")
except Exception as e:
    st.error(f"⛔ Lỗi cấu hình Secrets: {e}")
    st.info("Vui lòng vào Settings -> Secrets trên Streamlit Cloud để điền Token mới.")
    st.stop() # Dừng app an toàn

DATA_FILE_PATH = 'tiktok_farm_data.json'
VIDEO_FOLDER = 'videos/'

@st.cache_resource
def get_repo():
    """Kết nối GitHub an toàn"""
    try:
        g = Github(GH_TOKEN)
        return g.get_repo(GH_REPO_NAME)
    except Exception as e:
        return None

def load_data_from_github():
    repo = get_repo()
    if not repo: return [] # Trả về rỗng nếu lỗi kết nối
    try:
        content = repo.get_contents(DATA_FILE_PATH, ref=GH_BRANCH)
        json_str = content.decoded_content.decode("utf-8")
        data = json.loads(json_str)
        # Validate data
        for item in data:
            if "status" not in item: item["status"] = "Nuôi"
            if "date_added" not in item: item["date_added"] = datetime.now().strftime('%Y-%m-%d')
        return data
    except:
        return []

def save_data_to_github(data):
    repo = get_repo()
    if not repo: 
        st.error("Mất kết nối GitHub (Token lỗi?)"); return False
    
    # Convert date
    for item in data:
        for k, v in item.items():
            if isinstance(v, (date, datetime)): item[k] = v.strftime('%Y-%m-%d')
    
    json_str = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        contents = repo.get_contents(DATA_FILE_PATH, ref=GH_BRANCH)
        repo.update_file(contents.path, f"Update {datetime.now().strftime('%H:%M')}", json_str, contents.sha, branch=GH_BRANCH)
        return True
    except:
        try:
            repo.create_file(DATA_FILE_PATH, "Init", json_str, branch=GH_BRANCH)
            return True
        except: return False

# ==========================================
# 3. GIAO DIỆN & LOGIC
# ==========================================
def check_tiktok_status_simple(username):
    # Fake check để tránh request nhiều khi test
    return "Live" 

def check_login():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        st.title("🔒 Đăng Nhập")
        with st.form("login_form"):
            u = st.text_input("User")
            p = st.text_input("Pass", type="password")
            if st.form_submit_button("Vào Farm"):
                if u == ADMIN_USER and p == ADMIN_PASS:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else: st.error("Sai thông tin!")
        return False
    return True

def main_app():
    # --- Sidebar ---
    with st.sidebar:
        st.header(f"Xin chào, {ADMIN_USER}")
        menu = st.radio("Menu", ["📱 Copy Mobile", "📊 Dashboard", "⚙️ Quản lý Acc", "☁️ Kho Video"])
        if st.button("Đăng xuất"):
            st.session_state["authenticated"] = False
            st.rerun()

    # Load Data
    if "data_cache" not in st.session_state:
        with st.spinner("Đang tải dữ liệu..."):
            st.session_state["data_cache"] = load_data_from_github()
    raw_data = st.session_state["data_cache"]

    # --- 1. COPY MOBILE (Ưu tiên đưa lên đầu cho tiện) ---
    if menu == "📱 Copy Mobile":
        st.title("📱 Copy Nhanh")
        search = st.text_input("🔍 Tìm User/Máy...", placeholder="Gõ tên...")
        
        # Lọc dữ liệu
        view_data = raw_data
        if search: 
            view_data = [d for d in raw_data if search.lower() in str(d).lower()]
        
        if not view_data:
            st.info("Chưa có account nào. Qua tab 'Quản lý Acc' để thêm nhé!")
        
        # Hiển thị dạng thẻ mobile
        for acc in view_data:
            with st.expander(f"{acc.get('id')} | {acc.get('username')}", expanded=False):
                c1, c2 = st.columns(2)
                c1.text_input("User:", acc.get('username'), key=f"u_{acc.get('id')}")
                c2.text_input("Pass:", acc.get('password'), key=f"p_{acc.get('id')}")
                
                st.caption("Proxy:")
                st.code(acc.get('proxy_ip'), language="text")

    # --- 2. DASHBOARD ---
    elif menu == "📊 Dashboard":
        st.title("📊 Tổng Quan")
        if not raw_data: st.warning("Chưa có data."); return
        
        df = pd.DataFrame(raw_data)
        c1, c2 = st.columns(2)
        c1.metric("Tổng Acc", len(df))
        c2.metric("Acc Live", len(df[df['status']=='Live']))
        
        st.bar_chart(df['status'].value_counts())
        
        if st.button("🔄 Reload dữ liệu từ GitHub"):
            st.cache_data.clear()
            del st.session_state["data_cache"]
            st.rerun()

    # --- 3. QUẢN LÝ ACC ---
    elif menu == "⚙️ Quản lý Acc":
        st.title("⚙️ Quản lý Account")
        
        with st.expander("➕ Thêm Account Mới"):
            with st.form("add_new"):
                id_may = st.text_input("Tên máy (VD: IP-01)")
                user = st.text_input("Username")
                pas = st.text_input("Password")
                proxy = st.text_input("Proxy IP")
                if st.form_submit_button("Lưu lên Cloud"):
                    new_acc = {
                        "id": id_may, "username": user, "password": pas, 
                        "proxy_ip": proxy, "status": "Nuôi", 
                        "date_added": datetime.now().strftime('%Y-%m-%d')
                    }
                    raw_data.append(new_acc)
                    if save_data_to_github(raw_data):
                        st.success("Đã lưu!")
                        st.session_state["data_cache"] = raw_data
                        time.sleep(1); st.rerun()
                    else: st.error("Lỗi lưu GitHub!")

        st.subheader("Chỉnh sửa (Edit Table)")
        df = pd.DataFrame(raw_data)
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Lưu thay đổi"):
            if save_data_to_github(edited.to_dict(orient="records")):
                st.success("Đã cập nhật!")
                st.session_state["data_cache"] = edited.to_dict(orient="records")
            else: st.error("Lỗi GitHub!")

    # --- 4. KHO VIDEO ---
    elif menu == "☁️ Kho Video":
        st.title("☁️ Video GitHub")
        st.info("Chức năng đang bảo trì để tối ưu tốc độ.")

if __name__ == "__main__":
    if check_login():
        main_app()
