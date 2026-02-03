import streamlit as st
import pandas as pd
import json
import time
import requests
from datetime import datetime, timedelta, date
from github import Github, GithubException

# ==========================================
# CẤU HÌNH & KẾT NỐI
# ==========================================
st.set_page_config(page_title="TikTok Farm Cloud Pro", page_icon="☁️", layout="wide")

# CSS Tùy chỉnh (Giao diện Mobile & Dark Mode)
st.markdown("""
    <style>
    .stTextInput input { background-color: #262730; color: #fff; border: 1px solid #555; }
    .status-badge { font-weight: bold; padding: 4px 8px; border-radius: 4px; }
    div[data-testid="stExpander"] { border: 1px solid #444; border-radius: 8px; margin-bottom: 10px; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# Lấy Config từ secrets
try:
    ADMIN_USER = st.secrets["auth"]["username"]
    ADMIN_PASS = st.secrets["auth"]["password"]
    GH_TOKEN = st.secrets["github"]["token"]
    GH_REPO_NAME = st.secrets["github"]["repo_name"]
    GH_BRANCH = st.secrets["github"].get("branch", "main")
except:
    st.error("⛔ LỖI CẤU HÌNH: Chưa có file secrets.toml hoặc thiếu Token GitHub.")
    st.stop()

# Định nghĩa đường dẫn file trên GitHub
DATA_FILE_PATH = 'tiktok_farm_data.json'
VIDEO_FOLDER = 'videos/'

# ==========================================
# GITHUB API HANDLER
# ==========================================
@st.cache_resource
def get_repo():
    """Kết nối tới GitHub Repo"""
    try:
        g = Github(GH_TOKEN)
        return g.get_repo(GH_REPO_NAME)
    except Exception as e:
        st.error(f"Không kết nối được GitHub: {e}")
        return None

def load_data_from_github():
    """Tải database json từ GitHub"""
    repo = get_repo()
    if not repo: return []
    
    try:
        content = repo.get_contents(DATA_FILE_PATH, ref=GH_BRANCH)
        json_str = content.decoded_content.decode("utf-8")
        data = json.loads(json_str)
        # Validate data để tránh lỗi key
        for item in data:
            if "password" not in item: item["password"] = ""
            if "date_added" not in item: item["date_added"] = datetime.now().strftime('%Y-%m-%d')
            if "status" not in item: item["status"] = "Nuôi"
        return data
    except:
        # Nếu file chưa tồn tại, trả về list rỗng
        return []

def save_data_to_github(data):
    """Lưu database json lên GitHub"""
    repo = get_repo()
    if not repo: return False
    
    # Convert date objects to string
    for item in data:
        for key, value in item.items():
            if isinstance(value, (date, datetime)):
                item[key] = value.strftime('%Y-%m-%d')
    
    json_str = json.dumps(data, indent=4, ensure_ascii=False)
    
    try:
        # Thử lấy file cũ để lấy SHA (cần SHA để update)
        contents = repo.get_contents(DATA_FILE_PATH, ref=GH_BRANCH)
        repo.update_file(contents.path, f"Auto-save {datetime.now().strftime('%H:%M %d/%m')}", json_str, contents.sha, branch=GH_BRANCH)
        return True
    except:
        try:
            # Nếu chưa có thì tạo mới
            repo.create_file(DATA_FILE_PATH, "Init data", json_str, branch=GH_BRANCH)
            return True
        except Exception as e:
            st.error(f"Lỗi lưu data: {e}")
            return False

def upload_video_to_github(file_obj):
    """Upload video vào folder videos/"""
    repo = get_repo()
    if not repo: return False
    
    file_path = f"{VIDEO_FOLDER}{file_obj.name}"
    try:
        # Check if exists to update
        contents = repo.get_contents(file_path, ref=GH_BRANCH)
        repo.update_file(file_path, f"Update video {file_obj.name}", file_obj.getvalue(), contents.sha, branch=GH_BRANCH)
    except:
        # Create new
        try:
            repo.create_file(file_path, f"Upload video {file_obj.name}", file_obj.getvalue(), branch=GH_BRANCH)
        except Exception as e:
            st.error(f"Lỗi upload: {e}")
            return False
    return True

def get_videos_from_github():
    """Lấy danh sách video"""
    repo = get_repo()
    if not repo: return []
    videos = []
    try:
        contents = repo.get_contents(VIDEO_FOLDER, ref=GH_BRANCH)
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path, ref=GH_BRANCH))
            else:
                if file_content.name.lower().endswith(('.mp4', '.mov', '.avi')):
                    videos.append(file_content)
    except:
        pass 
    return videos

def delete_github_file(file_path, sha):
    """Xóa file trên GitHub"""
    repo = get_repo()
    if repo:
        repo.delete_file(file_path, "User deleted file", sha, branch=GH_BRANCH)

# ==========================================
# LOGIC & UI
# ==========================================
def check_tiktok_status_simple(username):
    url = f"https://www.tiktok.com/@{username}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            if '"user":{"id":' in r.text or '"uniqueId":' in r.text: return "Live"
            return "Live?" # Cần check kỹ
        elif r.status_code == 404: return "Die"
        return "Unknown"
    except: return "Error"

def check_login():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            st.title("🔒 Login Farm Cloud")
            with st.form("login"):
                u = st.text_input("User"); p = st.text_input("Pass", type="password")
                if st.form_submit_button("Login"):
                    if u == ADMIN_USER and p == ADMIN_PASS:
                        st.session_state["authenticated"] = True; st.rerun()
                    else: st.error("Sai thông tin!")
        return False
    return True

def main_app():
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("☁️ Farm Menu")
        menu = st.radio("Chức năng:", ["Dashboard", "Quản lý Acc", "Kho Video Cloud", "Tool Check Live"])
        
        st.divider()
        if st.button("🔄 Reload Data"):
            st.cache_data.clear()
            if "data_cache" in st.session_state: del st.session_state["data_cache"]
            st.rerun()
        
        if st.button("🚪 Đăng xuất"):
            st.session_state["authenticated"] = False; st.rerun()

    # --- LOAD DATA (SESSION STATE) ---
    # Chỉ load từ GitHub khi chưa có trong session hoặc user bấm reload
    if "data_cache" not in st.session_state:
        with st.spinner("⏳ Đang đồng bộ dữ liệu từ GitHub..."):
            st.session_state["data_cache"] = load_data_from_github()
    
    raw_data = st.session_state["data_cache"]

    # --- TAB 1: DASHBOARD ---
    if menu == "Dashboard":
        st.title("🚀 Dashboard Tổng quan")
        
        if not raw_data:
            st.warning("Chưa có dữ liệu account. Hãy qua tab 'Quản lý Acc' để thêm.")
        else:
            df = pd.DataFrame(raw_data)
            
            # Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tổng Acc", len(df))
            c2.metric("Đang Nuôi", len(df[df['status']=='Nuôi']))
            c3.metric("Acc Live", len(df[df['status']=='Live']))
            c4.metric("Doanh thu", f"${pd.to_numeric(df.get('gmv', 0), errors='coerce').sum():,.2f}")
            
            st.divider()
            
            # Charts & Warnings
            col_g1, col_g2 = st.columns([2, 1])
            with col_g1:
                st.subheader("📊 Trạng thái Acc")
                st.bar_chart(df['status'].value_counts(), color="#FE2C55")
            
            with col_g2:
                st.subheader("⚠️ Cảnh báo Proxy")
                today = datetime.now().date()
                with st.container(height=300):
                    found_warn = False
                    for item in raw_data:
                        try:
                            p_exp = item.get('proxy_exp')
                            if p_exp:
                                d_obj = datetime.strptime(str(p_exp), '%Y-%m-%d').date()
                                days = (d_obj - today).days
                                if days < 0: 
                                    st.error(f"{item['id']}: Hết hạn {-days} ngày!")
                                    found_warn = True
                                elif days <= 3: 
                                    st.warning(f"{item['id']}: Còn {days} ngày!")
                                    found_warn = True
                        except: pass
                    if not found_warn: st.success("Proxy ổn định!")

    # --- TAB 2: QUẢN LÝ ACC ---
    elif menu == "Quản lý Acc":
        st.title("📱 Quản lý & Copy")

        # 1. Thêm mới
        with st.expander("➕ Thêm Account Mới"):
            with st.form("add_acc"):
                c1, c2 = st.columns(2)
                nid = c1.text_input("Tên máy (VD: IP7-A)")
                nuser = c2.text_input("Username")
                npass = st.text_input("Password")
                nip = st.text_input("Proxy IP:Port:User:Pass")
                
                if st.form_submit_button("Lưu lên Cloud"):
                    new_acc = {
                        "id": nid, "username": nuser, "password": npass,
                        "status": "Nuôi", "proxy_ip": nip,
                        "date_added": datetime.now().strftime('%Y-%m-%d'),
                        "proxy_exp": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                        "gmv": 0
                    }
                    raw_data.append(new_acc)
                    if save_data_to_github(raw_data):
                        st.session_state["data_cache"] = raw_data
                        st.success("Đã thêm thành công!")
                        time.sleep(1); st.rerun()

        st.divider()

        # 2. Data Editor
        st.subheader("📝 Danh sách Acc (Edit trực tiếp)")
        df = pd.DataFrame(raw_data)
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="editor")
        
        if st.button("💾 Lưu thay đổi lên GitHub", type="primary"):
            with st.spinner("Đang đẩy dữ liệu lên Cloud..."):
                updated_data = edited_df.to_dict(orient='records')
                if save_data_to_github(updated_data):
                    st.session_state["data_cache"] = updated_data
                    st.success("Đã đồng bộ xong!")
                else:
                    st.error("Lỗi khi lưu!")

        # 3. Mobile Copy View
        st.divider()
        st.subheader("📋 Copy Nhanh (Mobile)")
        search = st.text_input("🔍 Tìm kiếm:", placeholder="Nhập tên user...")
        view_data = raw_data
        if search: view_data = [d for d in raw_data if search.lower() in str(d).lower()]
        
        for acc in view_data:
            with st.expander(f"{acc.get('id','?')} | {acc.get('username','?')} ({acc.get('status','')})"):
                c1, c2 = st.columns(2)
                c1.text_input("User", acc.get('username',''), key=f"u_{acc.get('id','x')}")
                c2.text_input("Pass", acc.get('password',''), key=f"p_{acc.get('id','x')}")
                st.code(acc.get('proxy_ip',''), language="text")

    # --- TAB 3: KHO VIDEO ---
    elif menu == "Kho Video Cloud":
        st.title("🎬 Kho Video (Lưu trên GitHub)")
        st.info("⚠️ Lưu ý: GitHub giới hạn file < 100MB (Khuyên dùng < 50MB). Upload file lớn sẽ bị lỗi.")
        
        # Upload
        upl = st.file_uploader("Chọn video (MP4)", type=['mp4','mov'])
        if upl:
            if st.button(f"⬆️ Upload {upl.name} ngay"):
                with st.spinner("Đang upload... (Vui lòng chờ)"):
                    if upload_video_to_github(upl):
                        st.success("Upload thành công!")
                        time.sleep(2); st.rerun()
        
        st.divider()
        
        # List Videos
        st.subheader("Danh sách Video")
        videos = get_videos_from_github()
        
        if not videos:
            st.warning("Kho trống.")
        else:
            for vid in videos:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"🎥 **{vid.name}** ({round(vid.size/1048576, 2)} MB)")
                    col2.link_button("⬇️ Tải về", vid.download_url)
                    if col3.button("🗑️ Xóa", key=vid.sha):
                        with st.spinner("Đang xóa..."):
                            delete_github_file(vid.path, vid.sha)
                        st.rerun()
                    st.divider()

    # --- TAB 4: CHECK LIVE ---
    elif menu == "Tool Check Live":
        st.title("🕵️ Kiểm tra trạng thái Acc")
        st.write("Tool sẽ gửi request cơ bản vào profile TikTok để check.")
        
        if st.button("▶️ Bắt đầu quét"):
            prog = st.progress(0)
            log_area = st.empty()
            count_die = 0
            
            for i, acc in enumerate(raw_data):
                u = acc.get('username')
                log_area.text(f"Checking: {u}...")
                
                status = check_tiktok_status_simple(u)
                if status == "Die":
                    acc['status'] = "Die"
                    count_die += 1
                
                prog.progress((i+1)/len(raw_data))
                time.sleep(0.8) # Delay tránh spam
            
            log_area.text("Hoàn thành!")
            if count_die > 0:
                save_data_to_github(raw_data)
                st.success(f"Phát hiện {count_die} acc Die. Đã cập nhật database!")
            else:
                st.info("Không phát hiện acc Die mới.")

if __name__ == "__main__":
    if check_login():
        main_app()
