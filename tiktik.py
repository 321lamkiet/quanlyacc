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

# CSS Tùy chỉnh
st.markdown("""
    <style>
    button[title="Copy to clipboard"] {
        font-size: 1.2rem !important; 
        padding: 10px !important;
    }
    .stCode {
        font-size: 16px !important;
    }
    .status-badge {
        font-weight: bold;
        padding: 5px 10px;
        border-radius: 5px;
    }
    .farm-days {
        color: #FFD700; 
        font-weight: bold;
        font-size: 15px;
    }
    .content-tag {
        color: #00BFFF;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# HELPER: ICON TRẠNG THÁI
# ==========================================
def get_status_config(status):
    if status == "Live": return "🟢", 0 
    if status == "Nuôi": return "🟡", 1
    if status == "Shadowban": return "❌", 2
    if status == "Die": return "💀", 3
    return "⚪", 4

# ==========================================
# BACKEND: XỬ LÝ DỮ LIỆU
# ==========================================
def load_data():
    default_data = [
        {
            "id": "iPhone 7-A",
            "status": "Live",
            "username": "user_us_01",
            "password": "pass_tiktok_123",
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
            today_str = datetime.now().strftime('%Y-%m-%d')
            for item in data:
                if "password" not in item: item["password"] = ""
                if "proxy_pass" not in item: item["proxy_pass"] = ""
                if "date_added" not in item: item["date_added"] = today_str
                if "content_type" not in item: item["content_type"] = ""
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
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng Acc", len(df))
        
        farm_accs = df[df['status'] == 'Nuôi']
        avg_days = 0
        if not farm_accs.empty and 'date_added' in farm_accs.columns:
            today = datetime.now().date()
            dates = pd.to_datetime(farm_accs['date_added'], errors='coerce').dt.date
            total_days = sum([(today - d).days for d in dates if pd.notnull(d)])
            avg_days = int(total_days / len(farm_accs)) if len(farm_accs) > 0 else 0

        c2.metric("Đang nuôi", len(farm_accs), delta=f"TB: {avg_days} ngày")
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

    # --- TAB 2: QUẢN LÝ & COPY ---
    elif menu == "Quản lý & Copy":
        st.title("📱 Quản lý Account")
        
        if not raw_data:
            st.info("Chưa có account nào.")
        else:
            # Sort Logic
            for item in raw_data:
                icon, priority = get_status_config(item.get('status', 'Nuôi'))
                item['_sort_priority'] = priority
            sorted_data = sorted(raw_data, key=lambda x: (x['_sort_priority'], x['id']))
            df = pd.DataFrame(sorted_data).drop(columns=['_sort_priority'])
            
            # --- TÍNH NĂNG MỚI: TẠO CỘT SỐ NGÀY ĐỂ EDIT ---
            st.subheader("1. Cập nhật thông tin")
            
            today = datetime.now().date()
            
            # 1. Chuyển đổi dữ liệu ngày tháng
            if "proxy_exp" in df.columns:
                df["proxy_exp"] = pd.to_datetime(df["proxy_exp"], errors='coerce').dt.date
            
            # 2. Tạo cột 'days_farmed' từ 'date_added' để hiển thị
            if "date_added" in df.columns:
                # Hàm tính số ngày: Hôm nay - Ngày tạo
                df["days_farmed"] = df["date_added"].apply(
                    lambda x: (today - pd.to_datetime(x).date()).days if x else 0
                )

            edited_df = st.data_editor(
                df,
                column_config={
                    "status": st.column_config.SelectboxColumn("Trạng thái", options=["Live", "Shadowban", "Die", "Nuôi"], width="small"),
                    "days_farmed": st.column_config.NumberColumn(
                        "Đã nuôi (Ngày)", 
                        help="Nhập số ngày để chỉnh tuổi thọ Acc",
                        min_value=0,
                        step=1,
                        required=True
                    ),
                    "content_type": st.column_config.TextColumn("Loại Content", width="medium"),
                    "niche": st.column_config.TextColumn("Chủ đề"),
                    "password": st.column_config.TextColumn("Pass TikTok"),
                    "proxy_pass": st.column_config.TextColumn("Pass Proxy"),
                    "gmv": st.column_config.NumberColumn("GMV ($)", format="$%.2f"),
                    # Ẩn cột ngày gốc đi cho đỡ rối, chỉ hiện cột số ngày
                    "date_added": None, 
                    "id": "Tên máy",
                    "username": "User"
                },
                hide_index=True,
                num_rows="dynamic",
                use_container_width=True
            )

            if st.button("💾 Lưu thay đổi", type="primary"):
                try:
                    save_list = edited_df.to_dict(orient='records')
                    
                    # --- LOGIC QUAN TRỌNG: TÍNH LẠI NGÀY TỪ SỐ NGÀY NHẬP VÀO ---
                    for item in save_list:
                        # 1. Tính lại date_added dựa trên days_farmed
                        if 'days_farmed' in item:
                            new_days = int(item['days_farmed'])
                            # Ngày bắt đầu = Hôm nay - Số ngày đã nuôi
                            new_start_date = today - timedelta(days=new_days)
                            item['date_added'] = new_start_date.strftime('%Y-%m-%d')
                            # Xóa cột tạm days_farmed trước khi lưu
                            del item['days_farmed']

                        # 2. Format cột Proxy Exp
                        if isinstance(item.get('proxy_exp'), (date, datetime)):
                            item['proxy_exp'] = item['proxy_exp'].strftime('%Y-%m-%d')
                        elif not item.get('proxy_exp'):
                            item['proxy_exp'] = (today + timedelta(days=1)).strftime('%Y-%m-%d')
                        
                        # 3. Dọn dẹp cột sort
                        if '_sort_priority' in item: del item['_sort_priority']
                            
                    save_data(save_list)
                    st.success("Đã lưu dữ liệu & Cập nhật ngày nuôi!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")

            st.divider()

            # --- 2. MOBILE COPY CARD ---
            st.subheader("📋 Copy Nhanh (Mobile)")
            
            col_search, col_filter = st.columns([1, 1])
            search = col_search.text_input("🔍 Tìm kiếm:", placeholder="Tên máy, User...")
            filter_status = col_filter.multiselect("Lọc trạng thái:", ["Live", "Nuôi", "Shadowban", "Die"])
            
            display_data = sorted_data
            if search:
                display_data = [d for d in display_data if search.lower() in d['id'].lower() or search.lower() in d['username'].lower()]
            if filter_status:
                display_data = [d for d in display_data if d['status'] in filter_status]

            for acc in display_data:
                icon, _ = get_status_config(acc.get('status', 'Nuôi'))
                
                # Tính lại ngày để hiển thị
                days_diff = 0
                try:
                    start_date = datetime.strptime(str(acc.get('date_added')), '%Y-%m-%d').date()
                    days_diff = (today - start_date).days
                except: pass

                # Header thẻ Card
                with st.expander(f"{icon} {acc['id']} | {acc['username']}", expanded=True):
                    
                    info_html = ""
                    if acc.get('content_type'):
                        info_html += f"<span class='content-tag'>🎬 {acc['content_type']}</span> "
                    
                    # Luôn hiển thị số ngày nuôi
                    info_html += f" | <span class='farm-days'>⏳ Đã nuôi: {days_diff} ngày</span>"
                    
                    if info_html:
                        st.markdown(info_html, unsafe_allow_html=True)
                        st.divider() 

                    c1, c2 = st.columns(2)
                    with c1:
                        st.caption("User TikTok")
                        st.code(acc['username'], language=None)
                    with c2:
                        st.caption("Pass TikTok")
                        st.code(acc.get('password', ''), language=None)
                    
                    c3, c4 = st.columns(2)
                    with c3:
                        st.caption("Proxy IP")
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
                    custom_niche = st.text_input("👉 Nhập tên chủ đề:")
                    final_niche = custom_niche if custom_niche else "Chưa đặt tên"

            st.markdown("---")
            new_content_type = st.text_input("🎬 Loại Content (VD: Reup Phim...)", placeholder="Nhập loại content...")

            st.markdown("---")
            st.write("Cấu hình Proxy:")
            p1, p2 = st.columns(2)
            new_ip = p1.text_input("IP:Port")
            new_prox_pass = p2.text_input("Proxy Password")
            
            st.write("Thời hạn Proxy:")
            proxy_duration_opt = st.radio(
                "Chọn thời gian:", ["Nhập ngày cụ thể", "30 ngày", "60 ngày", "90 ngày"], 
                horizontal=True, label_visibility="collapsed"
            )
            final_exp_date = None
            if proxy_duration_opt == "Nhập ngày cụ thể":
                final_exp_date = st.date_input("Chọn ngày hết hạn")
            else:
                days_to_add = int(proxy_duration_opt.split()[0])
                final_exp_date = datetime.now().date() + timedelta(days=days_to_add)
                st.info(f"📅 Proxy đến ngày: **{final_exp_date.strftime('%Y-%m-%d')}**")

            # --- TÍNH NĂNG MỚI: NHẬP SỐ NGÀY ĐÃ NUÔI TRƯỚC ĐÓ ---
            st.markdown("---")
            init_days = st.number_input("⏳ Account này đã nuôi trước đó bao nhiêu ngày?", min_value=0, value=0, help="Nếu là acc mới thì để 0")

            if st.form_submit_button("Thêm ngay"):
                if new_id and new_user:
                    # Tính ngày bắt đầu lùi về quá khứ
                    start_date_val = datetime.now().date() - timedelta(days=init_days)
                    
                    new_obj = {
                        "id": new_id,
                        "status": "Nuôi",
                        "username": new_user,
                        "password": new_pass,
                        "niche": final_niche,
                        "content_type": new_content_type,
                        "country": new_country,
                        "proxy_ip": new_ip,
                        "proxy_pass": new_prox_pass,
                        "proxy_exp": final_exp_date.strftime('%Y-%m-%d'),
                        "date_added": start_date_val.strftime('%Y-%m-%d'), # Lưu ngày đã lùi
                        "views": 0,
                        "gmv": 0.0,
                    }
                    data = load_data()
                    data.append(new_obj)
                    save_data(data)
                    st.success(f"Đã thêm {new_id} (Đã nuôi {init_days} ngày)")
                else:
                    st.error("Thiếu Tên máy hoặc Username!")

if __name__ == "__main__":
    if check_login():
        main_app()
