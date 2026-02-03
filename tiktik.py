import streamlit as st
import pandas as pd
import json
import os
import requests
import time
from datetime import datetime, timedelta, date

# ==========================================
# CẤU HÌNH & AUTH (Đã nâng cấp bảo mật)
# ==========================================
# Cố gắng lấy pass từ secrets.toml, nếu không có thì dùng mặc định
try:
    ADMIN_USER = st.secrets["auth"]["username"]
    ADMIN_PASS = st.secrets["auth"]["password"]
except:
    # Mặc định để bạn test ngay (Nên tạo file secrets.toml sau này)
    ADMIN_USER = "admin"
    ADMIN_PASS = "mmo888"

DATA_FILE = 'tiktok_farm_v2.json'

st.set_page_config(page_title="TikTok Farm Pro Max", page_icon="🚀", layout="wide")

# CSS Tùy chỉnh (Tối ưu Mobile & Giao diện tối)
st.markdown("""
    <style>
    /* Mobile Input Style */
    .stTextInput input {
        background-color: #262730;
        color: #fff;
        border: 1px solid #444;
    }
    .status-badge {
        font-weight: bold;
        padding: 5px 10px;
        border-radius: 5px;
    }
    .farm-days {
        color: #FFD700; 
        font-weight: bold;
        font-size: 14px;
    }
    .content-tag {
        color: #00BFFF;
        font-weight: bold;
        font-size: 14px;
    }
    /* Ẩn nút check status mặc định của check video */
    div[data-testid="stExpander"] {
        border: 1px solid #444;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# HELPER: ICON & TOOL CHECKER
# ==========================================
def get_status_config(status):
    if status == "Live": return "🟢", 0 
    if status == "Nuôi": return "🟡", 1
    if status == "Shadowban": return "❌", 2
    if status == "Die": return "💀", 3
    return "⚪", 4

def check_tiktok_status_simple(username):
    """
    Check cơ bản trạng thái User.
    LƯU Ý: TikTok chặn request server rất gắt. Đây chỉ là check cơ bản (HTTP Code).
    Để chính xác 100% cần dùng Residential Proxy.
    """
    url = f"https://www.tiktok.com/@{username}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        # TikTok thường trả về 200 cho profile sống
        if r.status_code == 200:
            # Check thêm keyword trong HTML để chắc chắn không bị redirect login
            if '"user":{"id":' in r.text or '"uniqueId":' in r.text:
                return "Live"
            return "Live (Cần check lại)" # Có thể bị redirect
        elif r.status_code == 404:
            return "Die"
        else:
            return "Unknown" # Có thể bị chặn IP
    except:
        return "Error"

# ==========================================
# BACKEND: XỬ LÝ DỮ LIỆU
# ==========================================
def load_data():
    default_data = [
        {
            "id": "iPhone 7-A",
            "status": "Live",
            "username": "user_demo_01",
            "password": "pass_demo_123",
            "niche": "Health",
            "content_type": "Reup Video",
            "country": "US",
            "proxy_ip": "192.168.1.10:8000",
            "proxy_pass": "proxypass1",
            "proxy_exp": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "date_added": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
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
            # Validate field thiếu
            for item in data:
                if "password" not in item: item["password"] = ""
                if "proxy_pass" not in item: item["proxy_pass"] = ""
                if "date_added" not in item: item["date_added"] = datetime.now().strftime('%Y-%m-%d')
            return data
    except:
        return default_data

def save_data(data):
    # Convert date objects to string before saving
    for item in data:
        for key, value in item.items():
            if isinstance(value, (date, datetime)):
                item[key] = value.strftime('%Y-%m-%d')

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
        menu = st.radio("Chức năng:", ["Dashboard", "Quản lý & Copy", "Tool Check Live", "Thêm Account"])
        st.divider()
        if st.button("Đăng xuất"):
            st.session_state["authenticated"] = False
            st.rerun()

    raw_data = load_data()
    
    # --- TAB 1: DASHBOARD (NÂNG CẤP) ---
    if menu == "Dashboard":
        st.title("🚀 Tổng quan Farm")
        
        # Nút tải Backup
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 Tải Backup Data (.json)",
                data=f,
                file_name=f"backup_tiktok_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

        if not raw_data:
            st.warning("Chưa có dữ liệu.")
            return

        df = pd.DataFrame(raw_data)
        
        # Metric
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng Acc", len(df))
        c2.metric("Đang nuôi", len(df[df['status'] == 'Nuôi']))
        c3.metric("Live (Sẵn sàng)", len(df[df['status'] == 'Live']))
        total_gmv = pd.to_numeric(df.get('gmv', 0), errors='coerce').sum()
        c4.metric("Tổng Doanh thu", f"${total_gmv:,.2f}")

        st.divider()

        # Chart & Warning Layout
        col_chart1, col_chart2 = st.columns([2, 1])
        
        with col_chart1:
            st.subheader("📊 Tỉ lệ Trạng thái")
            if not df.empty:
                status_counts = df['status'].value_counts()
                st.bar_chart(status_counts, color="#FE2C55") # Màu đỏ TikTok
        
        with col_chart2:
            st.subheader("⚠️ Cảnh báo Proxy")
            today = datetime.now().date()
            has_warning = False
            
            with st.container(height=300):
                for item in raw_data:
                    try:
                        p_date = datetime.strptime(str(item.get('proxy_exp')), '%Y-%m-%d').date()
                        days = (p_date - today).days
                        if days < 0:
                            st.error(f"🔴 {item['id']}: Hết hạn {abs(days)} ngày!")
                            has_warning = True
                        elif days <= 3:
                            st.warning(f"🟡 {item['id']}: Còn {days} ngày!")
                            has_warning = True
                    except: pass
                
                if not has_warning:
                    st.success("✅ Tất cả Proxy ổn định!")

    # --- TAB 2: QUẢN LÝ & COPY (MOBILE OPTIMIZED) ---
    elif menu == "Quản lý & Copy":
        st.title("📱 Quản lý Account")
        
        # Sort Logic
        for item in raw_data:
            icon, priority = get_status_config(item.get('status', 'Nuôi'))
            item['_sort_priority'] = priority
        sorted_data = sorted(raw_data, key=lambda x: (x['_sort_priority'], x['id']))
        df = pd.DataFrame(sorted_data).drop(columns=['_sort_priority'])
        
        # --- 1. EDITOR TABLE ---
        st.subheader("1. Cập nhật thông tin")
        today = datetime.now().date()
        
        if "days_farmed" not in df.columns:
            df["days_farmed"] = df["date_added"].apply(
                lambda x: (today - pd.to_datetime(x).date()).days if x else 0
            )

        edited_df = st.data_editor(
            df,
            column_config={
                "status": st.column_config.SelectboxColumn("Trạng thái", options=["Live", "Shadowban", "Die", "Nuôi"], width="small"),
                "days_farmed": st.column_config.NumberColumn("Đã nuôi (Ngày)"),
                "gmv": st.column_config.NumberColumn("GMV ($)", format="$%.2f"),
                "date_added": None, 
                "id": "Tên máy",
                "username": "User"
            },
            hide_index=True,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_main"
        )

        if st.button("💾 Lưu thay đổi", type="primary"):
            try:
                save_list = edited_df.to_dict(orient='records')
                for item in save_list:
                    # Logic chỉnh ngày nuôi ngược lại thành ngày bắt đầu
                    if 'days_farmed' in item:
                        new_days = int(item['days_farmed'])
                        new_start_date = today - timedelta(days=new_days)
                        item['date_added'] = new_start_date.strftime('%Y-%m-%d')
                        del item['days_farmed']
                        
                    if '_sort_priority' in item: del item['_sort_priority']
                        
                save_data(save_list)
                st.success("Đã lưu dữ liệu!")
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi: {e}")

        st.divider()

        # --- 2. MOBILE COPY CARD ---
        st.subheader("📋 Copy Nhanh (Giao diện Mobile)")
        
        search = st.text_input("🔍 Tìm nhanh (User/Máy):", placeholder="gõ tên...")
        display_data = sorted_data
        if search:
            display_data = [d for d in display_data if search.lower() in d['id'].lower() or search.lower() in d['username'].lower()]

        for acc in display_data:
            icon, _ = get_status_config(acc.get('status', 'Nuôi'))
            
            # Tính ngày nuôi
            days_diff = 0
            try:
                start_date = datetime.strptime(str(acc.get('date_added')), '%Y-%m-%d').date()
                days_diff = (today - start_date).days
            except: pass

            with st.expander(f"{icon} {acc['id']} | {acc['username']}", expanded=False):
                # Hiển thị Tag
                st.markdown(f"<span class='content-tag'>🎬 {acc.get('content_type','None')}</span> • <span class='farm-days'>⏳ {days_diff} ngày</span>", unsafe_allow_html=True)
                
                # Input để copy dễ dàng trên mobile (dùng text_input thay vì code)
                c1, c2 = st.columns(2)
                with c1:
                    st.text_input("User", value=acc['username'], key=f"u_{acc['id']}")
                with c2:
                    st.text_input("Pass", value=acc.get('password', ''), type="password", key=f"p_{acc['id']}")
                
                # Proxy section
                st.caption("Proxy Info (IP:Port:User:Pass)")
                proxy_str = f"{acc.get('proxy_ip','')}:{acc.get('proxy_pass','')}"
                st.code(proxy_str, language="text")
                
                # Nút hành động nhanh
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("🗑️ Xóa", key=f"del_{acc['id']}"):
                        new_list = [x for x in raw_data if x['id'] != acc['id']]
                        save_data(new_list)
                        st.rerun()

    # --- TAB 3: TOOL CHECK LIVE (NEW) ---
    elif menu == "Tool Check Live":
        st.title("🕵️ Tool Check Live/Die")
        st.warning("⚠️ Lưu ý: Tool dùng request cơ bản. Không nên spam liên tục tránh bị TikTok chặn IP máy chủ.")
        
        if st.button("Bắt đầu quét tất cả Account"):
            progress_bar = st.progress(0)
            status_log = st.empty()
            
            updated_count = 0
            
            for i, acc in enumerate(raw_data):
                status_log.write(f"Đang check: **{acc['username']}**...")
                
                # Check status
                new_status = check_tiktok_status_simple(acc['username'])
                
                # Cập nhật nếu phát hiện Die
                if new_status == "Die" and acc['status'] != "Die":
                    acc['status'] = "Die"
                    updated_count += 1
                
                # Update progress
                progress_bar.progress((i + 1) / len(raw_data))
                time.sleep(1) # Delay nhẹ để tránh block
            
            # Lưu lại
            if updated_count > 0:
                save_data(raw_data)
                st.success(f"Hoàn thành! Đã cập nhật {updated_count} account sang trạng thái DIE.")
            else:
                st.info("Hoàn thành! Các account vẫn ổn định (hoặc không thể xác định).")
                
            status_log.empty()

    # --- TAB 4: THÊM ACCOUNT ---
    elif menu == "Thêm Account":
        st.title("➕ Thêm Account Mới")
        
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            new_id = c1.text_input("Tên máy (VD: iPhone 7-A)")
            new_country = c2.selectbox("Quốc gia", ["US", "UK", "FR", "VN"])
            
            st.markdown("---")
            t1, t2 = st.columns(2)
            new_user = t1.text_input("Username")
            new_pass = t2.text_input("Password TikTok")
            
            st.markdown("---")
            n1, n2 = st.columns([1, 1])
            with n1:
                niche_opt = st.selectbox("Chọn Chủ đề", ["Sức khỏe", "Gia dụng", "Thời trang", "Nhập thủ công..."])
            final_niche = niche_opt
            if niche_opt == "Nhập thủ công...":
                with n2:
                    final_niche = st.text_input("👉 Nhập tên chủ đề:")

            st.markdown("---")
            new_content_type = st.text_input("🎬 Loại Content", placeholder="VD: Reup Phim...")

            st.markdown("---")
            p1, p2 = st.columns(2)
            new_ip = p1.text_input("IP:Port")
            new_prox_pass = p2.text_input("Proxy User:Pass")
            
            proxy_duration_opt = st.radio("Thời hạn Proxy:", ["Nhập ngày", "30 ngày"], horizontal=True)
            final_exp_date = datetime.now().date() + timedelta(days=30)
            if proxy_duration_opt == "Nhập ngày":
                final_exp_date = st.date_input("Chọn ngày hết hạn")

            st.markdown("---")
            init_days = st.number_input("⏳ Đã nuôi trước đó (ngày)?", min_value=0, value=0)

            if st.form_submit_button("Thêm ngay", type="primary"):
                if new_id and new_user:
                    start_date_val = datetime.now().date() - timedelta(days=init_days)
                    new_obj = {
                        "id": new_id,
                        "status": "Nuôi",
                        "username": new_user,
                        "password": new_pass,
                        "niche": final_niche if final_niche else "Unset",
                        "content_type": new_content_type,
                        "country": new_country,
                        "proxy_ip": new_ip,
                        "proxy_pass": new_prox_pass,
                        "proxy_exp": final_exp_date.strftime('%Y-%m-%d'),
                        "date_added": start_date_val.strftime('%Y-%m-%d'),
                        "views": 0,
                        "gmv": 0.0,
                    }
                    data = load_data()
                    data.append(new_obj)
                    save_data(data)
                    st.success(f"Đã thêm {new_id} thành công!")
                else:
                    st.error("Thiếu Tên máy hoặc Username!")

if __name__ == "__main__":
    if check_login():
        main_app()
